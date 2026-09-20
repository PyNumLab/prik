module checked_extent_provider
  implicit none
contains
  pure integer function extent_for(n)
    integer, intent(in) :: n
    extent_for = n + 1
  end function extent_for
end module checked_extent_provider

module checked_extent_owner
  use, intrinsic :: iso_c_binding, only: c_double
  use checked_extent_provider, only: extent_for
  implicit none
contains
  subroutine fill(n, values)
    integer, intent(in) :: n
    real(c_double), intent(out) :: values(extent_for(n))
    values = 2.0_c_double
  end subroutine fill
  real(c_double) function total(n, values)
    integer, intent(in) :: n
    real(c_double), intent(in) :: values(extent_for(n))
    total = sum(values)
  end function total
  subroutine maybe_fill(n, values)
    integer, intent(in) :: n
    real(c_double), intent(inout), optional :: values(extent_for(n))
    if (present(values)) values = 5.0_c_double
  end subroutine maybe_fill
end module checked_extent_owner
