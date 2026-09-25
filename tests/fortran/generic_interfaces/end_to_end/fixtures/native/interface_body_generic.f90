module interface_body_generic
  implicit none
  public

  interface scale
    function scale_integer(value) result(output)
      integer, intent(in) :: value
      integer :: output
    end function scale_integer
    function scale_real(value) result(output)
      real(8), intent(in) :: value
      real(8) :: output
    end function scale_real
  end interface scale
end module interface_body_generic
