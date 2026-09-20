module store_mod
  implicit none
  integer :: counter = 5
  integer, parameter :: limit = 42
  character(len=8) :: label = 'first   '
  character(len=4) :: tags(2) = ['ab  ', 'cd  ']
  real(8), allocatable :: values(:)
  real(8), pointer :: view(:) => null()
  real(8), target :: backing(4) = [1.0d0, 2.0d0, 3.0d0, 4.0d0]
contains
  subroutine allocate_values(n)
    integer, intent(in) :: n
    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = 1.0d0
  end subroutine allocate_values

  subroutine release_values()
    if (allocated(values)) deallocate(values)
  end subroutine release_values

  subroutine associate_view()
    view => backing
  end subroutine associate_view

  subroutine clear_view()
    view => null()
  end subroutine clear_view

end module store_mod

module facade_mod
  use store_mod, only : counter, limit, label, tags, values, view
  implicit none
  public :: counter, limit, label, tags, values, view
end module facade_mod

module renamed_mod
  use store_mod, only : tally => counter
  implicit none
  public :: tally
end module renamed_mod

module hop_mod
  use renamed_mod, only : tally
  implicit none
  public :: tally
end module hop_mod
