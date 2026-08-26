module array_ops
  implicit none
contains
  subroutine scale_matrix(rows, columns, values)
    integer(4), intent(in) :: rows, columns
    real(8), intent(inout) :: values(rows, columns)
    values = 2.0_8 * values
  end subroutine scale_matrix

  subroutine shift(size, values)
    integer(4), intent(in) :: size
    real(8), intent(inout) :: values(0:size-1)
    values = values + 1.0_8
  end subroutine shift

  subroutine sum_columns(size, values, result)
    integer(4), intent(in) :: size
    real(8), intent(in) :: values(size, size)
    real(8), intent(out) :: result(size)
    integer(4) :: column

    do column = 1, size
      result(column) = sum(values(:, column))
    end do
  end subroutine sum_columns

  function sum_flat(count, values) result(total)
    integer(4), intent(in) :: count
    real(8), intent(in) :: values(*)
    real(8) :: total
    integer(4) :: index

    total = 0.0_8
    do index = 1, count
      total = total + values(index)
    end do
  end function sum_flat

  function sum_flat_columns(rows, columns, values) result(total)
    integer(4), intent(in) :: rows, columns
    real(8), intent(in) :: values(rows, *)
    real(8) :: total
    integer(4) :: row, column

    total = 0.0_8
    do column = 1, columns
      do row = 1, rows
        total = total + values(row, column)
      end do
    end do
  end function sum_flat_columns

  subroutine scale_visible_rows(values, out)
    real(8), intent(in) :: values(:, :)
    real(8), intent(out) :: out(:, :)
    out = 3.0_8 * values
  end subroutine scale_visible_rows

  subroutine scale_without_intent(values)
    real(8) :: values(:)
    values = 2.0_8 * values
  end subroutine scale_without_intent

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
    integer(4), intent(in) :: n
    real(8), intent(out), optional :: values(:)
    integer(4) :: i
    if (present(values)) then
      do i = 1, n
        values(i) = 10.0_8 + real(i, 8)
      end do
    end if
  end subroutine fill_optional

  function automatic_vector(count) result(values)
    integer(4), intent(in) :: count
    real(8) :: values(count)
    integer(4) :: i
    values = [(2.0_8 * i, i = 1, count)]
  end function automatic_vector
end module array_ops
