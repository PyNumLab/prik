module reserved_extent_owner
  use, intrinsic :: iso_c_binding, only: c_double
  use reserved_extent_provider, only: lambda, lambda_
  implicit none
contains
  function keyword_values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(lambda(n))
    output = 1.0_c_double
  end function keyword_values
  function collided_values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(2*lambda_(n) + n)
    output = 2.0_c_double
  end function collided_values
end module reserved_extent_owner
