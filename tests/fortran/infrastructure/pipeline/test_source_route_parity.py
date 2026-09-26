"""A build and ``prik generate`` turn the same Fortran sources into the same modules.

Both read, parse, measure, convert, and select through one source route, so
the contract generated from a project describes what a build of it wraps.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from prik import cli as prik_cli
from prik.pipeline.build import _fortran_wrapper_module
from prik.preprocessing import PreprocessingConfig

USER = """module user
  use kinds, only: wp
  implicit none
contains
  subroutine scale(x, factor)
    real(wp), intent(inout) :: x
    real(wp), intent(in) :: factor
    x = x * factor
  end subroutine scale
  subroutine hidden()
  end subroutine hidden
end module user
"""
KINDS = "module kinds\n  integer, parameter :: wp = 8\nend module kinds\n"


def _shape(modules) -> dict[str, list[tuple[str, list[str | None]]]]:
    """Return each module's functions with their argument kinds."""
    return {
        module.name: [
            (function.name, [argument.semantic_type.name for argument in function.arguments])
            for function in module.functions
        ]
        for module in modules
    }


@pytest.mark.parametrize("exports", [None, ("user::scale",)], ids=["whole-project", "selected"])
def test_generate_and_build_convert_sources_named_out_of_order_alike(tmp_path: Path, exports):
    user = tmp_path / "user.f90"
    user.write_text(USER, encoding="utf-8")
    kinds = tmp_path / "kinds.f90"
    kinds.write_text(KINDS, encoding="utf-8")
    sources = (user, kinds)
    preprocessing = PreprocessingConfig()

    generated = prik_cli._converted_semantic_files(
        [str(path) for path in sources],
        preprocessing,
        language="fortran",
        export_symbols=exports,
    )
    _parsed, _module, built, _dependencies = _fortran_wrapper_module(
        sources,
        preprocessing=preprocessing,
        type_probe_preprocessing=preprocessing,
        output_name="parity",
        fortran_type_report=None,
        fortran_type_probe_runner=None,
        fortran_type_probe_cache_dir=None,
        refresh_fortran_type_probe=False,
        export_symbols=exports,
    )

    assert _shape(generated.available_modules) == _shape(built)
    assert ("scale", ["Float64", "Float64"]) in _shape(built)["user"]
