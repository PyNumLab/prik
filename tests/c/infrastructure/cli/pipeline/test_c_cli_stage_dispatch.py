"""C input-language CLI dispatch contracts."""

from pathlib import Path

import pytest

import prik.cli as prik_cli
from prik.parsers.c import sources as c_sources
from tests.c._support.cli import (
    _install_main_parser,
    _main_args,
)


def test_prik_main_preserves_c_parse_dispatch_contract(monkeypatch):
    class StopAfterDispatch(Exception):
        pass

    args = _main_args(language="requested", parse=True)
    _install_main_parser(monkeypatch, args)
    preprocessing = type("Preprocessing", (), {"include_dirs": ("include",)})()
    parse_payload = {"parse": "payload"}
    calls = []

    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, language, parser: "c")
    monkeypatch.setattr(
        prik_cli,
        "_build_preprocessing_config",
        lambda active_args, parser: preprocessing,
    )
    monkeypatch.setattr(
        prik_cli,
        "parse_c_report",
        lambda paths, active_preprocessing: calls.append(("parse", paths, active_preprocessing)) or parse_payload,
    )
    monkeypatch.setattr(
        prik_cli,
        "_select_main_payload",
        lambda *_args: (_ for _ in ()).throw(StopAfterDispatch),
    )

    with pytest.raises(StopAfterDispatch):
        prik_cli.main()

    # The C parse report receives the one preprocessing configuration the CLI built.
    assert calls == [("parse", args.paths, preprocessing)]


@pytest.mark.parametrize("stage", ["semantics", "pyi"])
def test_prik_main_accepts_each_non_parse_c_stage(monkeypatch, stage):
    class StopAfterDispatch(Exception):
        pass

    args = _main_args(language="c", **{stage: True})
    _install_main_parser(monkeypatch, args)
    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, language, parser: language)
    monkeypatch.setattr(
        prik_cli,
        "_build_preprocessing_config",
        lambda active_args, parser: object(),
    )
    monkeypatch.setattr(prik_cli, "_semantic_report", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        prik_cli,
        "_select_main_payload",
        lambda *_args: (_ for _ in ()).throw(StopAfterDispatch),
    )

    with pytest.raises(StopAfterDispatch):
        prik_cli.main()


def test_one_c_parse_preserves_parser_and_preprocessing_arguments(
    tmp_path: Path,
    monkeypatch,
):
    """Every C route parses a path through parse_c_source, raw or compiler-preprocessed."""
    path = tmp_path / "api.h"
    raw_parsed = object()
    compiled_parsed = object()

    class RawParser:
        def parse_file(self, source, *, filename, include_dirs, preprocessing):
            assert source == path
            assert filename == str(path)
            assert include_dirs == ["include"]
            assert preprocessing == "raw"
            return raw_parsed

    raw_config = prik_cli.PreprocessingConfig(include_dirs=["include"])
    assert c_sources.parse_c_source(path, raw_config, parser=RawParser()) is raw_parsed

    class Recipe:
        def to_dict(self):
            return {"mode": "compiler"}

    def preprocess(received_path, *, language, config):
        assert received_path == path
        assert language == "c"
        assert config is compiler_config
        return "int add(int x);\n", Recipe()

    class CompilerParser:
        def parse_file(self, source, *, filename, include_dirs, preprocessing):
            assert source == "int add(int x);\n"
            assert filename == str(path)
            assert include_dirs == ["include"]
            assert preprocessing == "compiler"
            return compiled_parsed

    def attach_recipe(parsed, recipe):
        assert parsed is compiled_parsed
        assert recipe == {"mode": "compiler"}

    compiler_config = prik_cli.PreprocessingConfig(
        mode="compiler",
        compiler="cc",
        include_dirs=["include"],
    )
    monkeypatch.setattr(c_sources, "run_compiler_preprocessor_with_recipe", preprocess)
    monkeypatch.setattr(c_sources, "attach_preprocessing_recipe", attach_recipe)

    assert c_sources.parse_c_source(path, compiler_config, parser=CompilerParser()) is compiled_parsed


def test_prik_main_preserves_c_parse_error_rendering_contract(monkeypatch, capsys):
    args = _main_args(language="c", parse=True, no_color=True)
    _install_main_parser(monkeypatch, args)
    preprocessing = type("Preprocessing", (), {"include_dirs": ()})()
    error = prik_cli.CParseError("bad parse")
    calls = []

    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, language, parser: "c")
    monkeypatch.setattr(
        prik_cli,
        "_build_preprocessing_config",
        lambda active_args, parser: preprocessing,
    )
    monkeypatch.setattr(
        prik_cli,
        "_env_flag",
        lambda name: calls.append(("env", name)) or False,
    )
    monkeypatch.setattr(
        prik_cli,
        "_diagnostic_color_enabled",
        lambda *, disabled: calls.append(("color", disabled)) or "color-enabled",
    )
    monkeypatch.setattr(
        prik_cli.CParseError,
        "format_diagnostic",
        lambda self, *, color, debug: calls.append(("render", color, debug)) or "rendered diagnostic",
    )
    monkeypatch.setattr(
        prik_cli,
        "parse_c_report",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    assert prik_cli.main() == 1
    assert capsys.readouterr().err == "rendered diagnostic\n"
    assert calls == [
        ("env", "C_PARSER_DEBUG"),
        ("color", True),
        ("render", "color-enabled", False),
    ]


def test_prik_main_reraises_c_parse_errors_for_debug_environment(monkeypatch):
    args = _main_args(language="c", parse=True)
    _install_main_parser(monkeypatch, args)
    preprocessing = type("Preprocessing", (), {"include_dirs": ()})()
    error = prik_cli.CParseError("bad parse")
    calls = []

    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, language, parser: "c")
    monkeypatch.setattr(
        prik_cli,
        "_build_preprocessing_config",
        lambda active_args, parser: preprocessing,
    )
    monkeypatch.setattr(
        prik_cli,
        "_env_flag",
        lambda name: calls.append(name) or name == "C_PARSER_DEBUG",
    )
    monkeypatch.setattr(
        prik_cli,
        "parse_c_report",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    with pytest.raises(prik_cli.CParseError):
        prik_cli.main()

    assert calls == ["C_PARSER_DEBUG"]
