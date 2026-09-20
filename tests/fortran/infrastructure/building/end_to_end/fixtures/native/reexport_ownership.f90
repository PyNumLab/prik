module owner_mod
  implicit none
contains
  subroutine scale_twice(value, scaled)
    integer, intent(in) :: value
    integer, intent(out) :: scaled
    scaled = value * 2
  end subroutine scale_twice
end module owner_mod

module facade_mod
  use owner_mod, only : scale_twice
  implicit none
  private
  public :: scale_twice
end module facade_mod

module renaming_mod
  use owner_mod, only : doubled => scale_twice
  implicit none
  private
  public :: doubled
end module renaming_mod
