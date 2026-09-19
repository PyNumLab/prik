"""A build names a type once, however many of its modules use it.

A build merges its source modules into one, so a type one of them imports from
another is declared by the merged module itself. It is not an import there,
and it must not compete with its own declaration for a name.
"""

from pathlib import Path

from prik.parsers.fortran import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.policy.exports import complete_python_export_policy
from prik.semantics import models
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules

SOURCES = """\
module shapes
  implicit none
  type :: box
    integer :: value = 0
  end type box
end module shapes

module ops
  use shapes, only: box
  implicit none
  private
  public :: boxed
contains
  function boxed(v) result(out)
    integer, intent(in) :: v
    type(box) :: out
    out%value = v
  end function boxed
end module ops
"""


def test_a_merged_build_names_a_type_its_modules_share_once(tmp_path: Path):
    """Named like the module declaring the type, the build still spells it `Box`.

    `ops` uses `box` without publishing it. Counting that use as an import put
    a second `Box` in the ledger ahead of the declaration, which took `Box_2`.
    """
    (tmp_path / "project.f90").write_text(SOURCES, encoding="utf-8")
    modules = fortran_project_to_semantic_modules(parse_fortran_project(str(tmp_path)))
    _apply_source_python_exports(modules)
    merged = _merge_wrapper_modules(modules, name="shapes")

    complete_python_export_policy(merged)

    box = next(item for item in merged.classes if item.name == "box")
    boxed = next(item for item in merged.functions if item.name == "boxed")
    assert models.completed_contract_name(box) == "Box"
    assert boxed.return_type.metadata[models.CONTRACT_NAME_METADATA] == "Box"
    assert "box" not in merged.metadata[models.CONTRACT_IMPORT_NAMES_METADATA]
