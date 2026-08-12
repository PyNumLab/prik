from prik.parsers.fortran import parse_fortran_file


def test_module_symbol_tables_keep_derived_type_fields_scoped_to_type():
    code = """
module sparse_types
  implicit none

  type sf_sparse_dmatrix_coo
     integer,dimension(:),allocatable :: rows
     integer,dimension(:),allocatable :: cols
     real(8),dimension(:),allocatable :: vals
  end type sf_sparse_dmatrix_coo

  type sf_sparse_cmatrix_coo
     integer,dimension(:),allocatable :: rows
     integer,dimension(:),allocatable :: cols
     complex(8),dimension(:),allocatable :: vals
  end type sf_sparse_cmatrix_coo

  integer :: module_counter
end module sparse_types
"""
    parsed = parse_fortran_file(code, filename="scope_types_scoped.f90")
    module = parsed.modules[0]

    assert {v.name for v in module.variables} == {"module_counter"}
    assert set(parsed.symbols) == {"sparse_types"}
    assert [t.name for t in module.derived_types] == ["sf_sparse_dmatrix_coo", "sf_sparse_cmatrix_coo"]
    assert {f.name for f in module.derived_types[0].fields} == {"rows", "cols", "vals"}
    assert {f.name for f in module.derived_types[1].fields} == {"rows", "cols", "vals"}


def test_legacy_type_header_without_double_colon_is_scoped_as_derived_type():
    code = """
module legacy_type_header
  implicit none
  type sf_sparse_dmatrix_coo
     real(8),dimension(:),allocatable :: vals
  end type sf_sparse_dmatrix_coo
end module legacy_type_header
"""
    parsed = parse_fortran_file(code, filename="scope_legacy_type_header.f90")
    module = parsed.modules[0]

    assert list(module.variables) == []
    assert [t.name for t in module.derived_types] == ["sf_sparse_dmatrix_coo"]
    assert {f.name for f in module.derived_types[0].fields} == {"vals"}


def test_same_derived_type_name_is_allowed_in_different_module_scopes():
    code = """
module left_mod
  type :: state
    integer :: left
  end type state
end module left_mod

module right_mod
  type :: state
    integer :: right
  end type state
end module right_mod
"""
    parsed = parse_fortran_file(code, filename="scope_same_type_names_ok.f90")

    assert [module.name for module in parsed.modules] == ["left_mod", "right_mod"]
    assert [module.derived_types[0].name for module in parsed.modules] == ["state", "state"]
