import builtins

from dataclasses import dataclass

import json

import os

import runpy

import subprocess

import sys

import types

from pathlib import Path

import pytest

from prik.parsers.fortran import cli as fortran_parser_cli

from prik import FortranParseError

from prik import cli as prik_cli

from prik.pipeline.preprocessing import PreprocessingConfig, PreprocessingDiagnostic, PreprocessingError

TEST_FILE = Path(__file__).parents[2] / "source_parsing" / "parsing" / "fixtures" / "general" / "basic_subroutine.f90"


class _MainParserError(Exception):
    pass


def _main_args(**overrides):
    values = {
        "paths": ["input.f90"],
        "command": "build",
        "language": "fortran",
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
        "no_compile_input_sources": False,
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


def _patch_main_report_payloads(
    monkeypatch,
    *,
    language="fortran",
    parse_payload=None,
    semantic_payload=None,
):
    preprocessing = object()
    calls = []
    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, _active_language, parser: language)
    monkeypatch.setattr(prik_cli, "_build_preprocessing_config", lambda args, parser: preprocessing)
    monkeypatch.setattr(
        prik_cli,
        "_parse_report",
        lambda paths, active_preprocessing: calls.append(("parse", paths, active_preprocessing)) or parse_payload,
    )
    monkeypatch.setattr(
        prik_cli,
        "_semantic_report",
        lambda paths, active_preprocessing, *, language: (
            calls.append(("semantic", paths, active_preprocessing, language)) or semantic_payload
        ),
    )
    return preprocessing, calls


__all__ = (
    "TEST_FILE",
    "FortranParseError",
    "Path",
    "PreprocessingConfig",
    "PreprocessingDiagnostic",
    "PreprocessingError",
    "_MainParserError",
    "_install_main_parser",
    "_main_args",
    "_patch_main_report_payloads",
    "builtins",
    "dataclass",
    "fortran_parser_cli",
    "json",
    "os",
    "prik_cli",
    "pytest",
    "runpy",
    "subprocess",
    "sys",
    "types",
)
