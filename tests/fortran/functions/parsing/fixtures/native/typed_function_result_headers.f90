module typed_result_mod
  type :: point
    real :: x
  end type point
contains
  type(point) function make_point()
  end function make_point

  class(point), pointer function current_point()
  end function current_point

  character(len=8) function label_name()
  end function label_name

  real(8) function weighted_value()
  end function weighted_value

  double precision function norm2()
  end function norm2

  double complex function complex_norm2()
  end function complex_norm2
end module typed_result_mod
