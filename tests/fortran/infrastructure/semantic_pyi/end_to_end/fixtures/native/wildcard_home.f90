module wild_home
  implicit none
contains
  subroutine one(value, out)
    integer, intent(in) :: value
    integer, intent(out) :: out
    out = value + 1
  end subroutine one
  subroutine two(value, out)
    integer, intent(in) :: value
    integer, intent(out) :: out
    out = value + 2
  end subroutine two
end module wild_home
