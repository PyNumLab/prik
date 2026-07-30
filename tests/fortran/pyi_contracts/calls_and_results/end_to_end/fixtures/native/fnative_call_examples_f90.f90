module fnative_call_examples_f90
  implicit none
  private

  public :: scalar_status
  public :: fill_vector, shift_matrix, scale_with_status
  public :: fixed_inout, make_label
  public :: summarize_mixed
  public :: summary_point, make_point

  type :: summary_point
    real(8) :: total
    integer :: code
  end type summary_point

contains

  subroutine scalar_status(base, status)
    integer, intent(in) :: base
    integer, intent(out) :: status

    status = base + 11
  end subroutine scalar_status

  subroutine fill_vector(n, values)
    integer, intent(in) :: n
    real(8), intent(out) :: values(n)
    integer :: i

    do i = 1, n
      values(i) = real(i, kind=8) * 1.5d0
    end do
  end subroutine fill_vector

  subroutine shift_matrix(n, m, values, out)
    integer, intent(in) :: n
    integer, intent(in) :: m
    real(8), intent(in) :: values(n, m)
    real(8), intent(out) :: out(n, m)

    out = values + 10.0d0
  end subroutine shift_matrix

  subroutine scale_with_status(values, status)
    real(8), intent(inout) :: values(:)
    integer, intent(out) :: status

    values = values * 2.0d0
    status = size(values)
  end subroutine scale_with_status

  subroutine fixed_inout(label)
    character(len=8), intent(inout) :: label

    label(1:1) = 'X'
    label(8:8) = '!'
  end subroutine fixed_inout

  subroutine make_label(label)
    character(len=6), intent(out) :: label

    label = 'done'
  end subroutine make_label

  real(8) function summarize_mixed(n, values, status, label) result(total)
    integer, intent(in) :: n
    real(8), intent(out) :: values(n)
    integer, intent(out) :: status
    character(len=6), intent(out) :: label
    integer :: i

    total = real(n, kind=8) + 0.75d0
    do i = 1, n
      values(i) = real(10 + i, kind=8)
    end do
    status = n + 20
    label = 'mix'
  end function summarize_mixed

  subroutine make_point(scale, point)
    integer, intent(in) :: scale
    type(summary_point), intent(out) :: point

    point%total = real(scale, kind=8) + 0.5d0
    point%code = scale + 100
  end subroutine make_point

end module fnative_call_examples_f90
