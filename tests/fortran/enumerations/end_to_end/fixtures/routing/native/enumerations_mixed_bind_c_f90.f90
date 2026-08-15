module enumerations_mixed_bind_c_f90
  use iso_c_binding
  implicit none

  enum, bind(C)
    enumerator :: stopped = -1, ready, running = 4
  end enum
contains
  integer(c_int) function direct_round_trip(state) bind(C) result(output)
    integer(c_int), value, intent(in) :: state

    output = state
  end function direct_round_trip

  integer(c_int) function adapted_next(state) result(output)
    integer(c_int), intent(in) :: state

    output = state + 1_c_int
  end function adapted_next
end module enumerations_mixed_bind_c_f90
