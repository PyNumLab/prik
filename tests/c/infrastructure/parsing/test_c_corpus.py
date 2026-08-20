"""Active cJSON parser regression tests.

cJSON is the first target corpus because it is small, realistic, and exercises
headers, typedef structs, recursive pointers, function declarations, macros,
constants, and callback hook fields without requiring a large build system.
"""

import shutil

import pytest
from tests.c._support.paths import C_DATA_DIR

_CJSON_DIR = C_DATA_DIR / "json"


def _preprocessed_cjson_source(filename: str) -> str:
    from prik.preprocessing import PreprocessingConfig, preprocess_source

    compiler = shutil.which("cc")
    if compiler is None:
        pytest.skip("cc is not available")
    return preprocess_source(
        _CJSON_DIR / filename,
        language="c",
        config=PreprocessingConfig(mode="compiler", compiler=compiler),
    ).source


def test_cjson_regression_source_and_header_are_available():
    assert (_CJSON_DIR / "cJSON.h").exists()
    assert (_CJSON_DIR / "cJSON.c").exists()


def test_cjson_header_raw_parse_requires_preprocessing():
    import pytest

    from prik.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="require compiler preprocessing") as exc_info:
        parse_c_file(_CJSON_DIR / "cJSON.h")
    assert exc_info.value.code == "CPARSE_PREPROCESSING_REQUIRED"


def test_cjson_header_preprocessed_mode_has_no_error_diagnostics():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        _preprocessed_cjson_source("cJSON.h"),
        filename=str(_CJSON_DIR / "cJSON.h"),
        preprocessing="compiler",
    )

    assert not any(diag.severity == "error" for diag in parsed.diagnostics)


def test_cjson_callback_hook_declarations_are_preprocessed_without_error_diagnostics():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        _preprocessed_cjson_source("cJSON.h"),
        filename=str(_CJSON_DIR / "cJSON.h"),
        preprocessing="compiler",
    )

    assert any(struct.name == "cJSON_Hooks" for struct in parsed.structs)
    assert not any(diag.severity == "error" for diag in parsed.diagnostics)


def test_cjson_source_file_parse_skips_function_bodies_safely():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        _preprocessed_cjson_source("cJSON.c"),
        filename=str(_CJSON_DIR / "cJSON.c"),
        preprocessing="compiler",
    )

    assert any(fn.name == "parse_number" for fn in parsed.functions)
    assert not any(hasattr(fn, "body") for fn in parsed.functions)


def test_cjson_project_parse_links_header_and_source():
    from prik.parsers.c import parse_c_project

    sources = {filename: _preprocessed_cjson_source(filename) for filename in ("cJSON.h", "cJSON.c")}
    project = parse_c_project(sources, preprocessing="compiler")

    assert "cJSON.h" in project.files
    assert "cJSON.c" in project.files
    assert project.header_source_pairs["cJSON.h"] == {"cJSON.c"}
