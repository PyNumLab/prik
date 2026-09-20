module generic_home
  implicit none
  interface convert
    module procedure convert_i
    module procedure convert_r
  end interface convert
contains
  integer function convert_i(value)
    integer, intent(in) :: value
    convert_i = value
  end function convert_i
  real function convert_r(value)
    real, intent(in) :: value
    convert_r = value
  end function convert_r
end module generic_home

module b_mod
  use generic_home
  implicit none
end module b_mod
