module reexport_home_mod
  implicit none
contains
  subroutine scale_value(value, scaled)
    integer, intent(in) :: value
    integer, intent(out) :: scaled
    scaled = value * 2
  end subroutine scale_value
end module reexport_home_mod

module reexport_facade_mod
  use reexport_home_mod, only : scale_value
  implicit none
  private
  public :: scale_value
end module reexport_facade_mod

module reexport_default_mod
  use reexport_home_mod
  implicit none
end module reexport_default_mod

module reexport_shout_mod
  implicit none
contains
  subroutine SCALE_LOUD(value, scaled)
    integer, intent(in) :: value
    integer, intent(out) :: scaled
    scaled = value * 3
  end subroutine SCALE_LOUD
end module reexport_shout_mod

module reexport_case_mod
  use reexport_shout_mod, only : SCALE_LOUD
  implicit none
  private
  public :: SCALE_LOUD
end module reexport_case_mod

module reexport_renamed_mod
  use reexport_home_mod, only : public_scale => scale_value
  implicit none
  private
  public :: public_scale
end module reexport_renamed_mod

module reexport_wildcard_mod
  use reexport_home_mod
  implicit none
  private
  public :: scale_value
end module reexport_wildcard_mod

module reexport_hop_mod
  use reexport_facade_mod, only : scale_value
  implicit none
  private
  public :: scale_value
end module reexport_hop_mod

module reexport_collide_mod
  implicit none
contains
  subroutine lambda(x)
    integer, intent(inout) :: x
    x = x + 1
  end subroutine lambda
  subroutine lambda_(x)
    integer, intent(inout) :: x
    x = x + 100
  end subroutine lambda_
end module reexport_collide_mod

module reexport_collide_user_mod
  use reexport_collide_mod, only : lambda_
  implicit none
  private
  public :: lambda_
end module reexport_collide_user_mod
