module callbacks_mixed_bind_c_f90
  use iso_c_binding
  implicit none

  abstract interface
    real(c_double) function direct_callback(value) bind(C) result(output)
      import c_double
      real(c_double), value, intent(in) :: value
    end function direct_callback

    real(c_double) function adapted_callback(value) result(output)
      import c_double
      real(c_double), intent(in) :: value
    end function adapted_callback
  end interface
contains
  real(c_double) function direct_apply(callback, value) bind(C) result(output)
    procedure(direct_callback) :: callback
    real(c_double), value, intent(in) :: value

    output = callback(value)
  end function direct_apply

  real(c_double) function adapted_apply(callback, value) result(output)
    procedure(adapted_callback) :: callback
    real(c_double), intent(in) :: value

    output = callback(value)
  end function adapted_apply
end module callbacks_mixed_bind_c_f90
