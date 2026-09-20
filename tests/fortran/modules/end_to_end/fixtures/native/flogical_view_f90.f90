module flogical_view_f90
  use iso_c_binding, only: c_bool
  implicit none

  logical(c_bool) :: narrow(4)
  logical :: wide(4)
  logical(c_bool), allocatable :: narrow_alloc(:)
  logical, allocatable :: wide_alloc(:)
  logical, target :: wide_store(4)
  logical, pointer :: wide_pointer(:) => null()

contains

  subroutine setup()
    narrow = [.true., .false., .true., .false.]
    wide = [.true., .false., .true., .false.]
    if (.not. allocated(narrow_alloc)) allocate(narrow_alloc(4))
    narrow_alloc = [.true., .true., .false., .false.]
    if (.not. allocated(wide_alloc)) allocate(wide_alloc(4))
    wide_alloc = [.true., .false., .true., .false.]
    wide_store = [.true., .false., .true., .false.]
    wide_pointer => wide_store
  end subroutine setup

  subroutine negate()
    narrow = .not. narrow
    wide = .not. wide
  end subroutine negate

  function count_narrow() result(total)
    integer :: total
    total = count(narrow)
  end function count_narrow

  function count_wide() result(total)
    integer :: total
    total = count(wide)
  end function count_wide

  function count_narrow_actual(values) result(total)
    logical(c_bool), intent(in) :: values(:)
    integer :: total
    total = count(values)
  end function count_narrow_actual

  function count_wide_actual(values) result(total)
    logical, intent(in) :: values(:)
    integer :: total
    total = count(values)
  end function count_wide_actual
end module flogical_view_f90
