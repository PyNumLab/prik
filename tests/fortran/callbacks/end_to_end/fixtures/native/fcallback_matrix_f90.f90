module fcallback_matrix_f90
  implicit none

  abstract interface
    subroutine matrix_callback(input, output)
      real(8), intent(in) :: input(:,:)
      real(8), intent(out) :: output(:,:)
    end subroutine matrix_callback
  end interface

contains
  subroutine apply_matrix(callback, input, output)
    procedure(matrix_callback) :: callback
    real(8), intent(in) :: input(:,:)
    real(8), intent(out) :: output(:,:)

    call callback(input, output)
  end subroutine apply_matrix
end module fcallback_matrix_f90
