module particle_mod
  type :: particle
    integer :: id
    real(kind=8), dimension(3) :: x
  contains
    procedure :: move, reset
  end type particle
contains
subroutine touch(p)
  type(particle), intent(inout) :: p
end subroutine touch
end module particle_mod
