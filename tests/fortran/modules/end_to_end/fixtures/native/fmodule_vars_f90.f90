module fmodule_vars_f90
  implicit none
  private
  public :: rgb_color, black
  public :: nmax, counter, scale, saved_counter
  public :: summarize, scaled_counter, next_local, black_sum

  type :: rgb_color
    integer(4) :: r
    integer(4) :: g
    integer(4) :: b
  end type rgb_color

  integer(4), parameter :: nmax = 12
  type(rgb_color), parameter :: black = rgb_color(0, 0, 0)
  integer(4) :: counter = 3
  real(8) :: scale = 1.5d0
  integer(4), save :: saved_counter = 6
  integer(4) :: hidden_counter = 17

contains
  integer(4) function summarize() result(value)
    value = counter + nmax
  end function summarize

  real(8) function scaled_counter() result(value)
    value = real(counter, 8) * scale
  end function scaled_counter

  integer(4) function next_local() result(value)
    integer(4), save :: local_counter = 0

    local_counter = local_counter + 1
    value = local_counter
  end function next_local

  integer(4) function black_sum() result(value)
    value = black%r + black%g + black%b
  end function black_sum
end module fmodule_vars_f90
