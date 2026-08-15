module strings_mixed_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function direct_char_code(ch) bind(C) result(code)
    character(kind=c_char), value, intent(in) :: ch

    code = iachar(ch, c_int)
  end function direct_char_code

  integer(c_int) function adapted_fixed_code(text) result(code)
    character(len=4), intent(in) :: text

    code = iachar(text(1:1), c_int)
  end function adapted_fixed_code
end module strings_mixed_bind_c_f90
