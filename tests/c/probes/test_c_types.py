"""Compiler-derived C standard-library type fact tests."""

import json
import os
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

import x2py.probes.c_types as c_type_probe
from x2py.probes.c_types import (
    CStandardTypeProbeRecipe,
    CStandardTypeProbeReport,
    CStandardTypeProbeError,
    _semantic_type_facts,
    build_c_standard_type_probe_source,
    c_standard_type_probe_cache_key,
    load_c_standard_type_probe_report,
    probe_c_standard_types_cached,
    probe_c_standard_types,
)
from x2py.pipeline.preprocessing import PreprocessingConfig


_CC = shutil.which("cc")


def _required_c_compiler() -> str:
    assert _CC is not None, "the full C pipeline test suite requires an available native C compiler"
    return _CC


def test_c_standard_type_probe_source_queries_standard_headers_without_layout_claims():
    source = build_c_standard_type_probe_source()

    assert "#include <complex.h>" in source
    assert "#include <float.h>" in source
    assert "#include <stddef.h>" in source
    assert "#include <stdint.h>" in source
    assert "#include <time.h>" in source
    assert "#include <stdio.h>" in source
    assert 'X2PY_PRINT_ARITHMETIC("_Bool"' in source
    assert "X2PY_PRINT_CHAR()" in source
    assert 'X2PY_PRINT_ARITHMETIC("unsigned long"' in source
    assert 'X2PY_PRINT_REAL("long double"' in source
    assert 'X2PY_PRINT_ARITHMETIC("long double _Complex"' in source
    assert 'X2PY_PRINT_ARITHMETIC("int"' in source
    assert 'X2PY_PRINT_ARITHMETIC("size_t"' in source
    assert 'X2PY_PRINT_ARITHMETIC("uint32_t"' in source
    assert 'X2PY_PRINT_ARITHMETIC("time_t"' in source
    assert "sizeof(FILE *)" in source
    assert "sizeof(FILE)" not in source


def test_c_standard_type_probe_requires_an_explicit_compiler():
    with pytest.raises(CStandardTypeProbeError, match="exact compiler"):
        probe_c_standard_types(PreprocessingConfig(mode="compiler"))


def test_c_standard_type_probe_rejects_compile_database_and_classifies_all_arithmetic_categories():
    compile_database = PreprocessingConfig(mode="compiler", compiler="cc", compile_commands="compile_commands.json")
    with pytest.raises(CStandardTypeProbeError, match="does not consume compile_commands"):
        probe_c_standard_types(compile_database)
    with pytest.raises(CStandardTypeProbeError, match="does not consume compile_commands"):
        probe_c_standard_types_cached(compile_database)
    with pytest.raises(CStandardTypeProbeError, match="does not consume custom preprocessing templates"):
        probe_c_standard_types(
            PreprocessingConfig(mode="compiler", compiler="cc", command_template="{compiler} {source}")
        )

    types = {
        "real": {"available": True, "kind": "arithmetic", "underlying_c_type": "double"},
        "char": {"available": True, "kind": "arithmetic", "underlying_c_type": "char"},
        "other": {"available": True, "kind": "arithmetic", "underlying_c_type": "other"},
        "unavailable": {"available": False, "kind": "arithmetic", "underlying_c_type": "double"},
    }
    _semantic_type_facts(types)

    assert types["real"]["semantic_category"] == "real"
    assert types["char"]["semantic_category"] == "integer_implementation_signedness"
    assert types["other"]["semantic_category"] == "implementation_defined"
    assert "semantic_category" not in types["unavailable"]


@pytest.mark.parametrize(
    ("results", "message"),
    [
        ([OSError("missing")], "failed to run C type probe compiler"),
        ([SimpleNamespace(returncode=1, stderr="compile failed")], "compilation failed"),
        ([SimpleNamespace(returncode=0, stderr=""), OSError("cannot execute")], "failed to execute"),
        (
            [SimpleNamespace(returncode=0, stderr=""), SimpleNamespace(returncode=2, stderr="run failed")],
            "execution failed",
        ),
        (
            [SimpleNamespace(returncode=0, stderr=""), SimpleNamespace(returncode=0, stdout="not json", stderr="")],
            "invalid JSON",
        ),
        (
            [SimpleNamespace(returncode=0, stderr=""), SimpleNamespace(returncode=0, stdout="{}", stderr="")],
            "missing 'types'",
        ),
    ],
)
def test_c_standard_type_probe_reports_compiler_and_runner_failures(monkeypatch, results, message):
    responses = iter(results)

    def run(*_args, **_kwargs):
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(c_type_probe.subprocess, "run", run)
    with pytest.raises(CStandardTypeProbeError, match=message):
        probe_c_standard_types(PreprocessingConfig(mode="compiler", compiler="cc"), runner=["runner"])


def test_c_standard_type_probe_accepts_explicit_runner_and_cli_validates_macros(monkeypatch):
    responses = iter(
        [
            SimpleNamespace(returncode=0, stderr=""),
            SimpleNamespace(returncode=0, stdout='{"types": {}}', stderr=""),
        ]
    )
    monkeypatch.setattr(c_type_probe.subprocess, "run", lambda *_args, **_kwargs: next(responses))

    report = probe_c_standard_types(PreprocessingConfig(mode="compiler", compiler="cc"), runner=["emulator"])
    assert report.recipe.run_argv[0] == "emulator"

    with pytest.raises(SystemExit):
        c_type_probe.main(["--compiler", "cc", "-D", "=bad"])
    with pytest.raises(SystemExit):
        c_type_probe.main(["--compiler", "cc", "-U", "=bad"])


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "must contain a JSON object"),
        ({}, "missing valid 'types'"),
        ({"types": {}, "recipe": {}, "source_text": "probe"}, "missing a valid 'recipe'"),
        ({"types": {}, "recipe": {"compiler": "cc"}}, "missing valid 'source_text'"),
    ],
)
def test_c_standard_type_probe_report_loader_validates_reusable_reports(tmp_path, payload, message):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CStandardTypeProbeError, match=message):
        load_c_standard_type_probe_report(report_path)


def test_c_standard_type_probe_report_loader_reports_read_and_json_errors(tmp_path):
    with pytest.raises(CStandardTypeProbeError, match="failed to read"):
        load_c_standard_type_probe_report(tmp_path / "missing.json")

    report_path = tmp_path / "invalid.json"
    report_path.write_text("not json", encoding="utf-8")
    with pytest.raises(CStandardTypeProbeError, match="contains invalid JSON"):
        load_c_standard_type_probe_report(report_path)


def test_c_standard_type_probe_reports_semantic_facts_from_native_compiler():
    compiler = _required_c_compiler()
    report = probe_c_standard_types(PreprocessingConfig(mode="compiler", compiler=compiler, std="c11"))

    c_int = report.types["int"]
    assert c_int["available"] is True
    assert c_int["kind"] == "integer"
    assert c_int["signed"] is True
    assert c_int["underlying_c_type"] == "int"
    assert c_int["bits"] >= 16

    plain_char = report.types["char"]
    assert plain_char["kind"] == "integer"
    assert isinstance(plain_char["signed"], bool)

    c_long = report.types["long"]
    assert c_long["kind"] == "integer"
    assert c_long["signed"] is True
    assert c_long["bits"] >= c_int["bits"]

    long_double = report.types["long double"]
    assert long_double["kind"] == "real"
    assert long_double["precision_bits"] > 0

    long_double_complex = report.types["long double _Complex"]
    assert long_double_complex["kind"] == "complex"
    assert long_double_complex["bits"] >= long_double["bits"]

    size_t = report.types["size_t"]
    assert size_t["available"] is True
    assert size_t["kind"] == "integer"
    assert size_t["signed"] is False
    assert size_t["semantic_category"] == "unsigned_integer"
    assert size_t["bits"] > 0

    uint32_t = report.types["uint32_t"]
    if uint32_t["available"]:
        assert uint32_t["kind"] == "integer"
        assert uint32_t["signed"] is False
        assert uint32_t["bits"] == 32

    time_t = report.types["time_t"]
    assert time_t["available"] is True
    assert time_t["semantic_category"] in {
        "signed_integer",
        "unsigned_integer",
        "real",
        "integer_implementation_signedness",
        "implementation_defined",
    }

    file_type = report.types["FILE"]
    assert file_type["kind"] == "opaque_handle"
    assert file_type["pointer_bits"] > 0
    assert report.recipe.compiler == compiler
    assert "-std=c11" in report.recipe.compile_argv
    assert "#include <time.h>" in report.source_text


def test_c_standard_type_probe_carries_target_relevant_user_flags(tmp_path):
    compiler = _required_c_compiler()
    include_dir = tmp_path / "include"
    include_dir.mkdir()

    report = probe_c_standard_types(
        PreprocessingConfig(
            mode="compiler",
            compiler=compiler,
            include_dirs=[str(include_dir)],
            defines=["X2PY_FEATURE=1"],
            undefs=["X2PY_OLD_FEATURE"],
            std="c99",
            compiler_args=["-funsigned-char"],
        )
    )

    argv = report.recipe.compile_argv
    assert f"-I{include_dir}" in argv
    assert "-DX2PY_FEATURE=1" in argv
    assert "-UX2PY_OLD_FEATURE" in argv
    assert "-std=c11" in argv
    assert "-funsigned-char" in argv
    assert report.recipe.requested_standard == "c99"
    assert report.recipe.include_dirs == [str(include_dir)]
    assert report.recipe.defines == ["X2PY_FEATURE=1"]
    assert report.recipe.undefs == ["X2PY_OLD_FEATURE"]
    assert report.recipe.compiler_args == ["-funsigned-char"]
    assert report.types["char"]["signed"] is False


def test_c_standard_type_probe_cache_reuses_report_and_invalidates_for_flags(monkeypatch, tmp_path):
    c_type_probe._MEMORY_CACHE.clear()
    calls = []
    compiler = tmp_path / "fake-cc"
    compiler.write_text("first compiler identity", encoding="utf-8")
    report = CStandardTypeProbeReport(
        types={"int": {"available": True, "kind": "integer", "signed": True, "bits": 32}},
        recipe=CStandardTypeProbeRecipe(compiler=str(compiler), compile_argv=[str(compiler)], run_argv=["probe"]),
        source_text=build_c_standard_type_probe_source(),
    )

    def probe(config, *, runner=None):
        calls.append((config, runner))
        return report

    monkeypatch.setattr(c_type_probe, "probe_c_standard_types", probe)
    config = PreprocessingConfig(mode="compiler", compiler=str(compiler), compiler_args=["-m64"])

    first = probe_c_standard_types_cached(config, cache_dir=tmp_path)
    second = probe_c_standard_types_cached(config, cache_dir=tmp_path)
    assert first is second
    assert len(calls) == 1

    c_type_probe._MEMORY_CACHE.clear()
    loaded = probe_c_standard_types_cached(config, cache_dir=tmp_path)
    assert loaded.types == report.types
    assert len(calls) == 1

    probe_c_standard_types_cached(config, cache_dir=tmp_path, refresh=True)
    assert len(calls) == 2

    changed = PreprocessingConfig(mode="compiler", compiler=str(compiler), compiler_args=["-m32"])
    assert c_standard_type_probe_cache_key(changed) != c_standard_type_probe_cache_key(config)
    assert c_standard_type_probe_cache_key(config, runner=["runner"]) != c_standard_type_probe_cache_key(config)
    probe_c_standard_types_cached(changed, cache_dir=tmp_path)
    assert len(calls) == 3

    original_key = c_standard_type_probe_cache_key(config)
    original_cpath = os.environ.get("CPATH")
    monkeypatch.setenv("CPATH", "target/include")
    assert c_standard_type_probe_cache_key(config) != original_key
    if original_cpath is None:
        monkeypatch.delenv("CPATH")
    else:
        monkeypatch.setenv("CPATH", original_cpath)
    compiler.write_text("changed compiler identity and size", encoding="utf-8")
    assert c_standard_type_probe_cache_key(config) != original_key


def test_c_standard_type_probe_cache_directory_precedence(monkeypatch, tmp_path):
    explicit = tmp_path / "explicit"
    assert c_type_probe._probe_cache_dir(explicit) == explicit

    monkeypatch.setenv("X2PY_CACHE_DIR", str(tmp_path / "x2py"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert c_type_probe._probe_cache_dir(None) == tmp_path / "x2py" / "c_type_probe"

    monkeypatch.delenv("X2PY_CACHE_DIR")
    assert c_type_probe._probe_cache_dir(None) == tmp_path / "xdg" / "x2py" / "c_type_probe"


def test_c_standard_type_probe_module_cli_emits_json_for_semantic_input():
    compiler = _required_c_compiler()
    completed = subprocess.run(
        [sys.executable, "-m", "x2py.probes.c_types", "--compiler", compiler],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["types"]["size_t"]["semantic_category"] == "unsigned_integer"
    assert payload["types"]["FILE"]["kind"] == "opaque_handle"
    assert payload["recipe"]["compiler"] == compiler
    assert payload["source_text"].startswith("#include <complex.h>")
