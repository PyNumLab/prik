module arrays_direct_bind_c_f90
  use iso_c_binding
contains
  real(c_double) function sum_values(n, values) bind(C) result(output)
    integer(c_int), value, intent(in) :: n
    real(c_double), intent(in) :: values(n)
    output = sum(values)
  end function sum_values

  subroutine scale_values(n, values) bind(C)
    integer(c_int), value, intent(in) :: n
    real(c_double), intent(inout) :: values(n)
    values = 2.0_c_double * values
  end subroutine scale_values

  logical(c_bool) function all_flags(n, values) bind(C) result(output)
    integer(c_int), value, intent(in) :: n
    logical(c_bool), intent(in) :: values(n)
    output = all(values)
  end function all_flags

  subroutine invert_flags(n, values) bind(C)
    integer(c_int), value, intent(in) :: n
    logical(c_bool), intent(inout) :: values(n)
    values = .not. values
  end subroutine invert_flags

  subroutine scale_matrix(rows, columns, values) bind(C)
    integer(c_int), value, intent(in) :: rows
    integer(c_int), value, intent(in) :: columns
    real(c_double), intent(inout) :: values(rows, columns)

    values = 3.0_c_double * values
  end subroutine scale_matrix
end module arrays_direct_bind_c_f90
