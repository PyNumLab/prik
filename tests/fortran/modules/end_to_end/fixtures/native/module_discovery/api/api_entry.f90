module api
  use api_types
  implicit none
contains
  subroutine touch(h)
    type(handle_t), intent(inout) :: h
    h%val = h%val + 1
  end subroutine touch
end module api
