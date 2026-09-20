module surface
  implicit none
contains
  function required_only(alpha, beta) result(total)
    real(8), intent(in) :: alpha, beta
    real(8) :: total
    total = alpha + beta
  end function required_only

  function has_optional(value, scale) result(total)
    real(8), intent(in) :: value
    real(8), intent(in), optional :: scale
    real(8) :: total
    total = value
    if (present(scale)) total = value * scale
  end function has_optional
end module surface
