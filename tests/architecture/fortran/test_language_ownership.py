"""Positive ownership and navigation contracts for the Fortran test tree."""

from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).parents[3]
TEST_ROOT = REPO_ROOT / "tests"
FORTRAN_ROOT = TEST_ROOT / "fortran"
FEATURE_ROOT = FORTRAN_ROOT
FORTRAN_INDEX = FORTRAN_ROOT / "README.md"
ROADMAP = REPO_ROOT / "docs/maintainer/roadmap/fortran-test-suite-cleanup-checklist.md"
BLAS_EXAMPLE_ROOT = REPO_ROOT / "examples" / "blas"
LAPACK_EXAMPLE_ROOT = REPO_ROOT / "examples" / "lapack"

FEATURE_DOCS = {
    "data_types": "docs/user/guide/data-types.md",
    "arrays": "docs/user/guide/arrays.md",
    "strings": "docs/user/guide/strings.md",
    "functions": "docs/user/guide/wrapping-functions.md",
    "subroutines": "docs/user/guide/wrapping-subroutines.md",
    "modules": "docs/user/guide/wrapping-modules.md",
    "optional_arguments": "docs/user/guide/optional-arguments.md",
    "generic_interfaces": "docs/user/guide/generic-interfaces.md",
    "derived_types": "docs/user/guide/wrapping-derived-types.md",
    "allocatables": "docs/user/guide/allocatables.md",
    "pointers": "docs/user/guide/pointers.md",
    "memory_management": "docs/user/guide/memory-management.md",
    "callbacks": "docs/user/guide/callbacks.md",
    "enumerations": "docs/user/guide/enumerations.md",
    "raw_addresses": "docs/user/guide/raw-addresses.md",
    "error_handling": "docs/user/guide/error-handling.md",
    "building_shared_library": "docs/user/guide/building-shared-library.md",
    "source_parsing": "docs/user/examples/recipes/inspect-fortran-api.md",
    "source_preprocessing": "docs/user/examples/recipes/compiler-preprocessing.md",
    "command_line_interface": "docs/user/reference/cli-commands.md",
    "semantic_ir": "docs/user/reference/semantic-ir.md",
    "semantic_pyi_format": "docs/user/reference/semantic-pyi-format.md",
    "pyi_contracts/exports_and_modules": "docs/user/reference/pyi-contracts/exports-and-modules.md",
    "pyi_contracts/functions_and_classes": "docs/user/reference/pyi-contracts/functions-and-classes.md",
    "pyi_contracts/calls_and_results": "docs/user/reference/pyi-contracts/calls-and-results.md",
}
STAGES = {
    "parsing",
    "probes",
    "preprocessing",
    "semantics",
    "policy",
    "codegen",
    "compiling",
    "pipeline",
    "runtime",
    "end_to_end",
}
FORTRAN_TOP_LEVEL_DIRECTORIES = {
    "_support",
    *(Path(feature).parts[0] for feature in FEATURE_DOCS),
    "infrastructure",
}
INFRASTRUCTURE_OWNERS = {
    "infrastructure/policy/",
    "infrastructure/codegen/",
}
FEATURE_ROW = re.compile(
    r"^\| \[(?P<status>[ x])\] \| \[[^]]+\]\((?P<documentation>[^)]+)\) "
    r"\| `(?P<feature>[^`]+)/` \|$",
    re.MULTILINE,
)


def _roadmap_feature_rows() -> dict[str, tuple[str, Path]]:
    rows = {}
    matches = list(FEATURE_ROW.finditer(ROADMAP.read_text(encoding="utf-8")))
    assert len(matches) == len(FEATURE_DOCS)
    for match in matches:
        documentation = (ROADMAP.parent / match.group("documentation")).resolve()
        rows[match.group("feature")] = (match.group("status"), documentation)
    return rows


def _feature_owner(relative: Path) -> str | None:
    parts = relative.parts
    for feature in sorted(FEATURE_DOCS, key=lambda item: len(Path(item).parts), reverse=True):
        owner_parts = Path(feature).parts
        if parts[: len(owner_parts)] == owner_parts:
            return feature
    return None


def _python_references(path: Path) -> tuple[set[str], set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imports.update(
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    strings = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    return imports, strings


def test_language_roots_are_documented_and_exist() -> None:
    test_index = (TEST_ROOT / "README.md").read_text(encoding="utf-8")
    for language in ("fortran", "c", "shared"):
        root = TEST_ROOT / language
        assert root.is_dir()
        assert (root / "README.md").is_file()
        assert f"tests/{language}/" in test_index


def test_fortran_index_maps_every_documented_feature_to_one_command() -> None:
    text = FORTRAN_INDEX.read_text(encoding="utf-8")
    for feature, documentation in FEATURE_DOCS.items():
        assert (REPO_ROOT / documentation).is_file()
        assert text.count(f"](../../{documentation})") == 1
        assert text.count(f"`{feature}/`") == 1
        assert text.count(f"`python3 -m pytest -q tests/fortran/{feature}`") == 1


def test_roadmap_feature_rows_match_the_fortran_index_contract() -> None:
    rows = _roadmap_feature_rows()
    assert set(rows) == set(FEATURE_DOCS)
    for feature, (status, documentation) in rows.items():
        assert documentation == (REPO_ROOT / FEATURE_DOCS[feature]).resolve()
        if status == "x":
            assert (FEATURE_ROOT / feature).is_dir()


def test_fortran_tree_uses_only_documented_top_level_owners() -> None:
    actual = {path.name for path in FORTRAN_ROOT.iterdir() if path.is_dir() and path.name != "__pycache__"}
    assert actual <= FORTRAN_TOP_LEVEL_DIRECTORIES


def test_feature_directories_and_pytest_modules_have_documented_owners() -> None:
    if not FEATURE_ROOT.exists():
        return

    allowed_roots = {Path(feature).parts[0] for feature in FEATURE_DOCS}
    actual_roots = {
        path.name
        for path in FEATURE_ROOT.iterdir()
        if path.is_dir() and path.name not in {"__pycache__", "_support", "infrastructure"}
    }
    assert actual_roots <= allowed_roots

    pyi_contracts = FEATURE_ROOT / "pyi_contracts"
    if pyi_contracts.exists():
        allowed_pyi_owners = {
            Path(feature).parts[1] for feature in FEATURE_DOCS if feature.startswith("pyi_contracts/")
        }
        actual_pyi_owners = {
            path.name for path in pyi_contracts.iterdir() if path.is_dir() and path.name != "__pycache__"
        }
        assert actual_pyi_owners <= allowed_pyi_owners

    for feature in FEATURE_DOCS:
        owner = FEATURE_ROOT / feature
        if not owner.exists():
            continue
        child_directories = {path.name for path in owner.iterdir() if path.is_dir() and path.name != "__pycache__"}
        assert child_directories <= STAGES

    feature_modules = (
        module
        for module in FEATURE_ROOT.rglob("test_*.py")
        if module.relative_to(FEATURE_ROOT).parts[0] in allowed_roots
    )
    for module in feature_modules:
        relative = module.relative_to(FEATURE_ROOT)
        owner = _feature_owner(relative)
        assert owner is not None, relative.as_posix()
        owner_depth = len(Path(owner).parts)
        assert len(relative.parts) > owner_depth + 1, relative.as_posix()
        assert relative.parts[owner_depth] in STAGES, relative.as_posix()


def test_fortran_index_names_every_infrastructure_owner() -> None:
    text = FORTRAN_INDEX.read_text(encoding="utf-8")
    for owner in INFRASTRUCTURE_OWNERS:
        assert f"`{owner}`" in text


def test_real_library_examples_have_single_native_source_owners() -> None:
    assert (BLAS_EXAMPLE_ROOT / "native").is_dir()
    assert (LAPACK_EXAMPLE_ROOT / "native").is_dir()
    assert len(tuple((BLAS_EXAMPLE_ROOT / "native").iterdir())) == 155
    assert len(tuple((LAPACK_EXAMPLE_ROOT / "native").iterdir())) == 2062


def test_final_language_roots_do_not_cross_import_or_read_fixtures() -> None:
    forbidden_by_root = {
        TEST_ROOT / "fortran": (("tests.c", "tests/c/"),),
        TEST_ROOT / "c": (("tests.fortran", "tests/fortran/"),),
        TEST_ROOT / "shared": (
            ("tests.c", "tests/c/"),
            ("tests.fortran", "tests/fortran/"),
        ),
    }
    violations = []
    for root, forbidden in forbidden_by_root.items():
        for path in root.rglob("*.py"):
            relative = path.relative_to(root)
            if "architecture" in relative.parts:
                continue
            imports, strings = _python_references(path)
            for reference in imports:
                if any(reference == module or reference.startswith(f"{module}.") for module, _ in forbidden):
                    violations.append(f"{path.relative_to(REPO_ROOT)}: {reference}")
            if root == TEST_ROOT / "shared" and relative.parts[0] == "docs":
                continue
            for reference in strings:
                if any(fixture_path in reference for _, fixture_path in forbidden):
                    violations.append(f"{path.relative_to(REPO_ROOT)}: {reference}")
    assert violations == []
