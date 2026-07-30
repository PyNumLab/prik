module fruntime_abi_f90
contains
  real(8) function scale(value, factor) result(output)
    real(8), intent(in) :: value
    real(8), intent(in) :: factor
    output = value * factor
  end function scale
end module fruntime_abi_f90
