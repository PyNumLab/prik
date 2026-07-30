module fstrings_f90
  use iso_c_binding, only: c_char
  implicit none
contains
  integer function char_code_default(c)
    character, intent(in) :: c
    char_code_default = ichar(c)
  end function char_code_default

  integer function char_code_len1(c)
    character(len=1), intent(in) :: c
    char_code_len1 = ichar(c)
  end function char_code_len1

  integer function char_code_kind1(c)
    character(kind=1), intent(in) :: c
    char_code_kind1 = ichar(c)
  end function char_code_kind1

  integer function char_code_c_char(c)
    character(kind=c_char), intent(in) :: c
    char_code_c_char = ichar(c)
  end function char_code_c_char

  integer function string_len_fixed(text)
    character(len=8), intent(in) :: text
    string_len_fixed = len_trim(text)
  end function string_len_fixed

  integer function string_len_assumed(text)
    character(len=*), intent(in) :: text
    string_len_assumed = len(text)
  end function string_len_assumed

  integer function string_len_c_char(text)
    character(len=8, kind=c_char), intent(in) :: text
    string_len_c_char = len_trim(text)
  end function string_len_c_char

  character function char_result_default()
    char_result_default = 'M'
  end function char_result_default

  function char_result_c_char() result(value)
    character(kind=c_char) :: value
    value = 'C'
  end function char_result_c_char

  function string_result_fixed() result(value)
    character(len=8) :: value
    value = 'MODERN!!'
  end function string_result_fixed

  function string_result_padded() result(value)
    character(len=8) :: value
    value = 'PAD'
  end function string_result_padded

  function string_result_c_char() result(value)
    character(len=8, kind=c_char) :: value
    value = 'C-CHAR!!'
  end function string_result_c_char

  subroutine string_result_deferred(text, value)
    character(len=*), intent(in) :: text
    character(len=:), allocatable, intent(out) :: value
    value = trim(text) // '-deferred'
  end subroutine string_result_deferred

  integer function fixed_array_extent(labels)
    character(len=8), intent(in) :: labels(:)
    if (size(labels) == 0) then
      fixed_array_extent = 0
    else
      fixed_array_extent = len(labels(1)) * size(labels)
    end if
  end function fixed_array_extent

  subroutine replace_names(names)
    character(len=:), allocatable, intent(inout) :: names(:)
    integer :: n

    if (allocated(names)) then
      n = size(names)
    else
      n = 2
    end if

    if (allocated(names)) deallocate(names)
    allocate(character(len=5) :: names(n))
    names = '     '
    if (n >= 1) names(1) = 'red'
    if (n >= 2) names(2) = 'blue'
  end subroutine replace_names

  subroutine rewrite_storage(label)
    character(len=8), intent(inout) :: label
    label(1:1) = 'Y'
    label(8:8) = '?'
  end subroutine rewrite_storage
end module fstrings_f90
