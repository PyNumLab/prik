
! Final feature-owned fixture for scalar callback lifecycle coverage.
module fcallback_scalar_f90
  implicit none

  abstract interface
    real(8) function scalar_callback(value) result(output)
      real(8), intent(in) :: value
    end function scalar_callback
    subroutine notify_callback(value)
      real(8), intent(in) :: value
    end subroutine notify_callback
  end interface

contains
  real(8) function apply_scalar(callback, value) result(output)
    procedure(scalar_callback) :: callback
    real(8), intent(in) :: value

    output = callback(value)
  end function apply_scalar

  real(8) function apply_explicit(callback, value) result(output)
    interface
      real(8) function callback(value) result(callback_output)
        real(8), intent(in) :: value
      end function callback
    end interface
    real(8), intent(in) :: value

    output = callback(value)
  end function apply_explicit

  subroutine call_notify(callback, value)
    procedure(notify_callback) :: callback
    real(8), intent(in) :: value

    call callback(value)
  end subroutine call_notify
end module fcallback_scalar_f90
