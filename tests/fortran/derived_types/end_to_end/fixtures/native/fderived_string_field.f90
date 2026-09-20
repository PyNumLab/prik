module derived_string_fields
  implicit none

  type :: record
    character(len=8) :: label = 'start   '
  end type record

  type(record), target :: current
contains
  function current_label() result(value)
    character(len=8) :: value
    value = current%label
  end function current_label

  subroutine reset_label()
    current%label = 'native  '
  end subroutine reset_label
end module derived_string_fields
