module fcallback_undeclared_intent_f90
  implicit none

  abstract interface
    subroutine tweak_callback(value)
      real(8) :: value
    end subroutine tweak_callback
  end interface

contains
  subroutine drive(callback, seed, result)
    procedure(tweak_callback) :: callback
    real(8), intent(in) :: seed
    real(8), intent(out) :: result

    result = seed
    call callback(result)
  end subroutine drive
end module fcallback_undeclared_intent_f90
