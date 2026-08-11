"""Shared facts and parsers for documentation contract tests."""

from __future__ import annotations

from functools import cache
from pathlib import Path
import re
import subprocess
import sys


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
C_DOCS_START = "<!-- PRIK_C_DOCS_START"
C_DOCS_END = "PRIK_C_DOCS_END -->"
C_DOCS_DISABLED = "<!-- PRIK_C_DOCS_DISABLED:"
VISIBLE_C_DOCUMENTATION_EXCEPTIONS = {
    "README.md": ("Fortran and C compilers",),
    "docs/user/about.md": ("C-to-Python interoperability", "C++"),
    "docs/user/getting-started/index.md": ("`gcc`",),
    "docs/user/getting-started/installation.md": (
        "matching C\ncompiler",
        "C compiler",
        "brew install gcc@13",
        "`gcc`",
        "`gcc-13`",
        "`clang`",
    ),
    "docs/user/getting-started/verification.md": ("gcc --version", "clang --version"),
    "docs/user/troubleshooting/compiler-issues.md": (
        "C binding",
        "C compiler",
        "matching C\ncompiler",
        "gcc --version",
        "`clang`",
    ),
    "docs/user/reference/cli-commands.md": ("C INCLUDE OPTIONS", "{fortran,c}"),
    "docs/user/guide/enumerations.md": ("bind(C)",),
    "docs/user/guide/wrapping-derived-types.md": ("bind(C)",),
    "docs/user/guide/arrays.md": ("ORDER_C", "C-contiguous", "C-order", "C-oriented", 'order="C"'),
    "docs/user/guide/raw-addresses.md": ("C-order", "C ordering"),
    "docs/user/guide/building-shared-library.md": (
        "PRIK_CFLAGS",
        "C binding",
        "C compiler",
        "`gcc`",
        "`clang`",
    ),
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
    r"|(?:tests/c/fixtures/native|tests/c/fixtures/parser|prik/parsers/c|/c/general/)"
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
    "--version",
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
    "--jobs",
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
    "prik/README.md",
    "prik/parsers/README.md",
    "prik/parsers/c/README.md",
    "prik/parsers/fortran/README.md",
    "prik/parsers/pyi/README.md",
    "prik/semantics/README.md",
    "prik/compiling/README.md",
]
SOURCE_NAVIGATION_HOTSPOTS = [
    "prik/__init__.py",
    "prik/cli.py",
    "prik/pipeline/build.py",
    "prik/pipeline/preprocessing.py",
    "prik/probes/c_types.py",
    "prik/probes/fortran_types.py",
    "prik/semantics/ownership.py",
    "prik/parsers/c/parser.py",
    "prik/parsers/c/cli.py",
    "prik/parsers/fortran/parser.py",
    "prik/parsers/fortran/cli.py",
    "prik/parsers/pyi/parser.py",
    "prik/semantics/models.py",
    "prik/semantics/fortran2ir.py",
    "prik/semantics/c2ir.py",
    "prik/semantics/pyi2ir.py",
    "prik/pipeline/pyi.py",
    "prik/semantics/policy_completion.py",
    "prik/codegen/plan.py",
    "prik/codegen/planner.py",
    "prik/codegen/generator.py",
    "prik/codegen/c/binding.py",
    "prik/codegen/fortran/bridge.py",
    "prik/codegen/printers/pyi_printer.py",
    "prik/codegen/printers/source_printers.py",
    "prik/compiling/objects.py",
    "prik/compiling/compilers.py",
    "prik/compiling/native_support.py",
    "prik/naming/policy.py",
    "prik/binding_support/",
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
    "tests/c/fixtures/parser/",
    "tests/fortran/command_line_interface/pipeline/",
    "tests/fortran/source_parsing/parsing/",
    "tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py",
    "tests/fortran/source_parsing/parsing/test_public_entrypoints.py",
    "tests/fortran/source_preprocessing/preprocessing/",
    "tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py",
    "tests/fortran/semantic_pyi_format/",
    "tests/fortran/semantic_pyi_format/parsing/",
    "tests/fortran/semantic_pyi_format/semantics/",
    "tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py",
    "tests/fortran/semantic_pyi_format/pipeline/test_contract_loading.py",
    "tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py",
    "tests/fortran/semantic_ir/semantics/",
    "tests/c/semantics/conversion/",
    "tests/fortran/semantic_pyi_format/pipeline/",
    "tests/fortran/semantic_pyi_format/pipeline/test_modern_example.py",
    "tests/docs/test_examples.py",
    "tests/docs/test_reference_and_source_map.py",
    "tests/fortran/",
    "tests/fortran/pyi_contracts/exports_and_modules/",
    "tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py",
    "tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py",
    "tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py",
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
    "Unproved pointer lifetime and ownership-changing operations",
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
REAL_LIBRARY_EXAMPLE_PAGES = [
    "user/examples/blas-wrapper.md",
    "user/examples/lapack-wrapper.md",
    "user/examples/fftpack-wrapper.md",
    "user/examples/minpack-wrapper.md",
]
MAJOR_SOURCE_PACKAGES = [
    "prik/parsers/",
    "prik/semantics/",
    "prik/codegen/",
    "prik/compiling/",
]
PACKAGE_READMES = [
    "prik/README.md",
    "prik/parsers/README.md",
    "prik/semantics/README.md",
    "prik/compiling/README.md",
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
def _prik_cli_help() -> str:
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
            [sys.executable, "-m", "prik", *command],
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
