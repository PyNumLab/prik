function scale_integer(value) result(output)
  implicit none
  integer, intent(in) :: value
  integer :: output
  output = 2 * value
end function scale_integer

function scale_real(value) result(output)
  implicit none
  real(8), intent(in) :: value
  real(8) :: output
  output = 2.5_8 * value
end function scale_real
