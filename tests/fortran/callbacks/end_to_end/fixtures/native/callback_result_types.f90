module cbresult_types
  implicit none
  type :: point_t
    real(8) :: x
  end type point_t

  abstract interface
    function make_point(x) result(p)
      import :: point_t
      implicit none
      real(8), intent(in) :: x
      type(point_t) :: p
    end function make_point
  end interface
end module cbresult_types
