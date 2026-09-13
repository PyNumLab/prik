from pathlib import Path

import pytest

from prik.compiler.compilers import Compiler
from prik.compiler.objects import ObjectFile


def _fortran_compile_command(vendor: str, *, standard_logicals: bool, tmp_path: Path) -> tuple[str, ...]:
    compiler = Compiler(vendor, execute_commands=False, standard_logicals=standard_logicals)
    compiler._executable = lambda _language, _tools: "fc"
    compiler.compile_object(
        ObjectFile(
            source=tmp_path / "module.f90",
            object_path=tmp_path / "module.o",
            language="fortran",
        )
    )
    return compiler.command_log[0]


@pytest.mark.parametrize(
    ("vendor", "option"),
    [("intel", "-standard-semantics"), ("PGI", "-Munixlogical"), ("nvidia", "-Munixlogical")],
)
def test_fortran_compilation_requests_the_interoperable_logical_by_default(vendor: str, option: str, tmp_path: Path):
    """A logical must reach C as 0 or 1, so the vendor option is on without being asked for."""
    assert option in _fortran_compile_command(vendor, standard_logicals=True, tmp_path=tmp_path)


@pytest.mark.parametrize(
    ("vendor", "option"),
    [("intel", "-standard-semantics"), ("PGI", "-Munixlogical"), ("nvidia", "-Munixlogical")],
)
def test_standard_logicals_can_be_turned_off_for_prebuilt_objects(vendor: str, option: str, tmp_path: Path):
    """Opting out is the only way to link objects built without the option, whose mangling differs."""
    assert option not in _fortran_compile_command(vendor, standard_logicals=False, tmp_path=tmp_path)


@pytest.mark.parametrize("vendor", ["GNU", "LLVM"])
def test_compilers_that_already_interoperate_add_no_logical_option(vendor: str, tmp_path: Path):
    """gfortran and Flang already store .true. as 1, so they must stay flag-free."""
    command = _fortran_compile_command(vendor, standard_logicals=True, tmp_path=tmp_path)
    assert "-standard-semantics" not in command
    assert "-Munixlogical" not in command


@pytest.mark.parametrize(
    ("vendor", "expected"),
    [
        ("intel", ("-standard-semantics",)),
        ("PGI", ("-Munixlogical",)),
        ("nvidia", ("-Munixlogical",)),
        ("GNU", ()),
    ],
)
def test_compiler_exposes_required_logical_abi_flags_for_external_builds(vendor: str, expected: tuple[str, ...]):
    compiler = Compiler(vendor, execute_commands=False)

    assert compiler.required_abi_flags("fortran") == expected
    assert compiler.required_abi_flags("c") == ()


def test_external_build_can_disable_required_logical_abi_flags():
    compiler = Compiler("intel", execute_commands=False, standard_logicals=False)

    assert compiler.required_abi_flags("fortran") == ()
