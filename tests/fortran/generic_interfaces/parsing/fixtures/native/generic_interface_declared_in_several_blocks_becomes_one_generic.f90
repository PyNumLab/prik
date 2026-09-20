module huge_mod
  implicit none
  private
  public :: huge_value

  interface huge_value
    module procedure huge_value_sp, huge_value_dp
  end interface huge_value

  interface huge_value
    module procedure huge_value_qp
  end interface huge_value
contains
  real function huge_value_sp(x)
    real, intent(in) :: x
    huge_value_sp = huge(x)
  end function huge_value_sp
  real(8) function huge_value_dp(x)
    real(8), intent(in) :: x
    huge_value_dp = huge(x)
  end function huge_value_dp
  real(16) function huge_value_qp(x)
    real(16), intent(in) :: x
    huge_value_qp = huge(x)
  end function huge_value_qp
end module huge_mod
