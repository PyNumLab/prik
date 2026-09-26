"""C compiler-preprocessor execution: failure categories, provenance, and recipe macros."""

from pathlib import Path
import subprocess
import sys

import pytest

import prik.preprocessing.source as preprocessing
from prik.parsers.c import sources as c_sources
from prik.preprocessing import PreprocessingConfig, PreprocessingError


def _completed(returncode: int, stdout: str = "", stderr: str = ""):
    return lambda *_args, **_kwargs: subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)


def _raise(error: Exception):
    def run(*_args, **_kwargs):
        raise error

    return run


@pytest.mark.parametrize(
    ("compiler", "run", "category", "message", "diagnostic"),
    [
        pytest.param(
            None,
            None,
            "INVALID_COMPILER_ARGUMENTS",
            "Compiler preprocessing not configured",
            None,
            id="not-configured",
        ),
        pytest.param(
            "prik-definitely-missing-preprocessor",
            None,
            "PREPROCESSOR_NOT_FOUND",
            "preprocessor not found: prik-definitely-missing-preprocessor",
            "preprocessor not found: prik-definitely-missing-preprocessor",
            id="executable-not-on-path",
        ),
        pytest.param(
            "missing-cc",
            _raise(FileNotFoundError("missing")),
            "PREPROCESSOR_NOT_FOUND",
            "preprocessor not found: {compiler}",
            "preprocessor not found: {compiler}",
            id="executable-vanished",
        ),
        pytest.param(
            "cannot-start-cc",
            _raise(OSError("cannot start")),
            "PREPROCESSOR_FAILED",
            "failed to run compiler preprocessor: cannot start",
            "failed to run compiler preprocessor: cannot start",
            id="executable-cannot-start",
        ),
        pytest.param(
            "slow-cc",
            _raise(subprocess.TimeoutExpired(cmd="cc", timeout=60)),
            "PREPROCESSOR_FAILED",
            "compiler preprocessing failed: timed out after 60 seconds",
            "compiler preprocessing timed out after 60 seconds",
            id="timeout",
        ),
        pytest.param(
            "failing-cc",
            _completed(1, stderr="bad option"),
            "PREPROCESSOR_FAILED",
            "compiler preprocessing failed with exit code 1\nbad option",
            "bad option",
            id="nonzero-exit-with-stderr",
        ),
        pytest.param(
            "bad-cc",
            _completed(2),
            "PREPROCESSOR_FAILED",
            "compiler preprocessing failed with exit code 2",
            "compiler preprocessing failed with exit code 2",
            id="silent-nonzero-exit",
        ),
    ],
)
def test_preprocess_source_reports_each_failure_with_its_category(
    monkeypatch, tmp_path: Path, compiler, run, category, message, diagnostic
):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    if run is not None:
        # A path-like executable skips the PATH lookup, so the stubbed launch decides the outcome.
        compiler = str(tmp_path / compiler)
        monkeypatch.setattr(preprocessing.subprocess, "run", run)
        message = message.format(compiler=compiler)
        diagnostic = diagnostic.format(compiler=compiler)
    config = PreprocessingConfig() if compiler is None else PreprocessingConfig(mode="compiler", compiler=compiler)

    with pytest.raises(PreprocessingError) as exc_info:
        preprocessing.preprocess_source(source, language="c", config=config)

    assert str(exc_info.value) == message
    assert exc_info.value.category == category
    expected = []
    if diagnostic is not None:
        expected = [
            {
                "category": category,
                "message": diagnostic,
                "severity": "error",
                "path": None,
                "line": None,
                "command": [compiler, "-E", "-x", "c", str(source)],
            }
        ]
    assert [item.to_dict() for item in exc_info.value.diagnostics] == expected


def test_preprocess_source_warns_when_the_adapter_output_has_no_source_mapping(monkeypatch, tmp_path: Path):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    monkeypatch.setattr(preprocessing.subprocess, "run", _completed(0))

    template = preprocessing.preprocess_source(
        source,
        language="c",
        config=PreprocessingConfig(
            mode="compiler",
            adapter="command-template",
            command_template=f"{sys.executable} {{source}}",
        ),
    )
    direct_config = PreprocessingConfig(mode="compiler", compiler=str(tmp_path / "cc"))
    empty_direct = preprocessing.preprocess_source(source, language="c", config=direct_config)
    monkeypatch.setattr(preprocessing.subprocess, "run", _completed(0, stdout="int api(void);\n"))
    direct = preprocessing.preprocess_source(source, language="c", config=direct_config)

    assert [item.to_dict() for item in template.diagnostics] == [
        {
            "category": "PROVENANCE_UNAVAILABLE",
            "message": "selected compiler adapter did not provide source linemarkers",
            "severity": "warning",
            "path": None,
            "line": None,
            "command": [sys.executable, str(source)],
        }
    ]
    # A linemarker-capable adapter is trusted even when its output is empty.
    assert empty_direct.diagnostics == []
    assert direct.diagnostics == []
    # Output without linemarkers maps line for line onto the root source.
    assert direct.source_mappings == [
        preprocessing.SourceMapping(
            generated_line=1,
            original_path=str(source),
            original_line=1,
            include_stack=[str(source)],
        )
    ]


def test_attach_preprocessing_recipe_filters_invalid_and_duplicate_macros():
    empty = c_sources.CFile()
    c_sources.attach_preprocessing_recipe(empty, None)
    assert empty.preprocessing_recipe is None

    parsed = c_sources.CFile(
        macros=[
            c_sources.CMacro(
                name="EXISTING",
                source_location=c_sources.CSourceLocation(filename="api.h", line=2),
            )
        ]
    )
    recipe = {
        "macros": [
            None,
            {"name": ""},
            {"name": "EXISTING", "path": "api.h", "line": 2},
            {"name": "NEW", "value": 123, "function_like": 1, "path": 42, "line": "bad"},
            {"name": "WITH_LOC", "value": "1", "path": "api.h", "line": 4},
        ]
    }

    c_sources.attach_preprocessing_recipe(parsed, recipe)

    assert parsed.preprocessing_recipe == recipe
    assert [macro.name for macro in parsed.macros] == ["EXISTING", "NEW", "WITH_LOC"]
    assert parsed.macros[1].value is None
    assert parsed.macros[1].function_like is True
    assert parsed.macros[1].source_location.filename is None
    assert parsed.macros[2].source_location.line == 4
