"""JSON schema sanity tests for legacy C parser project snapshots."""

import json
from pathlib import Path

_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "parser" / "fixtures"
_PARSER_FIXTURE_GROUPS = ("general", "json", "tinyexpr", "linmath", "nanosvg", "stb")


def _iter_project_payloads():
    for group in _PARSER_FIXTURE_GROUPS:
        for path in (_FIXTURES_DIR / group).rglob("*.json"):
            yield path, json.loads(path.read_text(encoding="utf-8"))


def _iter_file_payloads():
    for path, project in _iter_project_payloads():
        for filename, payload in project["files"].items():
            yield path, filename, payload


def test_c_json_fixtures_are_valid_json():
    for path in _FIXTURES_DIR.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_c_json_project_fixtures_have_stable_top_level_shape():
    required_keys = {
        "files",
        "functions",
        "structs",
        "unions",
        "enums",
        "typedefs",
        "variables",
        "macros",
        "includes",
        "functions_by_file",
        "enum_constants",
        "include_graph",
        "system_includes",
        "unresolved_includes",
        "header_source_pairs",
        "diagnostics",
    }

    for path, payload in _iter_project_payloads():
        assert required_keys <= set(payload), f"missing project keys in {path}"


def test_c_json_project_files_have_stable_c_file_shape():
    required_keys = {
        "language",
        "filename",
        "functions",
        "structs",
        "unions",
        "enums",
        "typedefs",
        "variables",
        "macros",
        "includes",
        "diagnostics",
    }

    for path, _, payload in _iter_file_payloads():
        assert required_keys <= set(payload), f"missing file keys in {path}"
        assert payload["language"] == "c"


def test_c_json_functions_have_names_types_and_source_locations():
    for path, _, payload in _iter_file_payloads():
        for fn in payload.get("functions", []):
            assert fn["name"], f"function without name in {path}"
            assert fn["result_type"], f"function without result type in {path}"
            assert isinstance(fn["parameters"], list)
            assert fn["source_location"]["line"] >= 1
            assert fn["source_location"]["column"] >= 1


def test_c_json_types_have_distinct_names_or_anonymous_ids():
    for path, _, payload in _iter_file_payloads():
        for key in ("structs", "unions", "enums"):
            for entry in payload.get(key, []):
                assert entry.get("name") or entry.get("anonymous_id") or entry.get("reference"), (
                    f"anonymous {key} missing id in {path}"
                )


def test_c_json_diagnostics_have_codes_locations_and_severities():
    allowed = {"info", "warning", "error"}

    for _path, payload in _iter_project_payloads():
        for diagnostic in payload.get("diagnostics", []):
            assert diagnostic["code"]
            assert diagnostic["severity"] in allowed
            assert diagnostic.get("message")
            if diagnostic.get("location"):
                assert diagnostic["location"]["line"] >= 1
