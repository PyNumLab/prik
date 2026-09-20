module reexport_state_home
  use iso_fortran_env, only: int32, real64
  implicit none

  type :: item
    integer(int32) :: value = 0
  end type item

  integer(int32), parameter :: limit = 7
  integer(int32) :: counter = 3
  integer(int32) :: numbers(3)
  real(real64), allocatable :: values(:)
  real(real64), target :: backing(3)
  real(real64), pointer :: selected(:) => null()
  type(item) :: current
  type(item), allocatable :: optional_item

contains

  subroutine setup()
    numbers = [1, 2, 3]
    if (.not. allocated(values)) allocate(values(3))
    values = [4.0_real64, 5.0_real64, 6.0_real64]
    backing = [7.0_real64, 8.0_real64, 9.0_real64]
    selected => backing
    current%value = 10
    if (.not. allocated(optional_item)) allocate(optional_item)
    optional_item%value = 11
  end subroutine setup
end module reexport_state_home

module reexport_state_facade
  use reexport_state_home, only: limit, counter, numbers, values, selected, current, optional_item
  implicit none
  private
  public :: limit, counter, numbers, values, selected, current, optional_item
end module reexport_state_facade
