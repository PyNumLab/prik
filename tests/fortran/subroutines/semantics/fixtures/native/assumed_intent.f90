module legacy
  type :: pt
    real(8) :: x = 0.0d0
  end type pt
contains
subroutine touch(count, item, values, label, declared)
    integer(4) :: count
    type(pt) :: item
    real(8) :: values(:)
    character(len=4) :: label
    integer(4), intent(inout) :: declared
    count = count + 1
    item%x = item%x + 1.0d0
    values = values * 2.0d0
    label = "zzzz"
    declared = declared + 1
end subroutine touch
end module legacy
