module fmodule_derived_snapshot_f90
  implicit none
  private

  public :: child, box, current
  public :: initialise_current, mutate_current, release_current, current_total

  type :: child
    integer :: id = 0
  end type child

  type :: box
    integer :: scalar = 0
    real(8) :: fixed(2) = [0.0d0, 0.0d0]
    real(8), allocatable :: values(:)
    type(child) :: nested
  contains
    procedure, public :: scalar_plus_nested
  end type box

  type(box) :: current

contains

  integer function scalar_plus_nested(self) result(total)
    class(box), intent(in) :: self

    total = self%scalar + self%nested%id
  end function scalar_plus_nested

  subroutine initialise_current(n)
    integer, intent(in) :: n
    integer :: i

    current%scalar = 7
    current%fixed = [1.5d0, 2.5d0]
    current%nested%id = 11
    if (allocated(current%values)) deallocate(current%values)
    allocate(current%values(n))
    do i = 1, n
      current%values(i) = real(i, kind=8)
    end do
  end subroutine initialise_current

  subroutine mutate_current()
    current%scalar = current%scalar + 10
    current%fixed = current%fixed + 100.0d0
    current%nested%id = current%nested%id + 100
    if (allocated(current%values)) then
      current%values = current%values + 1000.0d0
    end if
  end subroutine mutate_current

  subroutine release_current()
    if (allocated(current%values)) deallocate(current%values)
  end subroutine release_current

  real(8) function current_total() result(total)
    total = real(current%scalar + current%nested%id, kind=8) + sum(current%fixed)
    if (allocated(current%values)) total = total + sum(current%values)
  end function current_total

end module fmodule_derived_snapshot_f90
