  interface convert
    module procedure convert_l
  end interface

contains
  logical function convert_l(x)
    logical, intent(in) :: x
    convert_l = x
  end function convert_l
end module facade_mod
