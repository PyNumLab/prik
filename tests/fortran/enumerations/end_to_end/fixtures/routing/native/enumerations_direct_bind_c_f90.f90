module enumerations_direct_bind_c_f90
  use iso_c_binding
  implicit none

  enum, bind(C)
    enumerator :: stopped = -1, ready, running = 4
  end enum

  integer(c_int), parameter :: terminal = 5
contains
  integer(c_int) function direct_round_trip(state) bind(C) result(output)
    integer(c_int), value, intent(in) :: state

    output = state
  end function direct_round_trip

  subroutine direct_next(state, output) bind(C)
    integer(c_int), value, intent(in) :: state
    integer(c_int), intent(out) :: output

    output = state + 1_c_int
  end subroutine direct_next
end module enumerations_direct_bind_c_f90
