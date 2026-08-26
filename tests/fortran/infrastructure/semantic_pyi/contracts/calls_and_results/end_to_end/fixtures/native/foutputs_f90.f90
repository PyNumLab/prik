module foutputs_f90
  implicit none
  private

  public :: scalar_status
  public :: fill_vector, fill_matrix
  public :: build_alloc
  public :: with_scalar, mixed_outputs
  public :: increment, increment_with_status
  public :: output_point
  public :: make_label, make_point

  type :: output_point
    real(8) :: x
    integer :: tag
  end type output_point

contains

  subroutine scalar_status(n, status)
    integer, intent(in) :: n
    integer, intent(out) :: status

    status = n + 10
  end subroutine scalar_status

  subroutine fill_vector(n, values)
    integer, intent(in) :: n
    real(8), intent(out) :: values(n)
    integer :: i

    do i = 1, n
      values(i) = real(i * 2, kind=8)
    end do
  end subroutine fill_vector

  subroutine fill_matrix(n, m, values)
    integer, intent(in) :: n
    integer, intent(in) :: m
    real(8), intent(out) :: values(n, m)
    integer :: i
    integer :: j

    do j = 1, m
      do i = 1, n
        values(i, j) = real(i + 10 * j, kind=8)
      end do
    end do
  end subroutine fill_matrix

  subroutine build_alloc(n, values)
    integer, intent(in) :: n
    real(8), allocatable, intent(out) :: values(:)
    integer :: i

    if (n <= 0) return
    allocate(values(n))
    do i = 1, n
      values(i) = real(i * 3, kind=8)
    end do
  end subroutine build_alloc

  integer function with_scalar(n, status) result(total)
    integer, intent(in) :: n
    integer, intent(out) :: status

    total = n * 2
    status = n + 3
  end function with_scalar

  real(8) function mixed_outputs(n, values, status, built) result(total)
    integer, intent(in) :: n
    real(8), intent(out) :: values(n)
    integer, intent(out) :: status
    real(8), allocatable, intent(out) :: built(:)
    integer :: i

    total = real(n, kind=8) + 0.5d0
    do i = 1, n
      values(i) = real(100 + i, kind=8)
    end do
    status = n + 20
    if (n <= 0) return
    allocate(built(n))
    do i = 1, n
      built(i) = real(200 + i, kind=8)
    end do
  end function mixed_outputs

  subroutine increment(values)
    real(8), intent(inout) :: values(:)

    values = values + 1.0d0
  end subroutine increment

  subroutine increment_with_status(values, status)
    real(8), intent(inout) :: values(:)
    integer, intent(out) :: status

    values = values + 2.0d0
    status = size(values)
  end subroutine increment_with_status

  subroutine make_label(label)
    character(len=8), intent(out) :: label

    label = "RESULT!!"
  end subroutine make_label

  subroutine make_point(scale, point)
    integer, intent(in) :: scale
    type(output_point), intent(out) :: point

    point%x = real(scale, kind=8) + 0.25d0
    point%tag = scale + 40
  end subroutine make_point

end module foutputs_f90
