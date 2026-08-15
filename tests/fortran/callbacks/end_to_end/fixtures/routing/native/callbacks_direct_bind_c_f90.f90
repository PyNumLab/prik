module callbacks_direct_bind_c_f90
  use iso_c_binding
  implicit none

  abstract interface
    real(c_double) function direct_callback(value) bind(C) result(output)
      import c_double
      real(c_double), value, intent(in) :: value
    end function direct_callback

    subroutine direct_notify(value) bind(C)
      import c_int
      integer(c_int), value, intent(in) :: value
    end subroutine direct_notify
  end interface
contains
  real(c_double) function direct_apply(callback, value) bind(C) result(output)
    procedure(direct_callback) :: callback
    real(c_double), value, intent(in) :: value

    output = callback(value)
  end function direct_apply

  subroutine direct_call_notify(callback, value) bind(C)
    procedure(direct_notify) :: callback
    integer(c_int), value, intent(in) :: value

    call callback(value)
  end subroutine direct_call_notify
end module callbacks_direct_bind_c_f90
