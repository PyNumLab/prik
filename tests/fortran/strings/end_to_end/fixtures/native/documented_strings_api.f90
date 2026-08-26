module documented_strings_api
  implicit none
contains
  subroutine edit_text(text)
    character(len=8), intent(inout) :: text
    text(1:1) = "X"
  end subroutine edit_text

  subroutine edit_buffer(text)
    character(len=8), intent(inout) :: text
    text(1:1) = "X"
  end subroutine edit_buffer

  function make_text() result(text)
    character(len=8) :: text
    text = "ready"
  end function make_text

  function make_labels() result(labels)
    character(len=8) :: labels(2)
    labels = [character(len=8) :: "alpha", "beta"]
  end function make_labels

  subroutine edit_labels(count, labels)
    integer(4), intent(in) :: count
    character(len=8), intent(inout) :: labels(count)
    integer(4) :: index
    do index = 1, count
      labels(index)(1:1) = "X"
    end do
  end subroutine edit_labels
end module documented_strings_api
