
module foptional_f90
  implicit none

  type :: sample
    integer :: value
  end type sample

contains
  integer function summarize(required, scale, values, label, item)
    integer, intent(in) :: required
    integer, intent(in), optional :: scale
    real(8), intent(in), optional :: values(:)
    character(len=*), intent(in), optional :: label
    type(sample), intent(in), optional :: item

    summarize = required
    if (present(scale)) summarize = summarize + scale
    if (present(values)) summarize = summarize + int(sum(values))
    if (present(label)) summarize = summarize + len_trim(label)
    if (present(item)) summarize = summarize + item%value
  end function summarize

  subroutine mutate_optional(values, amount)
    real(8), intent(inout), optional :: values(:)
    real(8), intent(in), optional :: amount

    if (present(values)) then
      if (present(amount)) then
        values = values + amount
      else
        values = values + 1.0_8
      end if
    end if
  end subroutine mutate_optional

  subroutine fill_optional(n, values)
    integer, intent(in) :: n
    real(8), intent(out), optional :: values(:)
    integer :: i

    if (present(values)) then
      do i = 1, n
        values(i) = 10.0_8 + real(i, 8)
      end do
    end if
  end subroutine fill_optional

  integer function optional_status(base, status)
    integer, intent(in) :: base
    integer, intent(out), optional :: status

    optional_status = base
    if (present(status)) status = base + 50
  end function optional_status

  integer function three_optional(first, second, third)
    integer, intent(in), optional :: first, second, third

    three_optional = 0
    if (present(first)) three_optional = three_optional + 1
    if (present(second)) three_optional = three_optional + 2
    if (present(third)) three_optional = three_optional + 4
  end function three_optional
end module foptional_f90
