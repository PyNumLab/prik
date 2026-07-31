"""Tests split by stable ownership concept from `test_cli.py`."""

from tests.c._support.preprocessing import (
    Path,
    _failing_compiler,
    _fake_compiler,
    json,
    subprocess,
    sys,
)


def test_cli_c_default_compiler_mode_accepts_include_dirs(tmp_path: Path):
    include_dir = tmp_path / "include"
    include_dir.mkdir()
    dependency = include_dir / "types.h"
    header = tmp_path / "api.h"
    dependency.write_text("typedef int api_int;\n", encoding="utf-8")
    header.write_text('#include "types.h"\nint run(void);\n', encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "--json",
            "-I",
            str(include_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(res.stdout)[str(header)]

    assert payload["preprocessing"] == "compiler"
    assert payload["preprocessing_recipe"]["compiler"] == "cc"


def test_cli_c_default_compiler_mode_accepts_define_flags(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int run(void);\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "-D",
            "USE_FAST",
        ],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0


def test_cli_compiler_mode_uses_default_c_compiler(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int run(void);\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0
    assert json.loads(res.stdout)[str(header)]["preprocessing_recipe"]["compiler"] == "cc"


def test_cli_accepts_explicit_compiler_flag(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int run(void);\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "--compiler",
            "gcc-13",
        ],
        capture_output=True,
        text=True,
    )

    assert res.returncode in {0, 1}


def test_cli_c_compiler_mode_runs_exact_compiler_and_parses_preprocessed_stdout(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("#define API(ret) ret\nAPI(int) hidden(void);\n", encoding="utf-8")
    compiler, args_file, env = _fake_compiler(tmp_path, '# 44 "include/api.h"\nint expanded(void);\n')

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "--json",
            "--compiler",
            str(compiler),
            "-I",
            "include",
            "-D",
            "API_EXPORT=",
            "-U",
            "DEBUG",
            "--std",
            "c11",
            "--compiler-arg=--sysroot=/opt/sdk",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    payload = json.loads(res.stdout)[str(header)]
    compiler_args = args_file.read_text(encoding="utf-8").splitlines()

    assert payload["preprocessing"] == "compiler"
    assert [fn["name"] for fn in payload["functions"]] == ["expanded"]
    assert "origin" not in payload["functions"][0]
    assert payload["functions"][0]["source_location"]["filename"] == "include/api.h"
    assert payload["functions"][0]["source_location"]["line"] == 44
    assert compiler_args == [
        "-E",
        "-x",
        "c",
        "-Iinclude",
        "-DAPI_EXPORT=",
        "-UDEBUG",
        "-std=c11",
        "--sysroot=/opt/sdk",
        str(header),
    ]
    recipe = payload["preprocessing_recipe"]
    assert recipe["mode"] == "compiler"
    assert recipe["language"] == "c"
    assert recipe["source_path"] == str(header)
    assert recipe["compiler"] == str(compiler)
    assert recipe["argv"] == [str(compiler), *compiler_args]
    assert recipe["include_dirs"] == ["include"]
    assert recipe["defines"] == ["API_EXPORT="]
    assert recipe["undefs"] == ["DEBUG"]
    assert recipe["standard"] == "c11"
    assert recipe["compiler_args"] == ["--sysroot=/opt/sdk"]
    assert recipe["compile_commands"] is None
    assert recipe["compile_commands_entry"] is None
    assert payload["original_source_paths"] == ["include/api.h"]


def test_cli_preprocessing_failure_has_category_without_traceback_unless_debug(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int run(void);\n", encoding="utf-8")
    compiler = _failing_compiler(tmp_path, "bad option\n")

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "--compiler",
            str(compiler),
        ],
        capture_output=True,
        text=True,
    )
    debug_res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "--compiler",
            str(compiler),
            "--debug",
        ],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 1
    assert "error[PREPROCESSOR_FAILED]" in res.stderr
    assert "bad option" in res.stderr
    assert "Traceback" not in res.stderr
    assert debug_res.returncode == 1
    assert "Traceback" in debug_res.stderr


def test_cli_c_compile_commands_mode_uses_exact_database_compiler(tmp_path: Path):
    source = tmp_path / "api.c"
    source.write_text("API(int) hidden(void);\n", encoding="utf-8")
    compiler, args_file, env = _fake_compiler(tmp_path, '#line 12 "generated/api.h"\nint from_database(void);\n')
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps(
            [
                {
                    "directory": str(tmp_path),
                    "file": str(source),
                    "arguments": [
                        str(compiler),
                        "-Iproject/include",
                        "-DPROJECT_API=",
                        "-c",
                        str(source),
                        "-o",
                        "api.o",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(source),
            "--language",
            "c",
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
    compiler_args = args_file.read_text(encoding="utf-8").splitlines()

    assert [fn["name"] for fn in payload["functions"]] == ["from_database"]
    assert payload["functions"][0]["source_location"]["filename"] == "generated/api.h"
    assert payload["functions"][0]["source_location"]["line"] == 12
    assert compiler_args == ["-E", "-Iproject/include", "-DPROJECT_API=", str(source)]
    recipe = payload["preprocessing_recipe"]
    assert recipe["compiler"] == str(compiler)
    assert recipe["argv"] == [str(compiler), *compiler_args]
    assert recipe["cwd"] == str(tmp_path)
    assert recipe["compile_commands"] == str(database)
    assert recipe["compile_commands_entry"]["file"] == str(source)
    assert recipe["compile_commands_entry"]["arguments"][0] == str(compiler)


def test_cli_c_compiler_mode_macro_metadata_flows_to_parse_report(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("#define API_VERSION 3\nint api(void);\n", encoding="utf-8")
    compiler, _args_file, env = _fake_compiler(
        tmp_path,
        "#define API_VERSION 3\nint api(void);\n",
    )

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "parse",
            str(header),
            "--language",
            "c",
            "--json",
            "--compiler",
            str(compiler),
        ],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )

    macros = {macro["name"]: macro for macro in json.loads(res.stdout)[str(header)]["macros"]}
    assert macros["API_VERSION"]["value"] == "3"
