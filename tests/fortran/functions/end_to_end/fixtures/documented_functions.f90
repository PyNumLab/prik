module documented_functions
  implicit none
contains
  real(8) function scale(value, factor) result(output)
    real(8), intent(in) :: value
    real(8), intent(in) :: factor
    output = value * factor
  end function scale

  real(8) function sum_with_count(values, count) result(total)
    real(8), intent(in) :: values(:)
    integer(4), intent(out) :: count
    total = sum(values)
    count = size(values)
  end function sum_with_count

  real(8) function fill_and_sum(count, values) result(total)
    integer(4), intent(in) :: count
    real(8), intent(out) :: values(count)
    integer(4) :: index
    do index = 1, count
      values(index) = real(index, kind=8)
    end do
    total = sum(values)
  end function fill_and_sum

  real(8) function square_no_intent(value) result(output)
    real(8) :: value
    value = value + 1.0_8
    output = value * value
  end function square_no_intent

  function automatic_vector(count) result(values)
    integer(4), intent(in) :: count
    real(8) :: values(count)
    integer(4) :: index
    values = [(real(index * index, kind=8), index = 1, count)]
  end function automatic_vector
end module documented_functions
