"""Tests split by stable ownership concept from `test_cli.py`."""

from tests.c._support.preprocessing import (
    Path,
    PreprocessingConfig,
    PreprocessingError,
    preprocessing,
    pytest,
    subprocess,
    sys,
)


def test_preprocess_source_c_error_paths(monkeypatch, tmp_path: Path):
    c_source = tmp_path / "api.c"
    c_source.write_text("int api(void);\n", encoding="utf-8")

    with pytest.raises(PreprocessingError, match="not configured") as exc_info:
        preprocessing.preprocess_source(c_source, language="c", config=PreprocessingConfig())
    assert str(exc_info.value) == "Compiler preprocessing not configured"
    assert exc_info.value.category == "INVALID_COMPILER_ARGUMENTS"
    assert exc_info.value.diagnostics == []

    missing_name = "x2py-definitely-missing-preprocessor"
    with pytest.raises(PreprocessingError, match="preprocessor not found") as exc_info:
        preprocessing.preprocess_source(
            c_source,
            language="c",
            config=PreprocessingConfig(mode="compiler", compiler=missing_name),
        )
    assert exc_info.value.category == "PREPROCESSOR_NOT_FOUND"
    assert [diagnostic.to_dict() for diagnostic in exc_info.value.diagnostics] == [
        {
            "category": "PREPROCESSOR_NOT_FOUND",
            "message": f"preprocessor not found: {missing_name}",
            "severity": "error",
            "path": None,
            "line": None,
            "command": [missing_name, "-E", "-x", "c", str(c_source)],
        }
    ]

    def raise_file_not_found(*_args, **_kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(preprocessing.subprocess, "run", raise_file_not_found)
    missing_path = str(tmp_path / "missing-cc")
    with pytest.raises(PreprocessingError, match="preprocessor not found") as exc_info:
        preprocessing.preprocess_source(
            c_source,
            language="c",
            config=PreprocessingConfig(mode="compiler", compiler=missing_path),
        )
    assert str(exc_info.value) == f"preprocessor not found: {missing_path}"
    assert exc_info.value.category == "PREPROCESSOR_NOT_FOUND"
    assert [diagnostic.to_dict() for diagnostic in exc_info.value.diagnostics] == [
        {
            "category": "PREPROCESSOR_NOT_FOUND",
            "message": f"preprocessor not found: {missing_path}",
            "severity": "error",
            "path": None,
            "line": None,
            "command": [missing_path, "-E", "-x", "c", str(c_source)],
        }
    ]

    def raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="cc", timeout=60)

    monkeypatch.setattr(preprocessing.subprocess, "run", raise_timeout)
    slow_path = str(tmp_path / "slow-cc")
    with pytest.raises(PreprocessingError, match="timed out") as exc_info:
        preprocessing.preprocess_source(
            c_source,
            language="c",
            config=PreprocessingConfig(mode="compiler", compiler=slow_path),
        )
    assert str(exc_info.value) == "compiler preprocessing failed: timed out after 60 seconds"
    assert exc_info.value.category == "PREPROCESSOR_FAILED"
    assert [diagnostic.to_dict() for diagnostic in exc_info.value.diagnostics] == [
        {
            "category": "PREPROCESSOR_FAILED",
            "message": "compiler preprocessing timed out after 60 seconds",
            "severity": "error",
            "path": None,
            "line": None,
            "command": [slow_path, "-E", "-x", "c", str(c_source)],
        }
    ]

    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type("Done", (), {"returncode": 2, "stdout": "", "stderr": ""})(),
    )
    bad_path = str(tmp_path / "bad-cc")
    with pytest.raises(PreprocessingError, match="exit code 2") as exc_info:
        preprocessing.preprocess_source(
            c_source,
            language="c",
            config=PreprocessingConfig(mode="compiler", compiler=bad_path),
        )
    assert exc_info.value.category == "PREPROCESSOR_FAILED"
    assert [diagnostic.to_dict() for diagnostic in exc_info.value.diagnostics] == [
        {
            "category": "PREPROCESSOR_FAILED",
            "message": "compiler preprocessing failed with exit code 2",
            "severity": "error",
            "path": None,
            "line": None,
            "command": [bad_path, "-E", "-x", "c", str(c_source)],
        }
    ]

    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type("Done", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )
    result = preprocessing.preprocess_source(
        c_source,
        language="c",
        config=PreprocessingConfig(
            mode="compiler",
            adapter="command-template",
            command_template=f"{sys.executable} {{source}}",
        ),
    )
    assert [diagnostic.to_dict() for diagnostic in result.diagnostics] == [
        {
            "category": "PROVENANCE_UNAVAILABLE",
            "message": "selected compiler adapter did not provide source linemarkers",
            "severity": "warning",
            "path": None,
            "line": None,
            "command": [sys.executable, str(c_source)],
        }
    ]

    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type("Done", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )
    result = preprocessing.preprocess_source(
        c_source,
        language="c",
        config=PreprocessingConfig(mode="compiler", compiler=str(tmp_path / "cc")),
    )
    assert result.diagnostics == []
