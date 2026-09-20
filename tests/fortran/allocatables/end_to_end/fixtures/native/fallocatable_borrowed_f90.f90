module fallocatable_borrowed_f90
  implicit none
  type :: box
    real(8), allocatable :: field(:)
  end type box
  real(8), allocatable :: modvar(:)
  type(box) :: thebox
contains
  subroutine grow(values)
    real(8), allocatable, intent(inout) :: values(:)

    if (allocated(values)) deallocate(values)
    allocate(values(6))
    values = 9.0_8
  end subroutine grow

  function total(values) result(sum_out)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: sum_out

    sum_out = sum(values)
  end function total

  function make(n) result(values)
    integer(4), intent(in) :: n
    real(8), allocatable :: values(:)
    integer(4) :: i

    allocate(values(n))
    values = [(1.0_8 * i, i = 1, n)]
  end function make
end module fallocatable_borrowed_f90
