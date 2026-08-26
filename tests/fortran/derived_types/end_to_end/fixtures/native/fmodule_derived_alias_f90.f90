module fmodule_derived_alias_f90
  implicit none
  private

  public :: box, current
  public :: allocate_current, deallocate_current, current_sum

  type :: box
    real(8), allocatable :: values(:)
  contains
    procedure, public :: allocate_values
    procedure, public :: values_sum
  end type box

  type(box), target :: current

contains

  subroutine allocate_values(self, n)
    class(box), intent(inout) :: self
    integer, intent(in) :: n
    integer :: i

    if (allocated(self%values)) deallocate(self%values)
    allocate(self%values(n))
    do i = 1, n
      self%values(i) = real(i, kind=8)
    end do
  end subroutine allocate_values

  real(8) function values_sum(self) result(total)
    class(box), intent(in) :: self

    if (allocated(self%values)) then
      total = sum(self%values)
    else
      total = -1.0d0
    end if
  end function values_sum

  subroutine allocate_current(n)
    integer, intent(in) :: n

    call current%allocate_values(n)
  end subroutine allocate_current

  subroutine deallocate_current()
    if (allocated(current%values)) deallocate(current%values)
  end subroutine deallocate_current

  real(8) function current_sum() result(total)
    total = current%values_sum()
  end function current_sum

end module fmodule_derived_alias_f90
