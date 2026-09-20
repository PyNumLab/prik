module cbresult_consumer
  use, non_intrinsic :: cbresult_types, only : make_point, point_t
  implicit none
contains
  subroutine run(f, seed, out_x)
    procedure(make_point) :: f
    real(8), intent(in) :: seed
    real(8), intent(out) :: out_x
    type(point_t) :: made

    made = f(seed)
    out_x = made%x
  end subroutine run
end module cbresult_consumer
