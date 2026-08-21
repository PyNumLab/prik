import sys
from pathlib import Path

import pytest

import prik.compiler.compiler_profiles as compiler_profiles
import prik.compiler.compilers as compiler_module
from prik.compiler.objects import ObjectFile
from prik.compiler.compilers import Compiler
from prik.compiler.compiler_profiles import available_compilers, fortran_compiler_family, vendors


def test_record_only_compiler_keeps_object_command_without_executing(monkeypatch, tmp_path: Path):
    compiler = Compiler("GNU", execute_commands=False)
    monkeypatch.setattr(compiler, "_executable", lambda _language, _tools: "gcc")
    monkeypatch.setattr(
        Compiler,
        "run_command",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("command executed")),
    )
    object_file = ObjectFile(
        source=tmp_path / "source.c",
        object_path=tmp_path / "source.o",
        language="c",
    )

    compiler.compile_object(object_file)

    command = compiler.command_log[0]
    assert command[0] == "gcc"
    assert command[-4:] == ("-c", str(object_file.source), "-o", str(object_file.object_path))


def test_user_compile_flags_follow_default_profile_flags(monkeypatch, tmp_path: Path):
    compiler = Compiler("GNU", debug=False, execute_commands=False)
    monkeypatch.setattr(compiler, "_executable", lambda _language, _tools: "gcc")
    object_file = ObjectFile(
        source=tmp_path / "source.c",
        object_path=tmp_path / "source.o",
        language="c",
        flags=("-O0", "-g0"),
    )

    compiler.compile_object(object_file)

    command = compiler.command_log[0]
    assert command.index("-O3") < command.index("-O0")
    assert command.index("-DNDEBUG") < command.index("-g0")


def test_input_language_executable_override_controls_compilation_and_linking(tmp_path: Path):
    compiler = Compiler("GNU", execute_commands=False, executables={"fortran": sys.executable})
    native = ObjectFile(tmp_path / "native.f90", tmp_path / "native.o", "fortran")

    compiler.compile_object(native)
    compiler.link_extension(
        module_name="wrapped",
        output_dir=tmp_path,
        language="fortran",
        objects=(native,),
    )

    assert compiler.command_log[0][0] == sys.executable
    assert compiler.command_log[1][0] == sys.executable


@pytest.mark.parametrize(
    ("fortran_name", "c_name", "vendor", "fortran_flag", "c_flag"),
    (
        ("x86_64-linux-gnu-gfortran-15", "x86_64-linux-gnu-gcc-15", "GNU", "-J", "-funroll-loops"),
        ("ifx", "icx", "intel", "-module", "-funroll-loops"),
        ("flang-22", "clang-22", "LLVM", "-J", "-funroll-loops"),
        ("nvfortran", "nvc", "nvidia", "-module", "-Munroll"),
        ("pgfortran", "pgcc", "PGI", "-module", "-Munroll"),
    ),
)
def test_fortran_selection_uses_one_coherent_vendor_profile(
    tmp_path: Path,
    fortran_name: str,
    c_name: str,
    vendor: str,
    fortran_flag: str,
    c_flag: str,
):
    fortran = tmp_path / fortran_name
    c_compiler = tmp_path / c_name
    for executable in (fortran, c_compiler):
        executable.touch(mode=0o755)

    compiler = Compiler.from_fortran_executable(
        str(fortran),
        execute_commands=False,
        search_path=str(tmp_path),
    )
    native = ObjectFile(tmp_path / "native.f90", tmp_path / "native.o", "fortran")
    binding = ObjectFile(tmp_path / "binding.c", tmp_path / "binding.o", "c")

    compiler.compile_object(native)
    compiler.compile_object(binding)
    compiler.link_extension(
        module_name="wrapped",
        output_dir=tmp_path,
        language="fortran",
        objects=(native, binding),
    )

    assert fortran_compiler_family(str(fortran))[1] == vendor
    assert compiler.command_log[0][0] == str(fortran)
    assert fortran_flag in compiler.command_log[0]
    assert compiler.command_log[1][0] == str(c_compiler)
    assert c_flag in compiler.command_log[1]
    assert compiler.command_log[2][0] == str(fortran)


def test_fortran_selection_rejects_an_unknown_compiler_family(tmp_path: Path):
    compiler = tmp_path / "mystery-fortran"
    compiler.touch(mode=0o755)

    with pytest.raises(ValueError, match="Unknown Fortran compiler family"):
        Compiler.from_fortran_executable(str(compiler), execute_commands=False)


@pytest.mark.parametrize(
    ("banner", "vendor"),
    [
        ("Apple clang version 15.0.0 (clang-1500.3.9.4)\nTarget: arm64-apple-darwin23.4.0", "LLVM"),
        ("cc (Ubuntu 13.3.0-6ubuntu2) 13.3.0\nCopyright (C) 2023 Free Software Foundation, Inc.", "GNU"),
        ("Intel(R) oneAPI DPC++/C++ Compiler 2024.0.0 (2024.0.0.20231017)", "intel"),
    ],
)
def test_generic_c_driver_takes_its_vendor_from_its_own_version_banner(tmp_path: Path, banner: str, vendor: str):
    """``cc`` names no vendor, and on some platforms it is not a link to one."""
    compiler = tmp_path / "cc"
    compiler.write_text(f'#!/bin/sh\nif [ "$1" = "--version" ]; then\n  cat <<\'EOF\'\n{banner}\nEOF\nfi\n')
    compiler.chmod(0o755)

    selected = Compiler.from_c_executable("cc", execute_commands=False, search_path=str(tmp_path))

    assert selected._toolchain is available_compilers[vendor]


def test_c_selection_rejects_a_driver_that_names_no_family_and_reports_none(tmp_path: Path):
    compiler = tmp_path / "mystery-driver"
    compiler.write_text("#!/bin/sh\nexit 1\n")
    compiler.chmod(0o755)

    with pytest.raises(ValueError, match="Unknown C compiler family"):
        Compiler.from_c_executable("mystery-driver", execute_commands=False, search_path=str(tmp_path))


def test_fortran_selection_rejects_a_missing_vendor_c_compiler(tmp_path: Path):
    compiler = tmp_path / "ifx"
    compiler.touch(mode=0o755)

    with pytest.raises(FileNotFoundError, match=r"intel C compiler.*icx"):
        Compiler.from_fortran_executable(
            str(compiler),
            execute_commands=False,
            search_path=str(tmp_path),
        )


def test_python_sysconfig_compile_flags_are_not_forwarded_to_vendor_compiler(monkeypatch, tmp_path: Path):
    compiler = Compiler("GNU", debug=False, execute_commands=False)
    monkeypatch.setattr(compiler, "_executable", lambda _language, _tools: "gcc")
    monkeypatch.setitem(compiler._toolchain["c"]["python"], "flags", ("-foreign-python-build-flag",))
    object_file = ObjectFile(
        source=tmp_path / "binding.c",
        object_path=tmp_path / "binding.o",
        language="c",
        tools=frozenset({"python"}),
    )

    compiler.compile_object(object_file)

    command = compiler.command_log[0]
    assert command.count("-O3") == 1
    assert command.count("-DNDEBUG") == 1
    assert "-g" not in command
    assert "-foreign-python-build-flag" not in command


def test_python_include_directories_add_existing_multiarch_root(monkeypatch, tmp_path: Path):
    numpy_headers = tmp_path / "numpy"
    python_headers = tmp_path / "include" / "python3.14"
    delegated = tmp_path / "include" / "x86_64-test" / "python3.14" / "pyconfig.h"
    delegated.parent.mkdir(parents=True)
    delegated.touch()
    monkeypatch.setattr(compiler_profiles, "numpy_include", lambda: str(numpy_headers))

    include_dirs = compiler_profiles._python_include_directories(
        {
            "INCLUDEPY": str(python_headers),
            "MULTIARCH": "x86_64-test",
        }
    )

    assert include_dirs == (
        str(numpy_headers),
        str(python_headers),
        str(tmp_path / "include"),
        str(tmp_path / "include" / "x86_64-test"),
    )


def test_supported_optional_profile_flags_are_used_when_executing(monkeypatch, tmp_path: Path):
    compiler = Compiler("GNU")
    monkeypatch.setattr(compiler, "_executable", lambda _language, _tools: "gfortran")
    monkeypatch.setattr(compiler, "_supports_optional_flag", lambda _executable, flag: flag == "-ftrampoline-impl=heap")
    monkeypatch.setattr(Compiler, "run_command", staticmethod(lambda command, _verbose=False: tuple(command)))
    object_file = ObjectFile(
        source=tmp_path / "bridge.f90",
        object_path=tmp_path / "bridge.o",
        language="fortran",
    )

    compiler.compile_object(object_file)

    assert "-ftrampoline-impl=heap" in compiler.command_log[0]


def test_unsupported_optional_profile_flags_are_omitted(monkeypatch, tmp_path: Path):
    compiler = Compiler("GNU")
    monkeypatch.setattr(compiler, "_executable", lambda _language, _tools: "gfortran")
    monkeypatch.setattr(compiler, "_supports_optional_flag", lambda _executable, _flag: False)
    monkeypatch.setattr(Compiler, "run_command", staticmethod(lambda command, _verbose=False: tuple(command)))
    object_file = ObjectFile(
        source=tmp_path / "bridge.f90",
        object_path=tmp_path / "bridge.o",
        language="fortran",
    )

    compiler.compile_object(object_file)

    assert "-ftrampoline-impl=heap" not in compiler.command_log[0]


def test_optional_profile_flag_probe_reads_the_selected_compiler_help(monkeypatch):
    calls = []

    def completed(command, **kwargs):
        calls.append((command, kwargs))
        return type(
            "Completed",
            (),
            {
                "returncode": 0,
                "stdout": "  -ftrampoline-impl=        stack\n",
                "stderr": "",
            },
        )()

    Compiler._supports_optional_flag.cache_clear()
    monkeypatch.setattr(compiler_module.subprocess, "run", completed)

    assert Compiler._supports_optional_flag("gfortran-test", "-ftrampoline-impl=heap") is True
    assert calls == [
        (
            ("gfortran-test", "-Q", "--help=common"),
            {
                "capture_output": True,
                "text": True,
                "check": False,
            },
        )
    ]


def test_optional_profile_flag_probe_fails_closed_when_the_compiler_cannot_start(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise OSError("missing compiler")

    Compiler._supports_optional_flag.cache_clear()
    monkeypatch.setattr(compiler_module.subprocess, "run", unavailable)

    assert Compiler._supports_optional_flag("missing-gfortran", "-ftrampoline-impl=heap") is False


def test_link_keeps_the_declared_object_and_link_argument_order(monkeypatch, tmp_path: Path):
    compiler = Compiler("GNU", execute_commands=False)
    monkeypatch.setattr(compiler, "_executable", lambda _language, _tools: "gfortran")
    native = ObjectFile(tmp_path / "native.f90", tmp_path / "native.o", "fortran")
    bridge = ObjectFile(tmp_path / "bridge.f90", tmp_path / "bridge.o", "fortran")
    binding = ObjectFile(tmp_path / "binding.c", tmp_path / "binding.o", "c", tools=frozenset({"python"}))

    extension = compiler.link_extension(
        module_name="wrapped",
        output_dir=tmp_path,
        language="fortran",
        objects=(native, bridge, binding),
        link_args=("-Wl,--as-needed", "-lm"),
    )

    command = compiler.command_log[0]
    assert command.index(str(native.object_path)) < command.index(str(bridge.object_path))
    assert command.index(str(bridge.object_path)) < command.index(str(binding.object_path))
    assert command.index(str(binding.object_path)) < command.index("-Wl,--as-needed") < command.index("-lm")
    assert command[command.index("-o") + 1] == str(extension)


def test_builtin_toolchains_keep_c_and_fortran_stage_definitions():
    assert vendors == ("GNU", "intel", "PGI", "nvidia", "LLVM")
    for toolchain in available_compilers.values():
        for language in ("c", "fortran"):
            config = toolchain[language]
            assert config["exec"]
            assert config["debug_flags"]
            assert config["release_flags"]
            assert config["general_flags"]
        assert toolchain["fortran"]["module_output_flag"]
        assert toolchain["c"]["python"]["shared_suffix"]
