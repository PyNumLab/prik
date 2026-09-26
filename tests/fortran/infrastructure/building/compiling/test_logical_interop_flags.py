from pathlib import Path

import pytest

from prik.compiler.compilers import Compiler
from prik.compiler.objects import ObjectFile


LOGICAL_OPTIONS = ("-standard-semantics", "-Munixlogical")


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
    ("vendor", "expected"),
    [
        ("intel", ("-standard-semantics",)),
        ("PGI", ("-Munixlogical",)),
        ("nvidia", ("-Munixlogical",)),
        ("GNU", ()),
        ("LLVM", ()),
    ],
)
def test_vendor_logical_interop_option_is_on_by_default_and_can_be_turned_off(
    vendor: str, expected: tuple[str, ...], tmp_path: Path
):
    """A logical must reach C as 0 or 1, so the vendor option is on without being asked for.

    gfortran and Flang already store .true. as 1, so they stay flag-free. Opting
    out is the only way to link objects built without the option, whose mangling
    differs, and it also clears the flags external builds are told to use.
    """
    default_command = _fortran_compile_command(vendor, standard_logicals=True, tmp_path=tmp_path)
    assert tuple(option for option in LOGICAL_OPTIONS if option in default_command) == expected
    default_compiler = Compiler(vendor, execute_commands=False)
    assert default_compiler.required_abi_flags("fortran") == expected
    assert default_compiler.required_abi_flags("c") == ()

    disabled_command = _fortran_compile_command(vendor, standard_logicals=False, tmp_path=tmp_path)
    assert not any(option in disabled_command for option in LOGICAL_OPTIONS)
    assert Compiler(vendor, execute_commands=False, standard_logicals=False).required_abi_flags("fortran") == ()
