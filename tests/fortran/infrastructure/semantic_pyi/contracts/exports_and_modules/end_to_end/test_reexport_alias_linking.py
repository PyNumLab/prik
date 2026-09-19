"""A namespace alias reaches its target in a module that publishes nothing else.

Binding an alias calls a bundled native helper, so a module whose only use of
those helpers is the alias still has to carry them. Nothing else in such a
module asks for the support header, which is what made this fail to link.
"""

from pathlib import Path

import pytest

from prik.pipeline.build import build_fortran_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir

pytestmark = pytest.mark.fortran_end_to_end

# Neither procedure takes an argument, returns a result, or touches a derived
# type or module variable, so the alias is the module's only helper use.
HOME = """\
module alias_home
  implicit none
contains
  subroutine target()
  end subroutine target
end module alias_home
"""

FACADE = """\
module alias_facade
  use alias_home, only : lambda => target
  implicit none
  public :: lambda

contains

  subroutine lambda_()
  end subroutine lambda_
end module alias_facade
"""


def test_an_alias_is_the_only_helper_a_module_needs(tmp_path: Path):
    """The alias binds its target, so the module links and both names resolve."""
    home = tmp_path / "alias_home.f90"
    home.write_text(HOME, encoding="utf-8")
    facade = tmp_path / "alias_facade.f90"
    facade.write_text(FACADE, encoding="utf-8")

    result = build_fortran_extension(
        [home, facade],
        output_dir=tmp_path / "build",
        output_name="alias_api",
    )
    module = _import_from_build_dir(result.module_name, result.output_dir)

    published = {name for name in dir(module.alias_facade) if not name.startswith("_")}
    assert published == {"lambda_", "lambda__2"}
    # The module's own declaration keeps the name it would have had, and the
    # imported alias is the one export policy moved aside.
    assert module.alias_facade.lambda_.__name__ == "lambda_"
    assert module.alias_facade.lambda__2 is module.alias_home.target
