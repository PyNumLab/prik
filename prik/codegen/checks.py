"""Static contracts for wrapper lowering, printing, and orchestration."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from radon.complexity import cc_visit

__all__ = (
    "WrapperCodegenCheckConfig",
    "WrapperCodegenViolation",
    "check_codegen_package",
    "check_codegen_paths",
)


INFRASTRUCTURE_MODULES = frozenset({"__init__.py", "checks.py", "visitor.py"})
SEMANTIC_PRINTER_MODULE = "pyi.py"
SEMANTIC_PRINTER_FUNCTIONS = frozenset({"emit_module"})
VISITOR_CLASS_SUFFIXES = ("Analyzer", "Emitter", "Generator", "Planner", "Validator")
REGISTRY_SUFFIXES = ("_DISPATCHER", "_HANDLERS", "_REGISTRY")
HANDLER_PREFIXES = ("_convert_", "_emit_", "_handle_", "_visit_")
CONTROL_NODES = (ast.For, ast.AsyncFor, ast.If, ast.Match, ast.Try, ast.While, ast.With, ast.AsyncWith)
STRICT_CLASS_NAMES = frozenset(
    {
        "PrimitiveScalarTypeRegistry",
        "CBindingGenerator",
        "FortranBridgeGenerator",
        "WrapperPlanner",
    }
)
ASSEMBLER_CLASS_NAMES = frozenset(
    {
        "CBindingGenerator",
        "FortranBridgeGenerator",
        "WrapperGenerator",
    }
)


@dataclass(frozen=True)
class WrapperCodegenCheckConfig:
    """Limits enforced for new wrapper-codegen implementation code."""

    max_complexity: int = 10
    max_statements: int = 30
    max_nesting: int = 4
    strict_max_complexity: int = 5
    strict_max_statements: int = 25
    strict_max_nesting: int = 2
    assembler_max_complexity: int = 10
    assembler_max_statements: int = 50


@dataclass(frozen=True)
class WrapperCodegenViolation:
    """One static-contract violation in ``prik.codegen``."""

    path: Path
    lineno: int
    code: str
    message: str

    @property
    def label(self) -> str:
        return f"{self.path}:{self.lineno}: {self.code}: {self.message}"


DEFAULT_CHECK_CONFIG = WrapperCodegenCheckConfig()


def check_codegen_package(
    package_root: Path | None = None,
    *,
    config: WrapperCodegenCheckConfig | None = None,
) -> tuple[WrapperCodegenViolation, ...]:
    """Check the wrapper generation, printer, and orchestration modules."""
    if package_root is not None:
        paths = sorted(package_root.rglob("*.py"))
    else:
        source_root = Path(__file__).resolve().parents[1]
        paths = [
            *sorted((source_root / "codegen").rglob("*.py")),
            *sorted((source_root / "printers").glob("*.py")),
            source_root / "pipeline" / "wrapper.py",
        ]
    return check_codegen_paths(paths, config=config)


def check_codegen_paths(
    paths: list[Path],
    *,
    config: WrapperCodegenCheckConfig | None = None,
) -> tuple[WrapperCodegenViolation, ...]:
    """Check selected wrapper-codegen modules."""
    violations = []
    resolved_config = config or DEFAULT_CHECK_CONFIG
    tiered_limits = config is None
    for path in paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        violations.extend(_module_violations(path, tree))
        if path.name != SEMANTIC_PRINTER_MODULE:
            violations.extend(_function_size_violations(path, tree, source, resolved_config, tiered_limits))
        violations.extend(_registry_violations(path, tree))
    return tuple(violations)


def _module_violations(path: Path, tree: ast.Module) -> list[WrapperCodegenViolation]:
    if path.name in INFRASTRUCTURE_MODULES:
        return []
    return [
        *_module_function_violations(path, tree),
        *_visitor_class_violations(path, tree),
    ]


def _module_function_violations(path: Path, tree: ast.Module) -> list[WrapperCodegenViolation]:
    return [
        _violation(path, node, "module-function", f"move production function {node.name!r} onto a class")
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and not (path.name == SEMANTIC_PRINTER_MODULE and node.name in SEMANTIC_PRINTER_FUNCTIONS)
    ]


def _visitor_class_violations(path: Path, tree: ast.Module) -> list[WrapperCodegenViolation]:
    return [
        _violation(path, node, "visitor-class", f"{node.name} must inherit ClassVisitor")
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name.endswith(VISITOR_CLASS_SUFFIXES)
        and node.name != "WrapperGenerator"
        and not _inherits_class_visitor(node)
    ]


def _function_size_violations(
    path: Path,
    tree: ast.Module,
    source: str,
    config: WrapperCodegenCheckConfig,
    tiered_limits: bool,
) -> list[WrapperCodegenViolation]:
    complexity_by_line = {block.lineno: block.complexity for block in cc_visit(source)}
    violations = []
    for owner, node in _owned_functions(tree):
        max_complexity, max_statements, max_nesting = _function_limits(owner, config, tiered_limits)
        complexity = complexity_by_line.get(node.lineno, 1)
        statement_count = _statement_count(node)
        nesting_depth = _nesting_depth(node)
        if complexity > max_complexity:
            violations.append(_violation(path, node, "complexity", f"{node.name} has complexity {complexity}"))
        if statement_count > max_statements:
            violations.append(
                _violation(path, node, "statement-count", f"{node.name} has {statement_count} statements")
            )
        if nesting_depth > max_nesting:
            violations.append(_violation(path, node, "nesting-depth", f"{node.name} has nesting depth {nesting_depth}"))
    return violations


def _function_limits(
    owner: str | None,
    config: WrapperCodegenCheckConfig,
    tiered_limits: bool,
) -> tuple[int, int, int]:
    """Return the declared checker limits for one owning production class."""
    if not tiered_limits:
        return config.max_complexity, config.max_statements, config.max_nesting
    if owner in ASSEMBLER_CLASS_NAMES or (owner is not None and owner.endswith("Assembler")):
        return config.assembler_max_complexity, config.assembler_max_statements, config.max_nesting
    if owner in STRICT_CLASS_NAMES or (owner is not None and owner.endswith(("Emitter", "Generator", "Planner"))):
        return config.strict_max_complexity, config.strict_max_statements, config.strict_max_nesting
    return config.max_complexity, config.max_statements, config.max_nesting


def _registry_violations(path: Path, tree: ast.Module) -> list[WrapperCodegenViolation]:
    violations = []
    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        method_names = {node.name for node in class_node.body if isinstance(node, ast.FunctionDef)}
        registry_methods = _registry_methods(class_node)
        violations.extend(_missing_registry_methods(path, class_node, method_names, registry_methods))
        violations.extend(_forbidden_printer_calls(path, class_node, registry_methods))
    return violations


def _missing_registry_methods(
    path: Path,
    class_node: ast.ClassDef,
    method_names: set[str],
    registry_methods: dict[str, ast.AST],
) -> list[WrapperCodegenViolation]:
    return [
        _violation(path, owner, "registry-missing-handler", f"{class_node.name}.{method_name} is not defined")
        for method_name, owner in registry_methods.items()
        if method_name not in method_names
    ]


def _forbidden_printer_calls(
    path: Path,
    class_node: ast.ClassDef,
    registry_methods: dict[str, ast.AST],
) -> list[WrapperCodegenViolation]:
    handler_names = set(registry_methods) | {
        node.name
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith(HANDLER_PREFIXES)
    }
    return [
        _violation(path, call, "handler-printer-call", f"{class_node.name}.{method.name} calls a printer directly")
        for method in class_node.body
        if isinstance(method, ast.FunctionDef) and method.name in handler_names
        for call in ast.walk(method)
        if _is_forbidden_printer_call(call)
    ]


def _owned_functions(tree: ast.Module) -> list[tuple[str | None, ast.FunctionDef]]:
    """Return module functions and direct methods with their owning class name."""
    functions = [(None, node) for node in tree.body if isinstance(node, ast.FunctionDef)]
    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        functions.extend((class_node.name, node) for node in class_node.body if isinstance(node, ast.FunctionDef))
    return functions


def _statement_count(node: ast.FunctionDef) -> int:
    return sum(isinstance(child, ast.stmt) for child in ast.walk(node)) - 1


def _nesting_depth(node: ast.FunctionDef) -> int:
    return max((_node_nesting_depth(statement, 0) for statement in node.body), default=0)


def _node_nesting_depth(node: ast.AST, depth: int) -> int:
    next_depth = depth + 1 if isinstance(node, CONTROL_NODES) else depth
    child_depths = [_node_nesting_depth(child, next_depth) for child in ast.iter_child_nodes(node)]
    return max([next_depth, *child_depths])


def _registry_methods(class_node: ast.ClassDef) -> dict[str, ast.AST]:
    methods = {}
    for assignment in (node for node in class_node.body if isinstance(node, ast.Assign)):
        if _is_registry_assignment(assignment):
            _collect_registry_methods(assignment.value, assignment, methods)
    return methods


def _is_registry_assignment(node: ast.Assign) -> bool:
    return any(isinstance(target, ast.Name) and target.id.endswith(REGISTRY_SUFFIXES) for target in node.targets)


def _collect_registry_methods(node: ast.AST, owner: ast.AST, methods: dict[str, ast.AST]) -> None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        methods.setdefault(node.value, owner)
    if isinstance(node, ast.Dict):
        for value in node.values:
            _collect_registry_methods(value, owner, methods)


def _is_forbidden_printer_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"doprint", "write"}
    )


def _inherits_class_visitor(node: ast.ClassDef) -> bool:
    return any(_base_name(base) == "ClassVisitor" for base in node.bases)


def _base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _violation(path: Path, node: ast.AST, code: str, message: str) -> WrapperCodegenViolation:
    return WrapperCodegenViolation(path, getattr(node, "lineno", 1), code, message)
