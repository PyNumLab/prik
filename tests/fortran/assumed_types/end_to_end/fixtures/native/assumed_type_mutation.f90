subroutine bump_address(x) bind(C)
  type(*), dimension(*), intent(inout) :: x
end subroutine

subroutine bump_descriptor(x) bind(C)
  type(*), dimension(:), intent(inout) :: x
end subroutine

subroutine bump_scalar(x) bind(C)
  type(*), intent(inout) :: x
end subroutine
