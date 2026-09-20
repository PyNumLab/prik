module fcallback_scalar_storage_f90
  implicit none

  abstract interface
    subroutine directions_callback(read_value, update_value, write_value)
      real(8), intent(in) :: read_value
      real(8), intent(inout) :: update_value
      real(8), intent(out) :: write_value
    end subroutine directions_callback
  end interface

contains
  subroutine apply_directions(callback, read_value, update_value, write_value)
    procedure(directions_callback) :: callback
    real(8), intent(in) :: read_value
    real(8), intent(inout) :: update_value
    real(8), intent(out) :: write_value

    call callback(read_value, update_value, write_value)
  end subroutine apply_directions
end module fcallback_scalar_storage_f90
