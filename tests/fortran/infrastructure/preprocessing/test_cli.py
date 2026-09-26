"""The ``prik parse`` CLI runs Fortran compiler preprocessing and reports its recipe."""

import json
from pathlib import Path
import subprocess
import sys

from tests.fortran.infrastructure.preprocessing._support import _fake_compiler


def test_cli_accepts_compile_database_for_fortran_compiler_mode(tmp_path: Path):
    source = tmp_path / "solver.F90"
    source.write_text("subroutine solve()\nend subroutine solve\n", encoding="utf-8")
    compiler, _args_file, env = _fake_compiler(
        tmp_path,
        "subroutine from_database()\nend subroutine from_database\n",
    )
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps(
            [
                {
                    "directory": str(tmp_path),
                    "file": str(source),
                    "arguments": [str(compiler), "-cpp", "-c", str(source), "-o", "solver.o"],
                }
            ]
        ),
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "parse",
            str(source),
            "--json",
            "--compile-commands",
            str(database),
        ],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )

    payload = json.loads(res.stdout)[str(source)]
    assert [signature["name"] for signature in payload["signatures"]] == ["from_database"]
    assert payload["preprocessing_recipe"]["compile_commands"] == str(database)


def test_cli_fortran_default_compiler_mode_accepts_include_dirs_and_records_recipe(tmp_path: Path):
    source = tmp_path / "mini.F90"
    source.write_text("subroutine work()\nend subroutine work\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, "-m", "prik", "parse", str(source), "--json", "-I", "include"],
        capture_output=True,
        text=True,
        check=True,
    )

    recipe = json.loads(res.stdout)[str(source)]["preprocessing_recipe"]
    assert recipe["compiler"] == "gfortran"
    assert recipe["include_dirs"] == ["include"]


def test_cli_fortran_compiler_mode_runs_exact_compiler_and_parses_stdout(tmp_path: Path):
    source = tmp_path / "generated.F90"
    source.write_text("#define MAKE_SUBROUTINE name\n", encoding="utf-8")
    compiler, args_file, env = _fake_compiler(
        tmp_path,
        "subroutine from_compiler()\nend subroutine from_compiler\n",
    )

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "parse",
            str(source),
            "--json",
            "--compiler",
            str(compiler),
            "-I",
            "include",
            "-D",
            "USE_MPI",
            "-U",
            "DEBUG",
            "--std",
            "f2018",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    compiler_args = args_file.read_text(encoding="utf-8").splitlines()
    payload = json.loads(res.stdout)[str(source)]

    assert [signature["name"] for signature in payload["signatures"]] == ["from_compiler"]
    assert compiler_args == [
        "-E",
        "-cpp",
        "-Iinclude",
        "-DUSE_MPI",
        "-UDEBUG",
        "-std=f2018",
        str(source),
    ]
    recipe = payload["preprocessing_recipe"]
    assert recipe["mode"] == "compiler"
    assert recipe["language"] == "fortran"
    assert recipe["compiler"] == str(compiler)
    assert recipe["argv"] == [str(compiler), *compiler_args]
    assert recipe["include_dirs"] == ["include"]
    assert recipe["defines"] == ["USE_MPI"]
    assert recipe["undefs"] == ["DEBUG"]
    assert recipe["standard"] == "f2018"
