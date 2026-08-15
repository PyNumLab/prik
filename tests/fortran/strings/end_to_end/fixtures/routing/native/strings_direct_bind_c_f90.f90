module strings_direct_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function direct_char_code(ch) bind(C) result(code)
    character(kind=c_char), value, intent(in) :: ch

    code = iachar(ch, c_int)
  end function direct_char_code

  subroutine direct_uppercase(ch) bind(C)
    character(kind=c_char), intent(inout) :: ch

    if (ch >= 'a' .and. ch <= 'z') ch = achar(iachar(ch) - 32, kind=c_char)
  end subroutine direct_uppercase

  integer(c_int) function direct_buffer_sum(n, text) bind(C) result(total)
    integer(c_int), value, intent(in) :: n
    character(kind=c_char), intent(in) :: text(n)
    integer :: index

    total = 0_c_int
    do index = 1, n
      total = total + iachar(text(index), c_int)
    end do
  end function direct_buffer_sum

  subroutine direct_uppercase_buffer(n, text) bind(C)
    integer(c_int), value, intent(in) :: n
    character(kind=c_char), intent(inout) :: text(n)
    integer :: index

    do index = 1, n
      if (text(index) >= 'a' .and. text(index) <= 'z') then
        text(index) = achar(iachar(text(index)) - 32, kind=c_char)
      end if
    end do
  end subroutine direct_uppercase_buffer
end module strings_direct_bind_c_f90
