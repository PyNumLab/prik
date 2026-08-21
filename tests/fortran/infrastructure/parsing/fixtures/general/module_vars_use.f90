module constants_mod
  use iso_c_binding, only: c_int, c_double
  integer(kind=c_int), parameter :: nmax = 100
  real(kind=c_double), dimension(3) :: origin
end module constants_mod
