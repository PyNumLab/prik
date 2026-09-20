module fcallback_direct_storage_f90
  use iso_c_binding
  implicit none

  abstract interface
    subroutine update_callback(value) bind(C)
      import :: c_double
      real(c_double), intent(inout) :: value
    end subroutine update_callback

    subroutine emit_callback(value) bind(C)
      import :: c_double
      real(c_double), intent(out) :: value
    end subroutine emit_callback
  end interface

contains
  real(c_double) function drive_update(callback, seed) bind(C) result(output)
    procedure(update_callback) :: callback
    real(c_double), value, intent(in) :: seed

    output = seed
    call callback(output)
  end function drive_update

  real(c_double) function drive_emit(callback) bind(C) result(output)
    procedure(emit_callback) :: callback

    call callback(output)
  end function drive_emit
end module fcallback_direct_storage_f90
