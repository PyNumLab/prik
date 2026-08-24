
module fcharacter_edges_f90
  implicit none
contains
  subroutine fixed_inout(name)
    character(len=8), intent(inout) :: name

    name(1:1) = 'Z'
    name(8:8) = '!'
  end subroutine fixed_inout

  subroutine assumed_inout(name)
    character(len=*), intent(inout) :: name

    if (len(name) > 0) name(1:1) = 'Q'
  end subroutine assumed_inout

  subroutine optional_inout(label)
    character(len=*), intent(inout), optional :: label

    if (present(label)) then
      if (len(label) > 0) label(1:1) = 'P'
    end if
  end subroutine optional_inout

  subroutine make_out(label)
    character(len=6), intent(out) :: label

    label = 'go'
  end subroutine make_out

  character(len=5) function unicode_echo(label) result(out)
    character(len=*), intent(in) :: label

    out = label
  end function unicode_echo
end module fcharacter_edges_f90
