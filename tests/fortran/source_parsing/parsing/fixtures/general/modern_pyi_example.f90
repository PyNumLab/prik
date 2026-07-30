module modern_math_physics
  implicit none
  private
  public :: particle, vector3, counter, init_particle, kinetic_energy, scale_vector, dot3, fill_identity3, normalize_particle

  integer :: counter
  real(8) :: hidden_scale

  type :: particle
     integer :: id
     real(8) :: mass
     real(8), dimension(3) :: position
  end type particle

  type :: vector3
     real(8), dimension(3) :: values
  end type vector3

  type :: hidden_state
     integer :: code
  end type hidden_state

contains

  subroutine init_particle(p, pid, mass, x, y, z)
    type(particle), intent(out) :: p
    integer, intent(in) :: pid
    real(8), intent(in) :: mass, x, y, z
    p%id = pid
    p%mass = mass
    p%position = [x, y, z]
  end subroutine init_particle

  function kinetic_energy(p, vx, vy, vz) result(e)
    type(particle), intent(in) :: p
    real(8), intent(in) :: vx, vy, vz
    real(8) :: e
    e = 0.5d0 * p%mass * (vx*vx + vy*vy + vz*vz)
  end function kinetic_energy

  subroutine scale_vector(v, alpha)
    real(8), dimension(:), intent(inout) :: v
    real(8), intent(in) :: alpha
    v = alpha * v
  end subroutine scale_vector

  function dot3(a, b) result(s)
    real(8), dimension(3), intent(in) :: a, b
    real(8) :: s
    s = a(1)*b(1) + a(2)*b(2) + a(3)*b(3)
  end function dot3

  subroutine fill_identity3(a)
    real(8), dimension(3,3), intent(out) :: a
    a = 0.0d0
    a(1,1) = 1.0d0
    a(2,2) = 1.0d0
    a(3,3) = 1.0d0
  end subroutine fill_identity3

  subroutine normalize_particle(p)
    type(particle), intent(inout) :: p
    real(8) :: n
    n = sqrt(dot3(p%position, p%position))
    if (n > 0.0d0) p%position = p%position / n
  end subroutine normalize_particle

  subroutine hidden_proc(x)
    integer, intent(in) :: x
  end subroutine hidden_proc

end module modern_math_physics
