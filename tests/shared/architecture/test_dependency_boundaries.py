"""Structural contracts for navigable wrapper-generation boundaries."""

from __future__ import annotations

import ast

from tests.fortran._support.wrapper_build import REPO_ROOT

WRAPPER_CODEGEN_ROOT = REPO_ROOT / "x2py" / "wrapper_codegen"
BOUNDARY_MODULES = (
    ("c", WRAPPER_CODEGEN_ROOT / "c" / "binding.py"),
    ("fortran", WRAPPER_CODEGEN_ROOT / "fortran" / "bridge.py"),
    ("printers", WRAPPER_CODEGEN_ROOT / "printers" / "pyi_printer.py"),
    ("printers", WRAPPER_CODEGEN_ROOT / "printers" / "source_printers.py"),
)
PUBLIC_MODULE_FUNCTIONS = {
    ("printers", "pyi_printer.py", "emit_module"),
    ("printers", "pyi_printer.py", "emit_module_stubs"),
    ("printers", "pyi_printer.py", "opaque_dependency_modules"),
}


def test_wrapper_codegen_boundary_entrypoints_and_visitors_are_documented():
    """Require public entrypoints and dispatched model visitors to state their contract."""
    missing = []
    for _, path in BOUNDARY_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and ast.get_docstring(node) is None:
                missing.append(f"{path.name}:{node.lineno}:{node.name}")
            if isinstance(node, ast.ClassDef):
                missing.extend(
                    f"{path.name}:{method.lineno}:{node.name}.{method.name}"
                    for method in node.body
                    if isinstance(method, ast.FunctionDef)
                    and (not method.name.startswith("_") or method.name.startswith("_visit_"))
                    and ast.get_docstring(method) is None
                )
    assert not missing, "Undocumented wrapper-codegen callables:\n" + "\n".join(missing)


def test_wrapper_codegen_uses_one_model_visitor_protocol():
    """Prevent alternate printer and extractor dispatch protocols from appearing."""
    invalid = []
    lowercase_model_names = {"int", "str", "tuple"}
    for _, path in BOUNDARY_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith(("_print_", "_extract_")):
                invalid.append(f"{path.name}:{node.lineno}:{node.name}")
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_visit_"):
                model_name = node.name.removeprefix("_visit_")
                if model_name[:1].islower() and model_name not in lowercase_model_names | {"not_supported"}:
                    invalid.append(f"{path.name}:{node.lineno}:{node.name}")
    assert not invalid, "Use _visit_* handlers or named helpers:\n" + "\n".join(invalid)


def test_module_functions_are_deliberate_boundary_apis():
    """Keep stateful generation logic on its owning class."""
    unexpected = []
    for area, path in BOUNDARY_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
            key = (area, path.name, node.name)
            if key not in PUBLIC_MODULE_FUNCTIONS:
                unexpected.append(f"{path.name}:{node.lineno}:{node.name}")
    assert not unexpected, "Unexpected module-level wrapper-codegen functions:\n" + "\n".join(unexpected)
