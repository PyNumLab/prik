"""Verify the documentation architecture contract."""

from __future__ import annotations

from functools import cache
from pathlib import Path
import re
import subprocess
import sys

import pytest
import x2py


ROOT = Path(__file__).parents[2]
DOCS_ROOT = ROOT / "docs"
FEATURE_MATRIX_PATH = DOCS_ROOT / "user/language-support/feature-matrix.md"
CLI_REFERENCE_PATH = DOCS_ROOT / "user/reference/cli-commands.md"
PYTHON_API_REFERENCE_PATH = DOCS_ROOT / "user/reference/python-api.md"
DOCUMENTATION_CHECKLIST_PATH = DOCS_ROOT / "maintainer/roadmap/documentation-content-checklist.md"
DOC_PATHS = sorted(path for path in DOCS_ROOT.rglob("*.md") if "old_docs" not in path.parts)
WEBSITE_DOCUMENTATION_PATHS = [
    DOCS_ROOT / "index.md",
    *sorted((DOCS_ROOT / "user").rglob("*.md")),
    *sorted((DOCS_ROOT / "developer").rglob("*.md")),
    *sorted((DOCS_ROOT / "maintainer").rglob("*.md")),
]
LEARNING_DOCUMENTATION_PATHS = [
    *sorted((DOCS_ROOT / "user").rglob("*.md")),
    *sorted((DOCS_ROOT / "developer").rglob("*.md")),
]
DEFERRED_C_PAGE_PATHS = [
    ROOT / "docs/maintainer/design/cpython-integration.md",
    ROOT / "docs/developer/c-parser-reference.md",
    ROOT / "docs/user/examples/recipes/inspect-c-api.md",
]
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
NEXT_NAVIGATION = re.compile(r"^\s*(?:#{2,6}\s+Next|\*\*Next\*\*:?)\s*$", re.IGNORECASE)
NEXT_SECTION_BOUNDARY = re.compile(r"^\s*(?:#{2,6}\s+|---\s*$|\*\*[^*]+\*\*)")
ALLOWED_CONTEXTUAL_FORWARD_LINK_SOURCE_PREFIXES = ("user/getting-started/", "user/guide/")
ALLOWED_CONTEXTUAL_FORWARD_LINK_PREFIXES = ("user/reference/pyi-contracts/",)
C_DOCS_START = "<!-- X2PY_C_DOCS_START"
C_DOCS_END = "X2PY_C_DOCS_END -->"
C_DOCS_DISABLED = "<!-- X2PY_C_DOCS_DISABLED:"
VISIBLE_C_DOCUMENTATION_EXCEPTIONS = {
    "docs/user/reference/cli-commands.md": ("C INCLUDE OPTIONS", "{fortran,c}"),
    "docs/user/guide/enumerations.md": ("bind(C)",),
    "docs/user/guide/wrapping-derived-types.md": ("bind(C)",),
    "docs/user/guide/arrays.md": ("ORDER_C", "C-contiguous", "C-order", "C-oriented", 'order="C"'),
    "docs/user/guide/raw-addresses.md": ("C-order", "C ordering"),
    "docs/user/reference/semantic-pyi-format.md": (
        "ORDER_C",
        "C-contiguous",
        "C-order",
        "C-oriented",
        "bind(C)",
        "c_input",
    ),
}
VISIBLE_C_DOCUMENTATION = re.compile(
    r"(?:"
    r"(?<![A-Za-z0-9_])C(?:\+\+)?(?![A-Za-z0-9_])"
    r"|CPython"
    r"|Cython"
    r"|C-input"
    r"|bind\s*\(\s*c\s*\)"
    r"|```c(?:\s|$)"
    r"|\b(?:c_parser|c2ir|fortran_to_c|c_to_python|cpython_api|cpythoncode)\b"
    r"|\b(?:ccode|cpreprocessor)\.py\b"
    r"|\btest_c(?:2ir|_(?:semantic|parser|declarations|functions|structs|project|compiler|corpus|fixture|json|error|public))[A-Za-z0-9_]*\b"
    r"|\b(?:bind_c|iso_c_binding)\b"
    r"|\b[A-Za-z][A-Za-z0-9_]*_c\b"
    r"|\bc_[A-Za-z0-9_]+\b"
    r"|\b(?:ORDER_C|REQUIRE_C_CONTIGUOUS|NPY_C_CONTIGUOUS)\b"
    r"|\b(?:CToIR|CFile|CProject|CParse|CDiagnostic)[A-Za-z0-9_]*\b"
    r"|\b(?:parse_c|c_file|c_project|c_function|c_parameter|c_struct|c_type)_[A-Za-z0-9_]+\b"
    r"|(?:tests/data/c|tests/parser/c|x2py/parsers/c|/c/general/)"
    r"|(?:c-parser|inspect-c-api|c-api)"
    r"|\b(?:structs?|unions?|typedefs?|declarators?|bitfields?|K&R)\b"
    r"|--language\s+c\b"
    r"|(?:fortran\|c|\{fortran,c\}|\bc11\b|\bc17\b|\bc23\b)"
    r"|\"language\"\s*:\s*\"c\""
    r"|\.(?:c|h)(?:\b|`)"
    r"|\b(?:CFLAGS|CC|gcc(?:-\d+)?|clang(?:-\d+)?|cJSON)\b"
    r"|\bc-type(?:s|\b)"
    r")"
)
REQUIRED_METADATA = {"title", "audience", "prerequisites", "related", "status", "publication"}
ALLOWED_PUBLICATION_STATES = {"draft", "reviewed"}
ALLOWED_STATUSES = {
    "active-roadmap",
    "design",
    "draft",
    "maintained",
    "not-yet-implemented",
    "planned-documentation",
}
TODO_STATUSES = {"draft", "not-yet-implemented", "planned-documentation"}
REQUIRED_AREA_INDEXES = [
    "user/index.md",
    "user/getting-started/index.md",
    "user/guide/index.md",
    "user/tutorials/index.md",
    "user/examples/index.md",
    "user/reference/index.md",
    "user/language-support/index.md",
    "user/faq/index.md",
    "user/troubleshooting/index.md",
    "user/changelog/index.md",
    "developer/index.md",
    "developer/contributing/index.md",
    "maintainer/README.md",
    "maintainer/design/index.md",
    "maintainer/internal-architecture/index.md",
    "maintainer/roadmap/index.md",
]
REQUIRED_REFERENCE_PAGES = [
    "user/reference/index.md",
    "user/reference/cli-commands.md",
    "user/reference/python-api.md",
    "user/reference/fortran-wrapper.md",
    "user/reference/semantic-ir.md",
    "user/reference/semantic-pyi-format.md",
    "user/reference/pyi-contracts/index.md",
    "user/reference/pyi-contracts/exports-and-modules.md",
    "user/reference/pyi-contracts/functions-and-classes.md",
    "user/reference/pyi-contracts/calls-and-results.md",
    "user/reference/diagnostic-codes.md",
]
REQUIRED_ROADMAP_PAGES = [
    "maintainer/roadmap/index.md",
    "maintainer/roadmap/semantic-pyi-wrapper-checklist.md",
    "maintainer/roadmap/documentation-content-checklist.md",
]
REQUIRED_GETTING_STARTED_PAGES = [
    "user/getting-started/index.md",
    "user/getting-started/installation.md",
    "user/getting-started/verification.md",
    "user/getting-started/first-wrapped-function.md",
    "user/getting-started/first-wrapped-module.md",
    "user/getting-started/beginner-workflow.md",
]
REQUIRED_USER_GUIDE_PAGES = [
    "user/guide/index.md",
    "user/guide/data-types.md",
    "user/guide/arrays.md",
    "user/guide/strings.md",
    "user/guide/wrapping-functions.md",
    "user/guide/wrapping-subroutines.md",
    "user/guide/wrapping-modules.md",
    "user/guide/optional-arguments.md",
    "user/guide/generic-interfaces.md",
    "user/guide/wrapping-derived-types.md",
    "user/guide/allocatables.md",
    "user/guide/pointers.md",
    "user/guide/memory-management.md",
    "user/guide/callbacks.md",
    "user/guide/enumerations.md",
    "user/guide/raw-addresses.md",
    "user/guide/error-handling.md",
    "user/guide/building-shared-library.md",
]
CLI_HELP_GROUP_HEADINGS = [
    "commands:",
    "positional arguments:",
    "input selection:",
    "input options:",
    "generation modes:",
    "compiler and preprocessing options:",
    "preprocessing options:",
    "C include options:",
    "report options:",
    "compiler options:",
    "wrapper options:",
    "native options:",
    "probe options:",
    "execution options:",
    "output options:",
    "diagnostic options:",
]
CLI_REFERENCE_OPTIONS = [
    "paths",
    "--help-build",
    "--language",
    "--pyi",
    "--sources",
    "--preprocessor-adapter",
    "--compiler",
    "--preprocess-template",
    "-I",
    "--include-dir",
    "-D",
    "--define",
    "-U",
    "--undef",
    "--std",
    "--compiler-arg",
    "--show-vars",
    "--print-limit",
    "--makefile",
    "--strict-wrapper-names",
    "--build-manifest",
    "--native-fortran-sources",
    "--native-compile-flags",
    "--native-objects",
    "--native-library",
    "--native-link-item",
    "--native-library-dir",
    "--format",
    "--expr",
    "--runner",
    "--cache-dir",
    "--refresh",
    "--json",
    "--out",
    "--out-dir",
    "--verbose",
    "--no-color",
    "--debug",
]
CLI_VISIBLE_HELP_OPTIONS = CLI_REFERENCE_OPTIONS
REQUIRED_SOURCE_NAVIGATION_PAGES = [
    "developer/source-map.md",
    "developer/feature-to-code-map.md",
    "developer/repository-structure.md",
]
SOURCE_NAVIGATION_CORPUS = [
    "docs/developer/source-map.md",
    "docs/developer/feature-to-code-map.md",
    "docs/developer/repository-structure.md",
    "docs/maintainer/internal-architecture/pipeline-map.md",
    "x2py/README.md",
    "x2py/parsers/README.md",
    "x2py/parsers/c/README.md",
    "x2py/parsers/fortran/README.md",
    "x2py/parsers/pyi/README.md",
    "x2py/semantics/README.md",
    "x2py/compiling/README.md",
]
SOURCE_NAVIGATION_HOTSPOTS = [
    "x2py/__init__.py",
    "x2py/cli.py",
    "x2py/pipeline/build.py",
    "x2py/pipeline/preprocessing.py",
    "x2py/probes/c_types.py",
    "x2py/probes/fortran_types.py",
    "x2py/semantics/ownership.py",
    "x2py/parsers/c/parser.py",
    "x2py/parsers/c/cli.py",
    "x2py/parsers/fortran/parser.py",
    "x2py/parsers/fortran/cli.py",
    "x2py/parsers/pyi/parser.py",
    "x2py/semantics/models.py",
    "x2py/semantics/fortran2ir.py",
    "x2py/semantics/c2ir.py",
    "x2py/semantics/pyi2ir.py",
    "x2py/pipeline/pyi.py",
    "x2py/semantics/policy_completion.py",
    "x2py/wrapper_codegen/plan.py",
    "x2py/wrapper_codegen/planner.py",
    "x2py/wrapper_codegen/generator.py",
    "x2py/wrapper_codegen/c/binding.py",
    "x2py/wrapper_codegen/fortran/bridge.py",
    "x2py/wrapper_codegen/printers/pyi_printer.py",
    "x2py/wrapper_codegen/printers/source_printers.py",
    "x2py/compiling/objects.py",
    "x2py/compiling/compilers.py",
    "x2py/compiling/native_support.py",
    "x2py/naming/policy.py",
    "x2py/binding_support/",
]
SOURCE_NAVIGATION_PUBLIC_DOCS = [
    "README.md",
    "docs/user/examples/recipes/compiler-preprocessing.md",
    "docs/user/examples/recipes/inspect-c-api.md",
    "docs/user/examples/recipes/inspect-fortran-api.md",
    "docs/user/examples/recipes/semantic-pyi-contracts.md",
    "docs/user/reference/fortran-wrapper.md",
    "docs/user/reference/pyi-contracts/index.md",
    "docs/user/reference/cli-commands.md",
    "docs/user/reference/diagnostic-codes.md",
    "docs/user/reference/python-api.md",
    "docs/user/reference/semantic-ir.md",
    "docs/user/reference/semantic-pyi-format.md",
    "docs/developer/build-system.md",
    "docs/developer/c-parser-reference.md",
    "docs/developer/fortran-parser-reference.md",
    "docs/developer/quality-assurance.md",
    "docs/user/language-support/feature-matrix.md",
]
SOURCE_NAVIGATION_TEST_TARGETS = [
    "tests/parser/",
    "tests/parser/c/",
    "tests/cli/",
    "tests/parsing/fortran/test_fortran_fixture_suite.py",
    "tests/parsing/fortran/test_public_entrypoints.py",
    "tests/pipeline/preprocessing/",
    "tests/pipeline/preprocessing/test_parser_boundaries.py",
    "tests/pyi/",
    "tests/pipeline/pyi_builds/test_contract_package_generation.py",
    "tests/pipeline/pyi_builds/test_contract_fixtures.py",
    "tests/parsing/pyi/",
    "tests/semantics/",
    "tests/semantics/conversion/c/",
    "tests/semantics/conversion/fortran/",
    "tests/wrapper_codegen/printers/",
    "tests/wrapper_codegen/printers/test_modern_example.py",
    "tests/docs/test_examples.py",
    "tests/docs/test_structure.py",
    "tests/wrapper/fortran/",
    "tests/wrapper/fortran/build_from_pyi/test_pyi_wrapper_builds.py",
    "tests/wrapper/fortran/multiple_files/test_multi_source_builds.py",
    "tests/wrapper/fortran/build_from_source/test_build_modes.py",
    "tests/wrapper/fortran/build_from_source/test_runtime_abi.py",
]
PACKAGE_README_NAVIGATION_REFERENCES = [
    "docs/developer/source-map.md",
    "docs/developer/feature-to-code-map.md",
]
LEGACY_ACTIVE_DOC_REFERENCES = [
    "docs/c_parser.md",
    "docs/fortran_parser.md",
    "docs/fortran_wrapper.md",
    "docs/pyi_format.md",
    "docs/pyi_wrapper_checklist.md",
    "docs/quality.md",
    "docs/semantics.md",
]
FEATURE_MATRIX_STATUSES = {
    "Supported",
    "Partially supported",
    "Unsupported",
    "Planned",
    "Not implemented",
}
FEATURE_MATRIX_REQUIRED_FEATURES = [
    "Fortran source wrapper builds",
    "Scalar functions, subroutines, and baseline arrays",
    "Generic procedure interfaces",
    "Defined operators and assignment overloads",
    "Output arguments and multiple results",
    "Optional arguments",
    "Allocatable array handles, descriptor arguments, and owned results",
    "Pointer scalar projections and array handles",
    "Array-valued function results",
    "NumPy array argument contracts",
    "Derived-type scalar boundaries and methods",
    "Default and keyword constructors with finalizers",
    "Module variables, constants, saved state, and common-block procedure state",
    "Fortran enum constants",
    "Scalar character arguments, results, and fields",
    "Scalar kind coverage",
    "Caller-ordered multi-source builds, Makefiles, verbose mode, and output placement",
    "Visibility, naming, keyword escaping, and collision policy",
    "Immediate call-scoped Python callbacks",
    "Runtime error projection, GIL policy, recursion, OpenMP path, and GNU ABI checks",
    "Fortran parse, semantic IR, and `.pyi` inspection",
    "Semantic `.pyi` wrapper builds from explicit native artifacts",
    "Assumed-size, assumed-rank, and lower-bound array contracts",
    "Scalar inheritance and polymorphic dispatch",
    "Pointer-array results and unproved reassociation",
    "Persistent callbacks and procedure pointers",
    "Advanced multi-source dependency discovery and external-library integration",
    "Blocked array forms",
    "Unsupported polymorphic forms",
    "Generic constructor interfaces and overloaded runtime initialization",
    "Character arrays and mutable deferred-length character storage",
    "Wider-than-supported real, complex, and logical storage",
    "Full semantic `.pyi` parity across all wrapper scenarios",
    "MPI examples and distribution constraints",
    "Generated reference pages for modules, functions, and classes",
]
REQUIRED_EXAMPLE_RECIPE_PAGES = [
    "user/examples/recipes/build-and-import-python-api.md",
    "user/examples/recipes/inspect-fortran-api.md",
    "user/examples/recipes/inspect-c-api.md",
    "user/examples/recipes/semantic-pyi-contracts.md",
    "user/examples/recipes/control-cli-output.md",
    "user/examples/recipes/use-python-inspection-apis.md",
    "user/examples/recipes/compiler-preprocessing.md",
]
EXAMPLE_DOCUMENTATION_PAGES = [
    path.relative_to(DOCS_ROOT).as_posix()
    for path in sorted((DOCS_ROOT / "user/examples").rglob("*.md"))
    if path.name != "index.md"
]
MAJOR_SOURCE_PACKAGES = [
    "x2py/parsers/",
    "x2py/semantics/",
    "x2py/wrapper_codegen/",
    "x2py/compiling/",
]
PACKAGE_READMES = [
    "x2py/README.md",
    "x2py/parsers/README.md",
    "x2py/semantics/README.md",
    "x2py/compiling/README.md",
]
ARCHIVED_OLD_DOCS = [
    "old_docs/tutorial.md",
    "old_docs/examples.md",
    "old_docs/fortran_wrapper.md",
    "old_docs/semantics.md",
    "old_docs/pyi_format.md",
    "old_docs/diagnostic_codes.md",
    "old_docs/pyi_wrapper_checklist.md",
    "old_docs/developper_guide.md",
    "old_docs/quality.md",
    "old_docs/c_parser.md",
    "old_docs/fortran_parser.md",
    "old_docs/wrapper_design_notes.md",
    "old_docs/architecture/semantic_multilanguage_wrapper_runtime_architecture.md",
]
OLD_TOP_LEVEL_DOCS = [
    "tutorial.md",
    "examples.md",
    "fortran_wrapper.md",
    "semantics.md",
    "pyi_format.md",
    "diagnostic_codes.md",
    "pyi_wrapper_checklist.md",
    "developper_guide.md",
    "quality.md",
    "c_parser.md",
    "fortran_parser.md",
    "wrapper_design_notes.md",
]


def _front_matter(path: Path) -> tuple[dict[str, str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", f"{path.relative_to(ROOT)}: missing front matter"

    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise AssertionError(f"{path.relative_to(ROOT)}: unclosed front matter") from error

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        assert separator, f"{path.relative_to(ROOT)}: invalid front matter line: {line!r}"
        metadata[key.strip()] = value.strip()

    return metadata, "\n".join(lines[end + 1 :])


def _visible_documentation_source(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if path != ROOT / "README.md" and lines and lines[0] == "---":
        lines = lines[lines.index("---", 1) + 1 :]

    visible: list[str] = []
    hidden: str | None = None
    for line in lines:
        stripped = line.strip()
        if stripped == C_DOCS_START:
            assert not hidden, f"{path.relative_to(ROOT)}: nested deferred documentation comment"
            hidden = "deferred-c"
        elif stripped == "<!--":
            assert not hidden, f"{path.relative_to(ROOT)}: nested documentation comment"
            hidden = "ordinary"
        elif stripped == C_DOCS_END:
            assert hidden == "deferred-c", f"{path.relative_to(ROOT)}: unmatched deferred documentation comment end"
            hidden = None
        elif stripped == "-->" and hidden == "ordinary":
            hidden = None
        elif hidden == "deferred-c":
            assert "--" not in line, f"{path.relative_to(ROOT)}: invalid double hyphen in deferred comment"
        elif hidden == "ordinary":
            continue
        elif not line.lstrip().startswith(C_DOCS_DISABLED):
            visible.append(line)
    assert not hidden, f"{path.relative_to(ROOT)}: unclosed deferred documentation comment"
    return "\n".join(visible)


def _instructional_body_without_next(body: str) -> str:
    instructional_lines: list[str] = []
    inside_next = False

    for line in body.splitlines():
        if NEXT_NAVIGATION.match(line):
            inside_next = True
            continue
        if inside_next and NEXT_SECTION_BOUNDARY.match(line):
            inside_next = False
        if not inside_next:
            instructional_lines.append(line)

    return "\n".join(instructional_lines)


def _next_navigation_items(body: str) -> list[tuple[int, str, bool]]:
    items: list[tuple[int, str, bool]] = []
    current_line: int | None = None
    current_parts: list[str] = []
    inside_next = False

    def flush_current() -> None:
        nonlocal current_line, current_parts
        if current_line is not None:
            items.append((current_line, " ".join(current_parts), True))
            current_line = None
            current_parts = []

    for line_number, line in enumerate(body.splitlines(), start=1):
        if NEXT_NAVIGATION.match(line):
            flush_current()
            inside_next = True
            continue
        if inside_next and NEXT_SECTION_BOUNDARY.match(line):
            flush_current()
            inside_next = False
            continue
        if not inside_next or not line.strip():
            continue
        if line.startswith("- "):
            flush_current()
            current_line = line_number
            current_parts = [line[2:].strip()]
        elif current_line is not None and line.startswith("  "):
            current_parts.append(line.strip())
        else:
            flush_current()
            items.append((line_number, line.strip(), False))

    flush_current()
    return items


def _combined_text(relative_paths: list[str]) -> str:
    return "\n".join((ROOT / relative_path).read_text(encoding="utf-8") for relative_path in relative_paths)


@cache
def _site_navigation_positions() -> dict[str, int]:
    navigation_entry = re.compile(r": ([^#\s]+\.md)\s*$")
    paths: list[str] = []
    for line in (ROOT / "mkdocs.yml").read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        match = navigation_entry.search(line)
        if match:
            paths.append(match.group(1))
    return {path: index for index, path in enumerate(paths)}


def _user_guide_index_order() -> list[str]:
    _, body = _front_matter(DOCS_ROOT / "user/guide/index.md")
    guide_root = (DOCS_ROOT / "user/guide").resolve()
    paths: list[str] = []
    for target in MARKDOWN_LINK.findall(body):
        resolved = (guide_root / target).resolve()
        if resolved.parent != guide_root or resolved.name == "index.md":
            continue
        relative_path = resolved.relative_to(DOCS_ROOT).as_posix()
        if relative_path not in paths:
            paths.append(relative_path)
    return paths


@cache
def _x2py_cli_help() -> str:
    commands = [
        ["--help"],
        ["input.f90", "--help"],
        ["parse", "--help"],
        ["semantics", "--help"],
        ["generate", "--help"],
        ["probe", "--help"],
    ]
    outputs = []
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", "x2py", *command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs.append(result.stdout)
    return "\n".join(outputs)


def _feature_matrix_rows() -> list[dict[str, str]]:
    header = "| Feature | Status | User docs | Source owner | Evidence | Limitations |"
    columns = ["Feature", "Status", "User docs", "Source owner", "Evidence", "Limitations"]
    rows: list[dict[str, str]] = []
    in_table = False

    for line in FEATURE_MATRIX_PATH.read_text(encoding="utf-8").splitlines():
        if line == header:
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("| ---"):
            continue
        if not line.startswith("|"):
            in_table = False
            continue

        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == len(columns), f"invalid feature matrix row: {line!r}"
        rows.append(dict(zip(columns, cells, strict=True)))

    return rows


FEATURE_MATRIX_ROWS = _feature_matrix_rows()


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_documentation_page_metadata(path: Path) -> None:
    metadata, body = _front_matter(path)
    missing = REQUIRED_METADATA - metadata.keys()
    assert not missing, f"{path.relative_to(ROOT)}: missing metadata fields: {sorted(missing)}"

    for key in REQUIRED_METADATA:
        assert metadata[key], f"{path.relative_to(ROOT)}: metadata field {key!r} is empty"

    assert metadata["status"] in ALLOWED_STATUSES, f"{path.relative_to(ROOT)}: unknown status {metadata['status']!r}"
    assert metadata["publication"] in ALLOWED_PUBLICATION_STATES, (
        f"{path.relative_to(ROOT)}: unknown publication state {metadata['publication']!r}"
    )
    if metadata["status"] in TODO_STATUSES:
        assert "## TODO" in body, f"{path.relative_to(ROOT)}: unfinished pages must include a TODO section"
        assert "TODO:" in body, f"{path.relative_to(ROOT)}: TODO section must contain explicit TODO markers"


@pytest.mark.parametrize(
    "path",
    [
        ROOT / "README.md",
        *(path for path in WEBSITE_DOCUMENTATION_PATHS if _front_matter(path)[0].get("publication") == "reviewed"),
    ],
    ids=lambda path: str(path.relative_to(ROOT)),
)
def test_deferred_c_documentation_is_not_visible(path: Path) -> None:
    visible = _visible_documentation_source(path)
    for allowed_text in VISIBLE_C_DOCUMENTATION_EXCEPTIONS.get(str(path.relative_to(ROOT)), ()):
        visible = visible.replace(allowed_text, "")
    match = VISIBLE_C_DOCUMENTATION.search(visible)
    assert match is None, f"{path.relative_to(ROOT)}: visible deferred documentation: {match.group(0)!r}"


@pytest.mark.parametrize("path", DEFERRED_C_PAGE_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_dedicated_deferred_c_pages_have_no_visible_body(path: Path) -> None:
    assert _visible_documentation_source(path).strip() == ""


def test_deferred_c_pages_are_not_in_site_navigation() -> None:
    lines = (ROOT / "mkdocs.yml").read_text(encoding="utf-8").splitlines()
    active_navigation = "\n".join(line for line in lines if not line.lstrip().startswith("#"))
    assert "Inspect a C API" not in active_navigation
    assert "C Parser Reference" not in active_navigation
    assert any("X2PY_C_DOCS" in line and "inspect-c-api.md" in line for line in lines)
    assert any("X2PY_C_DOCS" in line and "c-parser-reference.md" in line for line in lines)


def test_readme_quick_start_shows_input_source_before_wrapper_build() -> None:
    readme = _visible_documentation_source(ROOT / "README.md")
    quick_start = readme.split("## Installation & Quick Start", maxsplit=1)[1].split(
        "The runtime wrapper mechanism is:",
        maxsplit=1,
    )[0]
    top_help = subprocess.run(
        [sys.executable, "-m", "x2py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert "Basic wrapper build:" in top_help
    for command in (
        "python3 -m x2py scale.f90",
        "python3 -m x2py scale.f90 --out SCALE",
        "python3 -m x2py generate --pyi scale.f90 --out contracts",
    ):
        assert command in quick_start
        assert command in top_help

    help_index = quick_start.index("python3 -m x2py --help")
    fortran_block_index = quick_start.index("```fortran")
    source_build_command_index = quick_start.index(
        "python3 -m x2py scale.f90",
        fortran_block_index,
    )
    default_source_build_tree_index = quick_start.index(
        ".\n  scale.f90\n  scale.so\n  __x2py__/", source_build_command_index
    )
    named_source_build_command_index = quick_start.index(
        "python3 -m x2py scale.f90 --out SCALE",
        default_source_build_tree_index,
    )
    source_build_tree_index = quick_start.index(
        ".\n  scale.f90\n  SCALE.so\n  __x2py__/",
        named_source_build_command_index,
    )
    explicit_source_build_command_index = quick_start.index(
        "python3 -m x2py scale.f90 \\\n  --out SCALE \\\n  --out-dir build/SCALE",
        source_build_tree_index,
    )
    explicit_source_build_tree_index = quick_start.index("build/SCALE/", explicit_source_build_command_index)
    pyi_generation_command_index = quick_start.index(
        "python3 -m x2py generate --pyi scale.f90",
        explicit_source_build_tree_index,
    )
    pyi_contract_tree_index = quick_start.index("contracts/\n  __init__.pyi", pyi_generation_command_index)
    pyi_contract_body_index = quick_start.index(
        "@external\n@native_call([Addr(Arg(0)), Addr(Arg(1))])\ndef scale(\n"
        "    value: Float64,\n    factor: Float64\n) -> Float64: ...",
        pyi_contract_tree_index,
    )
    pyi_build_command_index = quick_start.index(
        "python3 -m x2py contracts/__init__.pyi",
        pyi_contract_body_index,
    )
    native_source_argument_index = quick_start.index("--native-fortran-sources scale.f90", pyi_build_command_index)
    output_name_index = quick_start.index("--out SCALE", native_source_argument_index)
    pyi_build_tree_index = quick_start.index("build/SCALE_from_pyi/", output_name_index)
    direct_import_index = quick_start.index("SCALE.scale(", pyi_build_tree_index)
    package_entry_import_section_index = quick_start.index("The package-entry `.pyi` build", direct_import_index)
    pyi_import_index = quick_start.index("SCALE.scale(", package_entry_import_section_index)
    runtime_output_index = quick_start.index("7.5", pyi_import_index)
    verbose_command_index = quick_start.index(
        "python3 -m x2py scale.f90 \\\n  --out SCALE_debug",
        runtime_output_index,
    )
    verbose_fortran_flag_index = quick_start.index("--wrapper-fortran-flags=-O2", verbose_command_index)
    verbose_c_flag_index = quick_start.index("--wrapper-c-flags=-O2", verbose_fortran_flag_index)
    verbose_output_index = quick_start.index("generated Python binding", verbose_c_flag_index)
    module_lesson_index = quick_start.index("first wrapped module", verbose_output_index)

    assert help_index < fortran_block_index < source_build_command_index
    assert source_build_command_index < default_source_build_tree_index < named_source_build_command_index
    assert named_source_build_command_index < source_build_tree_index < explicit_source_build_command_index
    assert explicit_source_build_command_index < explicit_source_build_tree_index < pyi_generation_command_index
    assert pyi_generation_command_index < pyi_contract_tree_index < pyi_contract_body_index
    assert pyi_contract_body_index < pyi_build_command_index < native_source_argument_index < output_name_index
    assert output_name_index < pyi_build_tree_index < direct_import_index < package_entry_import_section_index
    assert package_entry_import_section_index < pyi_import_index
    assert pyi_import_index < runtime_output_index < verbose_command_index
    assert verbose_command_index < verbose_fortran_flag_index < verbose_c_flag_index < verbose_output_index
    assert verbose_output_index < module_lesson_index
    assert "--parse" not in readme
    assert "--semantics" not in readme
    assert "tests/data/fortran/wrapper/scale.f90" in quick_start
    assert "scale.f90 --json" not in quick_start
    assert "python3 -m x2py solver.f90" not in quick_start
    assert "python3 -m x2py tests/data/fortran/wrapper/scale.f90" not in quick_start
    assert "fruntime_abi_f90" not in readme
    assert "solver.f90" not in readme
    assert "add1" not in readme
    assert "distance2" not in readme
    assert "points_api" not in readme
    assert "point_api" not in readme
    assert "build/points" not in readme
    assert "tests/data/fortran/general/basic_subroutine.f90" not in readme
    assert "contracts/basic_subroutine/basic_subroutine.pyi" not in readme


@pytest.mark.parametrize("relative_path", REQUIRED_AREA_INDEXES)
def test_required_documentation_area_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


def test_documentation_root_uses_three_audience_lanes() -> None:
    directories = {path.name for path in DOCS_ROOT.iterdir() if path.is_dir()}
    root_pages = {path.name for path in DOCS_ROOT.glob("*.md")}
    assert directories == {
        "user",
        "developer",
        "maintainer",
        "javascripts",
        "stylesheets",
        "old_docs",
    }
    assert root_pages == {"index.md"}


@pytest.mark.parametrize(
    ("lane", "audience_terms"),
    [
        ("user", ("users",)),
        ("developer", ("developers", "contributors")),
        ("maintainer", ("maintainers",)),
    ],
)
def test_documentation_lane_has_consistent_audience(lane: str, audience_terms: tuple[str, ...]) -> None:
    for path in (DOCS_ROOT / lane).rglob("*.md"):
        metadata, _ = _front_matter(path)
        assert any(term in metadata["audience"] for term in audience_terms)
        if lane != "maintainer":
            assert "maintainers" not in metadata["audience"]
        else:
            assert metadata["audience"] == "maintainers"


@pytest.mark.parametrize("path", LEARNING_DOCUMENTATION_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_website_documentation_does_not_link_to_maintainer_lane(path: Path) -> None:
    maintainer_root = (DOCS_ROOT / "maintainer").resolve()
    for target in MARKDOWN_LINK.findall(_visible_documentation_source(path)):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / target).resolve()
        assert not resolved.is_relative_to(maintainer_root), (
            f"{path.relative_to(ROOT)}: website link enters maintainer lane: {target}"
        )


def test_readme_documentation_links_follow_site_navigation_order() -> None:
    readme = _visible_documentation_source(ROOT / "README.md")
    documentation = readme.split("## Documentation", maxsplit=1)[1].split(
        "## Development",
        maxsplit=1,
    )[0]
    positions = _site_navigation_positions()
    linked_positions = [
        positions[target.removeprefix("docs/")]
        for target in MARKDOWN_LINK.findall(documentation)
        if target.startswith("docs/")
    ]
    assert linked_positions == sorted(linked_positions)


@pytest.mark.parametrize("relative_path", REQUIRED_REFERENCE_PAGES)
def test_required_reference_page_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", REQUIRED_REFERENCE_PAGES)
def test_reference_page_is_in_site_navigation(relative_path: str) -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert relative_path in site_configuration


@pytest.mark.parametrize("relative_path", REQUIRED_ROADMAP_PAGES)
def test_required_roadmap_page_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


def test_site_navigation_includes_all_publishable_lanes_and_excludes_archive() -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "old_docs/**" in site_configuration
    positions = _site_navigation_positions()
    assert "user/index.md" in positions
    assert "developer/index.md" in positions
    assert "maintainer/README.md" in positions


def test_user_guide_navigation_follows_index_reading_order() -> None:
    positions = _site_navigation_positions()
    navigation_order = [
        path
        for path, _ in sorted(positions.items(), key=lambda item: item[1])
        if path.startswith("user/guide/") and path != "user/guide/index.md"
    ]

    assert navigation_order == _user_guide_index_order()


@pytest.mark.parametrize("relative_path", REQUIRED_GETTING_STARTED_PAGES)
def test_required_getting_started_page_is_maintained_and_navigable(relative_path: str) -> None:
    path = DOCS_ROOT / relative_path
    assert path.is_file()
    metadata, body = _front_matter(path)
    assert metadata["status"] == "maintained"
    assert relative_path in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        assert (path.parent / target).resolve().exists(), f"{relative_path}: missing link target {target}"


@pytest.mark.parametrize("relative_path", REQUIRED_GETTING_STARTED_PAGES)
def test_getting_started_page_is_completed_in_documentation_checklist(relative_path: str) -> None:
    checklist = DOCUMENTATION_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert f"- [x] `docs/{relative_path}`" in checklist


@pytest.mark.parametrize("relative_path", REQUIRED_USER_GUIDE_PAGES)
def test_required_user_guide_page_is_maintained_and_navigable(relative_path: str) -> None:
    path = DOCS_ROOT / relative_path
    assert path.is_file()
    metadata, body = _front_matter(path)
    assert metadata["status"] == "maintained"
    assert relative_path in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        assert (path.parent / target).resolve().exists(), f"{relative_path}: missing link target {target}"


@pytest.mark.parametrize("relative_path", REQUIRED_USER_GUIDE_PAGES)
def test_user_guide_page_is_completed_in_documentation_checklist(relative_path: str) -> None:
    checklist = DOCUMENTATION_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert f"- [x] `docs/{relative_path}`" in checklist


@pytest.mark.parametrize(
    "relative_path",
    [*REQUIRED_GETTING_STARTED_PAGES[1:], *REQUIRED_USER_GUIDE_PAGES[1:], *EXAMPLE_DOCUMENTATION_PAGES],
)
def test_sequential_user_pages_do_not_link_forward_from_instructional_prose(relative_path: str) -> None:
    path = DOCS_ROOT / relative_path
    _, body = _front_matter(path)
    body = _instructional_body_without_next(body)
    positions = _site_navigation_positions()
    if relative_path not in positions:
        pytest.skip(f"{relative_path}: not active in site navigation")
    source_position = positions[relative_path]
    for target in MARKDOWN_LINK.findall(body):
        target_path = (path.parent / target).resolve()
        if not target_path.is_relative_to(DOCS_ROOT):
            continue
        target_relative = target_path.relative_to(DOCS_ROOT).as_posix()
        if target_relative not in positions:
            continue
        if relative_path.startswith(ALLOWED_CONTEXTUAL_FORWARD_LINK_SOURCE_PREFIXES) and target_relative.startswith(
            ALLOWED_CONTEXTUAL_FORWARD_LINK_PREFIXES
        ):
            continue
        assert positions[target_relative] <= source_position, f"{relative_path}: forward link to {target_relative}"


@pytest.mark.parametrize(
    "relative_path",
    [*REQUIRED_GETTING_STARTED_PAGES[1:], *REQUIRED_USER_GUIDE_PAGES[1:]],
)
def test_next_sections_use_linked_bullet_destinations(relative_path: str) -> None:
    _, body = _front_matter(DOCS_ROOT / relative_path)
    for line_number, item, is_bullet in _next_navigation_items(body):
        assert is_bullet, f"{relative_path}:{line_number}: Next content must be a bullet item"
        assert MARKDOWN_LINK.search(item), f"{relative_path}:{line_number}: Next item must include a Markdown link"


@pytest.mark.parametrize("relative_path", REQUIRED_USER_GUIDE_PAGES)
def test_user_guide_commands_do_not_expose_fixture_paths(relative_path: str) -> None:
    page = (DOCS_ROOT / relative_path).read_text(encoding="utf-8")
    assert "python3 -m x2py tests/" not in page


@pytest.mark.parametrize(
    "relative_path",
    [
        "index.md",
        "user/index.md",
        *REQUIRED_GETTING_STARTED_PAGES,
        *REQUIRED_USER_GUIDE_PAGES,
    ],
)
def test_reviewed_user_pages_do_not_expose_internal_evidence(relative_path: str) -> None:
    page = _visible_documentation_source(DOCS_ROOT / relative_path)
    assert "## Evidence" not in page
    assert "## Runtime Evidence" not in page
    assert "Runtime tests:" not in page
    assert "../../../tests/" not in page
    assert "../../tests/" not in page
    assert "../tests/" not in page


@pytest.mark.parametrize(
    "relative_path",
    [
        "index.md",
        "user/index.md",
        *REQUIRED_GETTING_STARTED_PAGES,
        *REQUIRED_USER_GUIDE_PAGES,
    ],
)
def test_reviewed_user_pages_do_not_contain_editorial_notes(relative_path: str) -> None:
    page = _visible_documentation_source(DOCS_ROOT / relative_path).casefold()
    for phrase in (
        "i kept your",
        "let me know if you want",
        "original content had",
        "restore/polish",
    ):
        assert phrase not in page


def test_getting_started_overview_uses_standalone_example() -> None:
    overview = (DOCS_ROOT / "user/getting-started/index.md").read_text(encoding="utf-8")

    assert "scale.scale(np.float64(3.0), np.float64(2.5))" in overview


def test_documentation_homepage_demonstrates_x2py_before_getting_started() -> None:
    page = (DOCS_ROOT / "index.md").read_text(encoding="utf-8")
    introduction_index = page.index("Turn Fortran into natural Python APIs")
    build_index = page.index("python3 -m x2py points.f90 --out geometry")
    example_heading_index = page.index("## See it in action")
    source_index = page.index("```fortran", example_heading_index)
    generated_api_index = page.index("**Generated Python API:**", source_index)
    constructor_index = page.index("item = points.point(", generated_api_index)
    mutation_index = page.index("points.move(item", constructor_index)
    result_index = page.index("# 4.0 2.0", mutation_index)
    contract_index = page.index("Edit the generated `.pyi` contract", result_index)
    features_index = page.index("## Key Features", contract_index)
    getting_started_index = page.index("Getting Started Guide →", features_index)

    assert introduction_index < build_index < example_heading_index < source_index
    assert source_index < generated_api_index < constructor_index < mutation_index
    assert mutation_index < result_index < contract_index < features_index < getting_started_index
    assert "print(points.norm_squared(item))" in page
    assert "# 20.0" in page
    assert "[contract guide](user/reference/pyi-contracts/index.md)" in page
    assert "{ .x2py-primary-cta }" in page
    assert "developer/index.md" not in page
    assert "maintainer/README.md" not in page
    assert "user/guide/" not in page


def test_readme_opening_uses_the_homepage_message_and_showcase() -> None:
    homepage = _visible_documentation_source(DOCS_ROOT / "index.md")
    readme = _visible_documentation_source(ROOT / "README.md")
    readme_opening = readme.split("## Installation & Quick Start", maxsplit=1)[0]
    shared_content = (
        "**Turn Fortran into natural Python APIs.**",
        "Build clean, importable native extensions from supported Fortran without\nwriting low-level binding code.",
        "python3 -m x2py points.f90 --out geometry",
        "<!-- x2py-doc-source: tests/data/fortran/wrapper/home_points.f90 -->",
        "import geometry.points as points",
        "item = points.point(x=np.float64(3.0), y=np.float64(4.0))",
        "points.move(item, np.float64(1.0), np.float64(-2.0))",
        "print(points.norm_squared(item))  # 20.0",
        "No manual bindings are required.",
        "## Key Features",
        "- Editable `.pyi` contracts and readable generated docstrings",
    )

    for content in shared_content:
        assert content in homepage
        assert content in readme_opening

    assert readme.count("\nmodule points\n") == 1
    assert readme.count("python3 -m x2py points.f90 --out geometry") == 1
    assert readme.count("import geometry.points as points") == 1


def test_documentation_links_to_documentation_stay_on_the_website() -> None:
    github_documentation_prefixes = (
        "https://github.com/PyNumLab/x2py/blob/main/docs/",
        "https://github.com/PyNumLab/x2py/tree/main/docs/",
    )

    for path in DOC_PATHS:
        prose_lines: list[str] = []
        fence: str | None = None
        for line in _visible_documentation_source(path).splitlines():
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if fence is not None:
                if line.strip() == fence:
                    fence = None
                continue
            if marker is not None:
                fence = marker.group(1)
                continue
            prose_lines.append(line)

        for target in MARKDOWN_LINK.findall("\n".join(prose_lines)):
            if "/" not in target and "." not in target:
                continue
            assert not target.startswith(github_documentation_prefixes), (
                f"{path.relative_to(ROOT)}: documentation link points to GitHub: {target}"
            )
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            assert resolved != (ROOT / "README.md").resolve(), (
                f"{path.relative_to(ROOT)}: documentation workflow points to the repository README"
            )
            if resolved.is_relative_to(DOCS_ROOT.resolve()):
                assert resolved.is_file(), (
                    f"{path.relative_to(ROOT)}: documentation link must target a website page or asset: {target}"
                )


def test_first_wrapped_function_shows_contract_and_mentions_later_support_boundaries() -> None:
    page = (DOCS_ROOT / "user/getting-started/first-wrapped-function.md").read_text(encoding="utf-8")
    source_index = page.index("scale.f90")
    build_index = page.index("python3 -m x2py scale.f90")
    command_index = page.index("python3 -m x2py generate --pyi scale.f90")
    contract_index = page.index(
        "@external\n@native_call([Addr(Arg(0)), Addr(Arg(1))])\ndef scale(\n"
        "    value: Float64,\n    factor: Float64\n) -> Float64: ..."
    )
    docstring_index = page.index("## Inspect the Generated Docstring")
    call_index = page.index("## Call the Function")

    assert source_index < command_index < contract_index < build_index
    assert build_index < docstring_index < call_index
    assert "editable description of the\nPython interface" in page
    assert "scale(value, factor) -> float64" in page
    assert "assert result == 7.5" in page
    assert "isinstance(result, float)" not in page
    assert "## Current Limitations" not in page


def test_first_wrapped_module_shows_local_input_and_generated_contract() -> None:
    page = (DOCS_ROOT / "user/getting-started/first-wrapped-module.md").read_text(encoding="utf-8")
    source_index = page.index("module_state.f90")
    build_index = page.index("python3 -m x2py module_state.f90")
    docstring_index = page.index("## Inspect the Generated Docstring")
    usage_index = page.index("## Usage Example")
    inspect_index = page.index("python3 -m x2py generate --pyi module_state.f90")
    contract_index = page.index("## Key Rules")

    assert source_index < build_index < docstring_index < usage_index < inspect_index < contract_index
    assert "print(mod.__doc__)" in page
    assert "module_state\n\nModule Attributes" in page
    assert "summarize() -> int32" in page
    assert "scaled_counter() -> float64" in page
    assert "next_local() -> int32" in page
    assert "nmax : int32\n    Read-only constant." in page
    assert "counter : int32" in page
    assert "scale : float64" in page
    assert "saved_counter : int32" in page
    assert "Assignment writes through to native storage." not in page
    assert "fmodule_vars_f90" not in page
    assert "## Current Limitations" not in page


def test_beginner_workflow_reuses_scale_example_without_renaming_it() -> None:
    page = (DOCS_ROOT / "user/getting-started/beginner-workflow.md").read_text(encoding="utf-8")
    source_reference_index = page.index("scale.f90")
    layout_index = page.index("src/")
    contract_index = page.index("python3 -m x2py generate --pyi src/scale.f90")
    build_index = page.index("python3 -m x2py src/scale.f90")
    smoke_index = page.index("result = scale.scale(np.float64(3.0), np.float64(2.5))")
    editing_index = page.index("## 4. Optionally Edit the Contract")
    edited_contract_index = page.index("contracts/scale/__init__.pyi", editing_index)
    diagnosis_index = page.index("## 5. Diagnose a Failure")

    assert source_reference_index < layout_index < contract_index < build_index
    assert build_index < smoke_index < editing_index < edited_contract_index < diagnosis_index
    assert "scale_api" not in page


def test_user_guide_teaches_small_contract_edits_in_context() -> None:
    arrays = _visible_documentation_source(DOCS_ROOT / "user/guide/arrays.md")
    strings = _visible_documentation_source(DOCS_ROOT / "user/guide/strings.md")
    functions = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-functions.md")
    modules = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-modules.md")
    generics = _visible_documentation_source(DOCS_ROOT / "user/guide/generic-interfaces.md")
    derived = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-derived-types.md")
    errors = _visible_documentation_source(DOCS_ROOT / "user/guide/error-handling.md")

    assert "Edit the semantic `.pyi` and add `ORDER_C`" in arrays
    assert "Edit the declarations in `contracts/strings/strings_api.pyi`" in strings
    assert '@bind("scale")' in functions
    assert "## Shape the Module API With the Contract" in modules
    assert "nmax: Final[Int32] = 12" in modules
    assert "counter: Int32 = 9" in modules
    assert "scale: Float64 = 2.0" in modules
    assert "saved_counter: private[Int32]" in modules
    assert "It does not turn a writable Fortran variable into a read-only" in modules
    assert "## Flatten Module Namespaces" in modules
    assert "from .module1 import *" in modules
    assert "from .module2 import *" in modules
    assert "library.func1()" in modules
    assert "library.module1` and `library.module2` are no longer exported" in modules
    assert "the wrapper build fails and asks for an explicit" in modules
    assert "## Extend an Overload Set" in generics
    assert '@overload("convert_logical")' in generics
    assert "## Custom Constructor" in derived
    assert '@bind("initialize_point")' in derived
    assert "### Expose a Module Procedure as a Method" in derived
    assert "def move(self, dx: Float64, dy: Float64)" in derived
    assert '@raises(status="status", message="message", success=0)' in errors


def test_user_guide_keeps_generated_docstrings_with_new_overload_and_class_features() -> None:
    modules = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-modules.md")
    generics = _visible_documentation_source(DOCS_ROOT / "user/guide/generic-interfaces.md")
    derived = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-derived-types.md")

    assert "## Inspect the Module" not in modules
    assert "print(mod.__doc__)" not in modules

    assert "## Inspect the Overloads" in generics
    assert "print(conversions.__doc__)" in generics
    assert "print(conversions.convert.__doc__)" in generics
    assert "convert(value: int32) -> int32" in generics
    assert "convert(value: float64) -> float64" in generics

    assert "## Inspect the Class" in derived
    assert "print(points.point.__doc__)" in derived
    assert "print(points.point.__init__.__doc__)" in derived
    assert "`points.point.move.__doc__`" in derived
    assert "print(points.point.__add__.__doc__)" in derived
    assert "__add__(right: point) -> point" in derived


def test_getting_started_pages_keep_advanced_stage_flags_out_of_beginner_path() -> None:
    content = "\n".join(
        _visible_documentation_source(DOCS_ROOT / relative_path) for relative_path in REQUIRED_GETTING_STARTED_PAGES
    )

    assert "--parse" not in content
    assert "--semantics" not in content
    assert "--json" not in content


def test_user_guide_shows_direct_shared_library_build() -> None:
    content = "\n".join(
        _visible_documentation_source(DOCS_ROOT / relative_path) for relative_path in REQUIRED_USER_GUIDE_PAGES
    )

    assert "python3 -m x2py src/scale.f90 --out-dir build/scale" in content


def test_fortran_wrapper_reference_shows_every_common_shared_library_build_input() -> None:
    content = _visible_documentation_source(DOCS_ROOT / "user/reference/fortran-wrapper.md")
    example = content.split("For example, this command supplies every common build input", maxsplit=1)[1].split(
        "`--compiler` selects", maxsplit=1
    )[0]

    for value in (
        "python3 -m x2py solver.f90",
        "--out solver",
        "--out-dir build/solver",
        "--compiler gfortran",
        "-I include",
        "--native-compile-flags=-O3",
        "--native-library openblas",
        "--verbose",
    ):
        assert value in example


def test_array_handle_docs_keep_views_copies_and_handles_distinct() -> None:
    allocatables = _visible_documentation_source(DOCS_ROOT / "user/guide/allocatables.md")
    pointers = _visible_documentation_source(DOCS_ROOT / "user/guide/pointers.md")
    memory = _visible_documentation_source(DOCS_ROOT / "user/guide/memory-management.md")

    assert "Reading the Python attribute" in allocatables
    assert "returns an `Allocatable[T[...]]` handle, not `ndarray | None`." in allocatables
    assert "never creates an automatic detached snapshot" in allocatables
    assert "A NumPy view reflects current native storage." in allocatables
    assert "A pointer-array function result becomes a returned `PointerArray`." in pointers
    assert "has persistent descriptor storage, but the target can belong to another" in pointers
    assert "`associate(other)` makes two pointer handles refer to the same target" in pointers
    assert "If `p2` is unassociated, `p1` becomes" in pointers
    assert "Do Not Return A Pointer To Expired Local Storage" in pointers
    assert "Derived module variables remain live objects" in memory
    assert "Fortran module owns their storage" in memory


@pytest.mark.parametrize("heading", CLI_HELP_GROUP_HEADINGS)
def test_cli_help_uses_documented_option_groups(heading: str) -> None:
    assert heading in _x2py_cli_help()


@pytest.mark.parametrize("option", CLI_REFERENCE_OPTIONS)
def test_cli_reference_documents_public_option(option: str) -> None:
    content = CLI_REFERENCE_PATH.read_text(encoding="utf-8")
    assert option in content


@pytest.mark.parametrize("option", CLI_VISIBLE_HELP_OPTIONS)
def test_cli_help_exposes_documented_public_option(option: str) -> None:
    assert option in _x2py_cli_help()


@pytest.mark.parametrize("name", sorted(x2py.__all__))
def test_python_api_reference_documents_public_export(name: str) -> None:
    content = PYTHON_API_REFERENCE_PATH.read_text(encoding="utf-8")
    assert f"`{name}`" in content


@pytest.mark.parametrize("relative_path", REQUIRED_SOURCE_NAVIGATION_PAGES)
def test_required_source_navigation_page_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", REQUIRED_SOURCE_NAVIGATION_PAGES)
def test_source_navigation_page_is_in_site_navigation(relative_path: str) -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert relative_path in site_configuration


@pytest.mark.parametrize("relative_path", REQUIRED_EXAMPLE_RECIPE_PAGES)
def test_required_example_recipe_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", REQUIRED_EXAMPLE_RECIPE_PAGES)
def test_example_recipe_is_in_site_navigation(relative_path: str) -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert relative_path in site_configuration


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_HOTSPOTS)
def test_source_navigation_hotspot_exists(relative_path: str) -> None:
    assert (ROOT / relative_path).exists()


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_HOTSPOTS)
def test_source_navigation_mentions_hotspot(relative_path: str) -> None:
    assert relative_path in _combined_text(SOURCE_NAVIGATION_CORPUS)


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_PUBLIC_DOCS)
def test_source_navigation_public_doc_exists(relative_path: str) -> None:
    assert (ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_PUBLIC_DOCS)
def test_source_navigation_mentions_public_doc(relative_path: str) -> None:
    assert relative_path in _combined_text(SOURCE_NAVIGATION_CORPUS)


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_TEST_TARGETS)
def test_source_navigation_test_target_exists(relative_path: str) -> None:
    assert (ROOT / relative_path).exists()


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_TEST_TARGETS)
def test_source_navigation_mentions_test_target(relative_path: str) -> None:
    assert relative_path in _combined_text(SOURCE_NAVIGATION_CORPUS)


@pytest.mark.parametrize("relative_path", PACKAGE_READMES)
def test_package_readme_links_to_source_navigation(relative_path: str) -> None:
    content = (ROOT / relative_path).read_text(encoding="utf-8")
    for reference in PACKAGE_README_NAVIGATION_REFERENCES:
        assert reference in content


@pytest.mark.parametrize("relative_path", PACKAGE_READMES)
def test_package_readme_does_not_use_legacy_active_doc_paths(relative_path: str) -> None:
    content = (ROOT / relative_path).read_text(encoding="utf-8")
    for reference in LEGACY_ACTIVE_DOC_REFERENCES:
        assert reference not in content


def test_feature_matrix_has_rows_and_status_groups() -> None:
    assert FEATURE_MATRIX_ROWS
    statuses = {row["Status"] for row in FEATURE_MATRIX_ROWS}
    assert {"Supported", "Partially supported", "Unsupported", "Planned", "Not implemented"} <= statuses


@pytest.mark.parametrize("feature", FEATURE_MATRIX_REQUIRED_FEATURES)
def test_feature_matrix_includes_required_feature(feature: str) -> None:
    matrix_features = {row["Feature"] for row in FEATURE_MATRIX_ROWS}
    assert feature in matrix_features


@pytest.mark.parametrize("row", FEATURE_MATRIX_ROWS, ids=lambda row: row["Feature"])
def test_feature_matrix_row_is_complete(row: dict[str, str]) -> None:
    assert row["Status"] in FEATURE_MATRIX_STATUSES
    assert "TODO" not in " ".join(row.values())
    for column in ["Feature", "Status", "User docs", "Source owner", "Evidence", "Limitations"]:
        assert row[column]
    for column in ["User docs", "Source owner", "Evidence"]:
        assert MARKDOWN_LINK.search(row[column]), f"{row['Feature']}: {column} must contain a Markdown link"
    if row["Status"] in {"Supported", "Partially supported"}:
        evidence_targets = [
            (FEATURE_MATRIX_PATH.parent / target).resolve() for target in MARKDOWN_LINK.findall(row["Evidence"])
        ]
        assert any(target.is_relative_to(ROOT / "tests") for target in evidence_targets), (
            f"{row['Feature']}: support claims need direct test evidence"
        )


@pytest.mark.parametrize("row", FEATURE_MATRIX_ROWS, ids=lambda row: row["Feature"])
def test_feature_matrix_links_point_to_existing_files(row: dict[str, str]) -> None:
    for column in ["User docs", "Source owner", "Evidence"]:
        for target in MARKDOWN_LINK.findall(row[column]):
            if target.startswith(("http://", "https://")):
                continue
            resolved_target = (FEATURE_MATRIX_PATH.parent / target).resolve()
            assert resolved_target.exists(), f"{row['Feature']}: {column} link target does not exist: {target}"


@pytest.mark.parametrize("package", MAJOR_SOURCE_PACKAGES)
def test_source_map_covers_major_source_packages(package: str) -> None:
    source_map = (DOCS_ROOT / "developer/source-map.md").read_text(encoding="utf-8")
    assert package in source_map


@pytest.mark.parametrize("relative_path", PACKAGE_READMES)
def test_major_source_package_has_local_readme(relative_path: str) -> None:
    assert (ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", ARCHIVED_OLD_DOCS)
def test_old_documentation_is_archived(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", OLD_TOP_LEVEL_DOCS)
def test_old_top_level_documentation_was_moved(relative_path: str) -> None:
    assert not (DOCS_ROOT / relative_path).exists()


def test_static_site_seed_configuration_exists() -> None:
    assert (ROOT / "mkdocs.yml").is_file()


def test_site_theme_keeps_sidebar_open_and_code_blocks_copyable() -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "name: readthedocs" in site_configuration
    assert "collapse_navigation: false" in site_configuration
    assert "navigation_depth: 4" in site_configuration
    assert "stylesheets/site.css" in site_configuration
    assert "stylesheets/code-copy.css" in site_configuration
    assert "javascripts/code-copy.js" in site_configuration

    script = (DOCS_ROOT / "javascripts" / "code-copy.js").read_text(encoding="utf-8")
    layout_stylesheet = (DOCS_ROOT / "stylesheets" / "site.css").read_text(encoding="utf-8")
    stylesheet = (DOCS_ROOT / "stylesheets" / "code-copy.css").read_text(encoding="utf-8")
    assert ".wy-nav-content" in layout_stylesheet
    assert "max-width: 1200px" in layout_stylesheet
    assert "margin: 0" in layout_stylesheet
    assert ".wy-nav-side" in layout_stylesheet
    assert "padding-bottom: 0" in layout_stylesheet
    assert ".wy-side-scroll" in layout_stylesheet
    assert "overflow-y: auto" in layout_stylesheet
    assert "scrollbar-width: thin" in layout_stylesheet
    assert ".wy-side-scroll::-webkit-scrollbar-thumb" in layout_stylesheet
    assert ".rst-versions" in layout_stylesheet
    assert "display: none" in layout_stylesheet
    assert ".rst-content pre" in layout_stylesheet
    assert "width: 100%" in layout_stylesheet
    assert "max-width: 56rem" in layout_stylesheet
    assert "padding-right: 3.25rem" in layout_stylesheet
    assert 'document.querySelectorAll("pre code")' in script
    assert "navigator.clipboard.writeText" in script
    assert 'button.setAttribute("aria-label", "Copy code to clipboard")' in script
    assert ".x2py-code-copy" in stylesheet
