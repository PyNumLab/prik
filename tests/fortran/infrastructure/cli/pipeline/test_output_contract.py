"""CLI output contracts: report formats, destinations, and generated contract packages."""

import builtins
from importlib import metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import types

import prik
import pytest

import prik.cli as prik_cli
from prik.parsers.fortran import cli as fortran_parser_cli
from tests.fortran._support.paths import GENERAL_FORTRAN_DIR


def _invoke(argv: list[str], capsys) -> tuple[int, str, str]:
    try:
        code = prik_cli.main(argv)
    except SystemExit as exc:
        code = exc.code
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_cli_and_python_api_report_installed_distribution_version():
    expected = metadata.version("prik")
    installed_script = shutil.which("prik")
    assert installed_script is not None
    commands = (
        [sys.executable, "-m", "prik", "--version"],
        [installed_script, "--version"],
    )

    assert prik.__version__ == expected
    assert "__version__" in prik.__all__
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        assert result.stdout == f"prik {expected}\n"
        assert result.stderr == ""


SCOPES_SOURCE = """subroutine work(n)
  integer, intent(in) :: n
end subroutine work

module m
  integer :: n
  real(kind=8), dimension(3) :: x
contains
  subroutine work(n)
    integer, intent(in) :: n
  end subroutine work

  subroutine second()
  end subroutine second
end module m
"""

MODERN_DERIVED_BLOCK = """      Derived types: 3
        - type particle (fields=3, methods=0)
          Fields: 3
            - id:integer[0]
            - mass:real(8)[0]
            - position:real(8)[1]
        - type vector3 (fields=1, methods=0)
          Fields: 1
            - values:real(8)[1]
        - type hidden_state (fields=1, methods=0)
          Fields: 1
            - code:integer[0]
"""


@pytest.mark.parametrize(
    ("source", "options", "present", "absent"),
    [
        pytest.param(
            "scopes.f90",
            [],
            [
                "  Procedures: 1\n    - subroutine work(n:integer[0])",
                "    - module m (vars=2, uses=0)\n      Procedures: 2",
                "        - subroutine second()",
            ],
            ["Variables:"],
            id="free-and-module-procedure-share-a-name",
        ),
        pytest.param(
            "scopes.f90",
            ["--show-vars"],
            ["      Variables: 2\n        - n:integer[0]\n        - x:real(8)[1]"],
            [],
            id="show-vars",
        ),
        pytest.param(
            "scopes.f90",
            ["--show-vars", "--print-limit", "1"],
            ["        - n:integer[0]\n        ... 1 more variables", "        ... 1 more procedures"],
            ["x:real(8)[1]", "subroutine second()"],
            id="print-limit-truncates-variables-and-procedures",
        ),
        pytest.param(
            "scopes.f90",
            ["--print-limit", "0"],
            ["    ... 1 more procedures", "    ... 1 more modules"],
            ["subroutine work"],
            id="zero-print-limit-is-honoured",
        ),
        pytest.param(
            str(GENERAL_FORTRAN_DIR / "modern_pyi_example.f90"),
            [],
            [MODERN_DERIVED_BLOCK, "init_particle(p:type(particle)[0]"],
            [],
            id="module-derived-types-and-derived-arguments",
        ),
    ],
)
def test_parse_report_lists_each_scope_and_honours_report_options(
    tmp_path: Path, monkeypatch, capsys, source, options, present, absent
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scopes.f90").write_text(SCOPES_SOURCE, encoding="utf-8")

    code, out, _err = _invoke(["parse", source, *options], capsys)

    assert code == 0
    assert out.startswith(f"File: {source}\n")
    assert [text for text in present if text not in out] == []
    assert [text for text in absent if text in out] == []


def test_fortran_parser_cli_format_report_print_limit_covers_sections():
    var_a = {"name": "a", "base_type": "integer", "kind": "", "rank": 0}
    var_b = {"name": "b", "base_type": "real", "kind": "8", "rank": 1}
    field_a = {"name": "left", "base_type": "integer", "kind": "", "rank": 0}
    field_b = {"name": "right", "base_type": "integer", "kind": "", "rank": 0}
    proc_a = {"kind": "subroutine", "name": "first", "arguments": [var_a], "result": None}
    proc_b = {"kind": "function", "name": "second", "arguments": [], "result": var_b}
    dtype_a = {"name": "pair", "fields": [field_a, field_b], "methods": []}
    dtype_b = {"name": "hidden_pair", "fields": [], "methods": []}

    report = fortran_parser_cli._format_report(
        {
            "mixed.f90": {
                "signatures": [proc_a, proc_b],
                "types": [dtype_a, dtype_b],
                "modules": [
                    {
                        "name": "m1",
                        "variables": [var_a, var_b],
                        "uses": {},
                        "derived_types": [dtype_a, dtype_b],
                        "procedures": [proc_a, proc_b],
                    },
                    {
                        "name": "m2",
                        "variables": [],
                        "uses": {},
                        "derived_types": [],
                        "procedures": [],
                    },
                ],
                "submodules": [
                    {
                        "name": "sm1",
                        "parent": "m1",
                        "ancestor": None,
                        "variables": [var_a, var_b],
                        "uses": {},
                        "procedures": [proc_a, proc_b],
                    },
                    {
                        "name": "sm2",
                        "parent": "m1",
                        "ancestor": "root",
                        "variables": [],
                        "uses": {},
                        "procedures": [],
                    },
                ],
                "programs": [
                    {"name": "driver", "variables": [var_a, var_b], "uses": {}},
                    {"name": "other_driver", "variables": [], "uses": {}},
                ],
                "block_data": [
                    {"name": None, "variables": [var_a, var_b]},
                    {"name": "named_block", "variables": []},
                ],
            }
        },
        show_vars=True,
        print_limit=1,
    )

    assert "  Procedures: 2" in report
    assert "    - subroutine first(a:integer[0])" in report
    assert "    ... 1 more procedures" in report
    assert "  Derived types: 2" in report
    assert "    ... 1 more derived types" in report
    assert "  Modules: 2" in report
    assert "    - module m1 (vars=2, uses=0)" in report
    assert "      Variables: 2" in report
    assert "        - a:integer[0]" in report
    assert "        ... 1 more variables" in report
    assert "            - left:integer[0]" in report
    assert "            ... 1 more fields" in report
    assert "        ... 1 more derived types" in report
    assert "        ... 1 more procedures" in report
    assert "    ... 1 more modules" in report
    assert "  Submodules: 2" in report
    assert "    - submodule sm1 (parent=m1, vars=2, uses=0)" in report
    assert "    ... 1 more submodules" in report
    assert "  Programs: 2" in report
    assert "    - program driver (vars=2, uses=0)" in report
    assert "    ... 1 more programs" in report
    assert "  Block data: 2" in report
    assert "    - block data <unnamed> (vars=2)" in report
    assert "    ... 1 more block data units" in report


MINI_SOURCE = """module m
contains
  subroutine work(n)
    integer, intent(in) :: n
  end subroutine work
end module m
"""


@pytest.mark.parametrize(
    ("argv", "report_format", "written", "marker"),
    [
        pytest.param(["parse", "mini.f90"], "text", None, "subroutine work", id="parse-text-stdout"),
        pytest.param(["parse", "mini.f90", "--json"], "json", None, "modules", id="parse-json-stdout"),
        pytest.param(
            ["parse", "mini.f90", "--json", "--out", "report.json"],
            "json",
            "report.json",
            "modules",
            id="parse-json-file",
        ),
        pytest.param(
            ["parse", "mini.f90", "--json", "--out"], "json", "mini.json", "modules", id="parse-json-adjacent"
        ),
        pytest.param(["parse", "mini.f90", "--out"], "text", "mini.txt", "subroutine work", id="parse-text-adjacent"),
        pytest.param(["semantics", "mini.f90"], "text", None, "Semantic modules:", id="semantics-text-stdout"),
        pytest.param(["semantics", "mini.f90", "--json"], "json", None, "semantic_modules", id="semantics-json-stdout"),
        pytest.param(
            ["semantics", "mini.f90", "--json", "--out", "semantics.json"],
            "json",
            "semantics.json",
            "semantic_modules",
            id="semantics-json-file",
        ),
        pytest.param(["generate", "--pyi", "mini.f90"], "text", None, "def work(", id="generate-pyi-stdout"),
    ],
)
def test_report_format_and_destination_are_chosen_independently(
    tmp_path: Path, monkeypatch, capsys, argv, report_format, written, marker
):
    """--json picks the format and --out picks the destination; neither changes the report."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mini.f90").write_text(MINI_SOURCE, encoding="utf-8")

    code, out, _err = _invoke(argv, capsys)

    assert code == 0
    if written is None:
        report = out
    else:
        assert out == ""
        report = (tmp_path / written).read_text(encoding="utf-8")
    if report_format == "json":
        assert marker in json.loads(report)["mini.f90"]
    else:
        assert report.startswith("File: mini.f90\n")
        assert marker in report


TWO_MODULES_SOURCE = """module first_mod
contains
  subroutine first()
  end subroutine first
end module first_mod

module second_mod
contains
  subroutine second()
  end subroutine second
end module second_mod
"""

EXTERNAL_TYPE_SOURCE = """module physics
  use types_mod, only: particle
contains
  function create_particle() result(p)
    type(particle) :: p
  end function create_particle
end module physics
"""

OPAQUE_PARTICLE_STUB = (
    'from prik.contracts import Opaque\n\nclass particle(Opaque):\n    pass\n\n__all__ = ["particle"]\n'
)


@pytest.mark.parametrize(
    ("sources", "argv", "expected"),
    [
        pytest.param(
            {"mini.f90": MINI_SOURCE},
            ["mini.f90", "--out"],
            {"mini/mini.pyi": 'from . import m\n\n__all__ = ["m"]\n', "mini/m.pyi": ("def work(",)},
            id="adjacent-package-for-one-module",
        ),
        pytest.param(
            {"combined.f90": TWO_MODULES_SOURCE},
            ["combined.f90", "--out"],
            {
                "combined/combined.pyi": (
                    'from . import first_mod\nfrom . import second_mod\n\n__all__ = ["first_mod", "second_mod"]\n'
                ),
                "combined/first_mod.pyi": ("def first(",),
                "combined/second_mod.pyi": ("def second(",),
            },
            id="adjacent-package-for-two-modules",
        ),
        pytest.param(
            {
                "explicit.f90": "module explicit_mod\ncontains\n  subroutine set_value(x)\n"
                "    real(8), intent(out) :: x\n  end subroutine set_value\nend module explicit_mod\n"
            },
            ["explicit.f90", "--out", "contracts"],
            {
                "contracts/__init__.pyi": 'from . import explicit_mod\n\n__all__ = ["explicit_mod"]\n',
                "contracts/explicit_mod.pyi": ("@native_call([Return('x', 0)])", "def set_value(", "-> Float64: ..."),
            },
            id="explicit-package-directory",
        ),
        pytest.param(
            {"physics.f90": EXTERNAL_TYPE_SOURCE},
            ["physics.f90", "--out"],
            {
                "physics/__init__.pyi": 'from . import physics\n\n__all__ = ["physics"]\n',
                "physics/types_mod.pyi": OPAQUE_PARTICLE_STUB,
            },
            id="opaque-dependency-stub-for-external-type",
        ),
        pytest.param(
            {
                "project/precision.f90": "module precision_mod\n  integer, parameter :: word = 4\n"
                "  integer, parameter :: wp = word * 2\nend module precision_mod\n",
                "project/solver.f90": "subroutine consume(x)\n  use precision_mod, only: local_wp => wp\n"
                "  real(kind=local_wp), intent(inout) :: x(*)\nend subroutine consume\n",
            },
            ["project", "--language", "fortran", "--out", "contracts"],
            {"contracts/__init__.pyi": ("def consume(", "x: Float64[Flat]")},
            id="directory-input-resolves-renamed-project-kind",
        ),
    ],
)
def test_generate_pyi_writes_one_contract_per_module(tmp_path: Path, monkeypatch, capsys, sources, argv, expected):
    monkeypatch.chdir(tmp_path)
    for name, text in sources.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")

    code, out, _err = _invoke(["generate", "--pyi", *argv], capsys)

    assert code == 0
    assert out == ""
    for name, content in expected.items():
        text = (tmp_path / name).read_text(encoding="utf-8")
        if isinstance(content, str):
            assert text == content
        else:
            assert [fragment for fragment in content if fragment not in text] == []


def test_generate_pyi_rejects_a_single_file_destination(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "combined.f90").write_text(TWO_MODULES_SOURCE, encoding="utf-8")

    with pytest.raises(ValueError, match="generated contracts use one file per module"):
        prik_cli.main(["generate", "--pyi", "combined.f90", "--out", "combined.pyi"])

    assert not (tmp_path / "combined.pyi").exists()


def test_pyi_dependency_stubs_are_shared_once_and_conflicts_rejected(tmp_path: Path):
    report = {
        "first.f90": {
            "pyi": "def first() -> None: ...",
            "pyi_dependencies": {"shared": "class shared(Opaque):\n    pass"},
        },
        "second.f90": {
            "pyi": "def second() -> None: ...",
            "pyi_dependencies": {
                "shared": "class shared(Opaque):\n    pass",
                "extra": "class extra(Opaque):\n    pass",
            },
        },
        "empty.f90": {},
    }

    assert prik_cli._format_pyi_report(report) == (
        "File: first.f90\ndef first() -> None: ...\n\n"
        "Dependency stub: shared.pyi\nclass shared(Opaque):\n    pass\n\n"
        "File: second.f90\ndef second() -> None: ...\n\n"
        "Dependency stub: extra.pyi\nclass extra(Opaque):\n    pass\n\n"
        "File: empty.f90\n<no module declarations found>"
    )

    stub = "class Shared:\n    pass"
    prik_cli._write_pyi_dependencies(
        {
            "first.f90": {"pyi_dependencies": {"pkg.sub.shared": stub}},
            "second.f90": {"pyi_dependencies": {"pkg.sub.shared": stub}},
        },
        output_dir=tmp_path,
    )
    assert (tmp_path / "pkg" / "sub" / "shared.pyi").read_text(encoding="utf-8") == stub + "\n"
    assert not (tmp_path / "pkg.sub.shared.pyi").exists()

    with pytest.raises(ValueError, match="Conflicting generated dependency stub"):
        prik_cli._write_pyi_dependencies(
            {
                "first.f90": {"pyi_dependencies": {"shared": "class shared:\n    pass"}},
                "second.f90": {"pyi_dependencies": {"shared": "class shared:\n    value: int"}},
            },
            output_dir=tmp_path,
        )


ASSUMED_INTENT_SOURCE = """module legacy_mod
contains
  real(8) function weigh(count, factor)
    integer(4) :: count
    real(8) :: factor
    weigh = real(count, 8) * factor
  end function weigh
end module legacy_mod
"""


def test_assume_intent_in_scalars_reaches_the_generated_contract(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "legacy.f90").write_text(ASSUMED_INTENT_SOURCE, encoding="utf-8")

    assert _invoke(["generate", "--pyi", "legacy.f90", "--out", "default"], capsys)[0] == 0
    assert (
        _invoke(["generate", "--pyi", "legacy.f90", "--out", "assumed", "--assume-intent-in-scalars"], capsys)[0] == 0
    )

    default = (tmp_path / "default" / "legacy_mod.pyi").read_text(encoding="utf-8")
    assumed = (tmp_path / "assumed" / "legacy_mod.pyi").read_text(encoding="utf-8")
    assert 'Returns["count", Int32]' in default
    assert 'Returns["factor", Float64]' in default
    assert "Returns" not in assumed
    assert "-> Float64: ..." in assumed


def test_fortran_parser_cli_pyi_is_the_contract_generate_writes(tmp_path: Path, monkeypatch, capsys):
    """The parser CLI shows the generated contract, not an unplanned rendering of its own.

    Its report converted and printed each module alone, so a module importing
    from another file lost the import completion plans and the spelling
    completion gives each name.
    """
    monkeypatch.chdir(tmp_path)
    helpers = tmp_path / "helpers.f90"
    helpers.write_text(
        "module helpers\ncontains\n"
        "pure integer function lambda(n)\ninteger, intent(in) :: n\nlambda = n\nend function lambda\n"
        "end module helpers\n",
        encoding="utf-8",
    )
    user = tmp_path / "user.f90"
    user.write_text(
        "module user_mod\nuse helpers, only : lambda\ncontains\n"
        "subroutine fill(n, x)\ninteger, intent(in) :: n\nreal(8), intent(out) :: x(lambda(n))\nend subroutine fill\n"
        "end module user_mod\n",
        encoding="utf-8",
    )
    assert _invoke(["generate", "--pyi", str(helpers), str(user), "--out", "contracts"], capsys)[0] == 0

    report = fortran_parser_cli._semantic_report([str(helpers), str(user)])

    contracts = tmp_path / "contracts"
    assert report[str(helpers)]["pyi"] == (contracts / "helpers.pyi").read_text(encoding="utf-8").strip()
    assert report[str(user)]["pyi"] == (contracts / "user_mod.pyi").read_text(encoding="utf-8").strip()
    assert "from .helpers import lambda_" in report[str(user)]["pyi"]


@pytest.mark.parametrize("failure", ["rich-unavailable", "terminal-print-fails"])
def test_pyi_terminal_highlighting_falls_back_to_plain_text(monkeypatch, capsys, failure):
    """Syntax highlighting is optional; the contract text must still reach the terminal."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    if failure == "rich-unavailable":
        real_import = builtins.__import__

        def fail_rich_import(name, *args, **kwargs):
            if name.startswith("rich"):
                raise ImportError("rich disabled for test")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fail_rich_import)
    else:

        class RaisingConsole:
            def __init__(self, **_options):
                pass

            def print(self, _syntax):
                raise RuntimeError("terminal failed")

        console_module = types.ModuleType("rich.console")
        syntax_module = types.ModuleType("rich.syntax")
        console_module.Console = RaisingConsole
        syntax_module.Syntax = lambda code, *_args, **_options: code
        monkeypatch.setitem(sys.modules, "rich", types.ModuleType("rich"))
        monkeypatch.setitem(sys.modules, "rich.console", console_module)
        monkeypatch.setitem(sys.modules, "rich.syntax", syntax_module)

    prik_cli.print_pyi_output("def f() -> None: ...")

    assert "def f() -> None: ..." in capsys.readouterr().out
