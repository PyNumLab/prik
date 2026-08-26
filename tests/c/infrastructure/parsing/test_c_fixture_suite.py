"""C parser grouped-project fixture regression tests."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
from tests.c._support.paths import C_ROOT

_C_ROOT = C_ROOT
_DATA_DIR = _C_ROOT / "fixtures" / "native"
_SOURCE_SUFFIXES = {".c", ".h", ".i"}
_SOURCE_ORDER = {".c": 0, ".h": 1, ".i": 2}
_FIXTURE_GROUPS = ("general", "json", "tinyexpr", "linmath", "nanosvg", "stb")
_PROJECT_OVERRIDES = {
    "nanosvg": {
        "nanosvg": ("nanosvg.h", "nanosvgrast.h"),
    },
}


def _load_golden_generator():
    module_path = _C_ROOT / "fixtures" / "parser" / "generate_c_parser_goldens.py"
    spec = importlib.util.spec_from_file_location("generate_c_parser_goldens", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load C golden generator from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture_sort_key(fixture: Path) -> tuple[int, str]:
    return (_SOURCE_ORDER.get(fixture.suffix.lower(), 99), fixture.as_posix())


def _project_key(fixture: Path, root: Path) -> Path:
    relative = fixture.relative_to(root)
    for project_name, filenames in _PROJECT_OVERRIDES.get(root.name, {}).items():
        if relative.name in filenames:
            return Path(project_name)
    return relative.with_suffix("")


def _project_groups(root: Path) -> list[tuple[Path, list[Path]]]:
    grouped: dict[Path, list[Path]] = {}
    for fixture in sorted(root.rglob("*"), key=_fixture_sort_key):
        if fixture.is_file() and fixture.suffix.lower() in _SOURCE_SUFFIXES:
            grouped.setdefault(_project_key(fixture, root), []).append(fixture)
    projects = []
    for project_key, fixtures in sorted(grouped.items()):
        override = _PROJECT_OVERRIDES.get(root.name, {}).get(project_key.name)
        if override is not None:
            order = {filename: index for index, filename in enumerate(override)}
            fixtures = sorted(fixtures, key=lambda fixture: order[fixture.name])
        else:
            fixtures = sorted(fixtures, key=_fixture_sort_key)
        projects.append((project_key, fixtures))
    return projects


@pytest.mark.parametrize("data_subdir", _FIXTURE_GROUPS)
def test_c_fixture_suite_has_inputs(data_subdir):
    fixtures = sorted((_DATA_DIR / data_subdir).glob("*"))
    assert any(path.suffix.lower() in _SOURCE_SUFFIXES for path in fixtures)


@pytest.mark.parametrize(
    "fixture",
    [
        _DATA_DIR / "json" / "cJSON.h",
        _DATA_DIR / "tinyexpr" / "tinyexpr.h",
        _DATA_DIR / "linmath" / "linmath.h",
        _DATA_DIR / "nanosvg" / "nanosvg.h",
        _DATA_DIR / "stb" / "stb_c_lexer.h",
    ],
)
def test_c_fixture_headers_with_macros_require_preprocessing(fixture):
    from prik.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="require compiler preprocessing") as exc_info:
        parse_c_file(fixture)

    assert exc_info.value.code == "CPARSE_PREPROCESSING_REQUIRED"


@pytest.mark.parametrize(
    ("fixture", "defines"),
    [
        (_DATA_DIR / "json" / "jsmn.h", []),
        (_DATA_DIR / "tinyexpr" / "tinyexpr.c", []),
        (_DATA_DIR / "linmath" / "linmath.h", []),
        (_DATA_DIR / "nanosvg" / "nanosvg.h", ["NANOSVG_IMPLEMENTATION"]),
        (_DATA_DIR / "nanosvg" / "nanosvgrast.h", ["NANOSVGRAST_IMPLEMENTATION"]),
        (_DATA_DIR / "stb" / "stb_ds.h", ["STB_DS_IMPLEMENTATION"]),
        (_DATA_DIR / "stb" / "stb_dxt.h", ["STB_DXT_IMPLEMENTATION"]),
        (_DATA_DIR / "stb" / "stb_image.h", ["STB_IMAGE_IMPLEMENTATION"]),
        (_DATA_DIR / "stb" / "stb_rect_pack.h", ["STB_RECT_PACK_IMPLEMENTATION"]),
    ],
)
def test_c_fixture_headers_parse_after_compiler_preprocessing(fixture, defines):
    from prik.parsers.c import parse_c_file
    from prik.preprocessing import PreprocessingConfig, preprocess_source

    compiler = shutil.which("cc")
    if compiler is None:
        pytest.skip("cc is not available")
    preprocessed = preprocess_source(
        fixture,
        language="c",
        config=PreprocessingConfig(
            mode="compiler",
            compiler=compiler,
            include_dirs=[str(fixture.parent)],
            defines=defines,
        ),
    )

    parsed = parse_c_file(
        preprocessed.source,
        filename=str(fixture),
        preprocessing="compiler",
    )

    assert parsed.preprocessing == "compiler"
    assert parsed.functions


def test_c_fixture_suite_keeps_source_locations_stable_for_plain_source():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        _DATA_DIR / "general" / "basic_array_update.c",
    )
    function = parsed.functions[0]

    assert function.source_location.filename == str(_DATA_DIR / "general" / "basic_array_update.c")
    assert function.source_location.line >= 1
    assert function.source_location.column >= 1


def test_c_fixture_suite_groups_matching_source_and_header_source_first():
    projects = dict(_project_groups(_DATA_DIR / "json"))
    fixtures = projects[Path("cJSON")]

    assert [fixture.name for fixture in fixtures] == ["cJSON.c", "cJSON.h"]


def test_c_fixture_suite_groups_dependent_headers_dependency_first():
    projects = dict(_project_groups(_DATA_DIR / "nanosvg"))
    fixtures = projects[Path("nanosvg")]

    assert [fixture.name for fixture in fixtures] == ["nanosvg.h", "nanosvgrast.h"]


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="C project goldens use the Linux compiler-preprocessing reference environment",
)
def test_c_project_goldens_match_generated_payloads():
    if shutil.which("cc") is None:
        pytest.skip("cc is not available")

    generator = _load_golden_generator()
    for project_key, fixtures in generator._default_projects():
        expected_path = generator._output_path_for_project(project_key)
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        generated = generator._serialize_project(fixtures)

        assert generator._stable_project_payload(generated) == generator._stable_project_payload(expected), (
            f"C parser golden is stale: {expected_path}"
        )
