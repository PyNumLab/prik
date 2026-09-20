module parameter_array_constants_f90
  use iso_fortran_env, only: real64
  implicit none
  real(real64), parameter :: dpmpar(3) = [epsilon(1.0_real64), tiny(1.0_real64), huge(1.0_real64)]
contains
  function parameter_sum() result(value)
    real(real64) :: value

    value = sum(dpmpar)
  end function parameter_sum
end module parameter_array_constants_f90
