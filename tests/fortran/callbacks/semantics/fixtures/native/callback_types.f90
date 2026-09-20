module callback_types
  implicit none
  type :: point_t
    real(8) :: x
  end type point_t

  abstract interface
    subroutine move_point(p)
      import :: point_t
      implicit none
      type(point_t), intent(inout) :: p
    end subroutine move_point
  end interface
end module callback_types
