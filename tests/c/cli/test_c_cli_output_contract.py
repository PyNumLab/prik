"""C input-language CLI output contracts."""

from tests.c._support.cli import (
    _install_main_parser,
    _main_args,
    types,
    x2py_cli,
)


def test_x2py_main_preserves_c_readable_stdout_contract(monkeypatch, capsys):
    args = _main_args(language="c", parse=True, print_limit=2)
    _install_main_parser(monkeypatch, args)
    preprocessing = types.SimpleNamespace(include_dirs=())
    parse_payload = {"parse": {"node": 1}}
    formats = []

    monkeypatch.setattr(x2py_cli, "_resolve_language", lambda paths, language, parser: language)
    monkeypatch.setattr(
        x2py_cli,
        "_build_preprocessing_config",
        lambda active_args, parser: preprocessing,
    )
    monkeypatch.setattr(
        x2py_cli,
        "_c_parser_preprocessing_mode",
        lambda active_preprocessing: "mode",
    )
    monkeypatch.setattr(
        x2py_cli,
        "_c_source_loader",
        lambda active_preprocessing: "loader",
    )
    monkeypatch.setattr(x2py_cli, "parse_c_report", lambda *args, **kwargs: parse_payload)
    monkeypatch.setattr(
        x2py_cli,
        "format_c_report",
        lambda payload, **kwargs: formats.append((payload, kwargs)) or "C REPORT",
    )

    assert x2py_cli.main() == 0
    assert capsys.readouterr().out == "C REPORT\n"
    assert formats == [(parse_payload, {"print_limit": 2})]
