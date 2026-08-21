"""C input-language CLI argument contracts."""

from pathlib import Path
import types

import pytest

import prik.cli as prik_cli
from tests.c._support.cli import (
    _MainParserError,
    _install_main_parser,
    _main_args,
)


def test_prik_build_preprocessing_config_preserves_full_config_contract(monkeypatch):
    args = types.SimpleNamespace(
        defines=["USE_FAST=1"],
        undefs=["LEGACY"],
        compiler="cc",
        compile_commands="compile_commands.json",
        preprocessor_adapter="command-template",
        preprocess_template="{compiler} -E {source}",
        include_dirs=["include"],
        std="c11",
        compiler_args=["--target=test"],
        include_exposure="all-project",
        public_includes=["public.h"],
        private_includes=["private.h"],
        language="c",
    )
    config = types.SimpleNamespace(
        uses_compiler=True,
        command_template=args.preprocess_template,
        adapter=args.preprocessor_adapter,
        compiler=args.compiler,
        compile_commands=args.compile_commands,
        include_dirs=args.include_dirs,
    )
    calls = []

    class Parser:
        def error(self, message):
            raise AssertionError(message)

    def validate(value, option):
        calls.append(("validate", value, option))

    def build(**kwargs):
        calls.append(("build", kwargs))
        return config

    monkeypatch.setattr(prik_cli, "validate_macro_name", validate)
    monkeypatch.setattr(prik_cli, "PreprocessingConfig", build)

    assert prik_cli._build_preprocessing_config(args, Parser()) is config
    assert calls == [
        ("validate", "USE_FAST=1", "--define/-D"),
        ("validate", "LEGACY", "--undef/-U"),
        (
            "build",
            {
                "mode": "compiler",
                "compiler": "cc",
                "compile_commands": "compile_commands.json",
                "adapter": "command-template",
                "command_template": "{compiler} -E {source}",
                "include_dirs": ["include"],
                "defines": ["USE_FAST=1"],
                "undefs": ["LEGACY"],
                "std": "c11",
                "compiler_args": ["--target=test"],
                "include_exposure": "all-project",
                "public_includes": ["public.h"],
                "private_includes": ["private.h"],
            },
        ),
    ]


def test_prik_main_rejects_fortran_only_c_parse_options(monkeypatch):
    overrides = {"language": "c", "parse": True, "show_vars": True}
    expected = "--show-vars is Fortran-only and is not supported for --language c"
    args = _main_args(**overrides)
    _install_main_parser(monkeypatch, args)
    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, language, parser: language)
    monkeypatch.setattr(
        prik_cli,
        "_build_preprocessing_config",
        lambda active_args, parser: object(),
    )

    with pytest.raises(_MainParserError) as exc_info:
        prik_cli.main()

    assert str(exc_info.value) == expected


def test_prik_resolve_language_handles_c_input_edges(tmp_path: Path):
    class ErrorParser:
        def error(self, message):
            raise ValueError(message)

    parser = ErrorParser()
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    c_header = tmp_path / "api.h"
    c_header.write_text("int add(int x);\n", encoding="utf-8")
    unknown = tmp_path / "notes.txt"
    unknown.write_text("notes\n", encoding="utf-8")

    assert prik_cli._resolve_language([str(unknown)], "c", parser) == "c"
    with pytest.raises(ValueError) as requested_error:
        prik_cli._resolve_language([str(input_dir), str(c_header)], "fortran", parser)
    assert str(requested_error.value) == (
        f"C input {c_header} is incompatible with --language fortran; pass --language c. Use --help for examples."
    )
