"""Shared setup for C input-language CLI tests."""

from __future__ import annotations

import types

import prik.cli as prik_cli


class _MainParserError(Exception):
    pass


def _main_args(**overrides):
    values = {
        "paths": ["input.h"],
        "command": "build",
        "language": "c",
        "parse": False,
        "preprocessor_adapter": "auto",
        "compiler": None,
        "compile_commands": None,
        "preprocess_template": None,
        "include_dirs": [],
        "defines": [],
        "undefs": [],
        "std": None,
        "compiler_args": [],
        "include_exposure": "reachable-project",
        "public_includes": [],
        "private_includes": [],
        "show_vars": False,
        "print_limit": None,
        "vars_limit": None,
        "makefile": False,
        "generate_sources": False,
        "build_manifest": None,
        "native_fortran_sources": None,
        "native_compile_flags": None,
        "native_objects": None,
        "native_libraries": None,
        "native_link_items": None,
        "native_library_dirs": None,
        "strict_wrapper_names": False,
        "wrapper_compiler_debug": False,
        "wrapper_fortran_flags": None,
        "wrapper_c_flags": None,
        "semantics": False,
        "pyi": False,
        "json": False,
        "out": None,
        "out_dir": None,
        "verbose": False,
        "no_color": False,
        "debug": False,
    }
    values.update(overrides)
    if "command" not in overrides:
        if values["parse"]:
            values["command"] = "parse"
        elif values["semantics"]:
            values["command"] = "semantics"
        elif values["pyi"] or values["generate_sources"] or values["makefile"]:
            values["command"] = "generate"
    return types.SimpleNamespace(**values)


def _install_main_parser(monkeypatch, args):
    class FakeParser:
        def add_argument(self, *_args, **_kwargs):
            pass

        def add_argument_group(self, *_args, **_kwargs):
            return self

        def parse_args(self, _argv=None):
            return args

        def error(self, message):
            raise _MainParserError(message)

    parser = FakeParser()
    monkeypatch.setattr(prik_cli, "_parser_for_argv", lambda argv: (parser, argv))
    return parser
