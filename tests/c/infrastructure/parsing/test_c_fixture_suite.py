"""C parser grouped-project golden regression test.

The goldens are the compiler-preprocessed Linux reference payloads for every
grouped fixture project (general, json, tinyexpr, linmath, nanosvg, stb). One
exact comparison proves the parse, project assembly, include graph, and JSON
shape for real-world headers; see ``tests/c/fixtures/parser/README.md``.
"""

import importlib.util
import json
import shutil
import sys

import pytest
from tests.c._support.paths import C_ROOT


def _load_golden_generator():
    module_path = C_ROOT / "fixtures" / "parser" / "generate_c_parser_goldens.py"
    spec = importlib.util.spec_from_file_location("generate_c_parser_goldens", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load C golden generator from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
