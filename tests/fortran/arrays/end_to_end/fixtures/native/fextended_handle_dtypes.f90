\
module fextended_handle_dtypes
  use iso_c_binding, only: c_long_double, c_long_double_complex
  implicit none

  real(c_long_double), allocatable :: real_values(:)
  complex(c_long_double_complex), pointer :: complex_values(:) => null()

contains

  subroutine setup()
    integer :: i

    if (allocated(real_values)) deallocate(real_values)
    allocate(real_values(2))
    real_values = [1.0_c_long_double, 2.0_c_long_double]

    if (associated(complex_values)) deallocate(complex_values)
    allocate(complex_values(2))
    complex_values = [(cmplx(i, -i, kind=c_long_double_complex), i = 1, 2)]

  end subroutine setup

  function sum_real(values) result(total)
    real(c_long_double), intent(in) :: values(:)
    real(c_long_double) :: total
    total = sum(values)
  end function sum_real

  function sum_complex(values) result(total)
    complex(c_long_double_complex), intent(in) :: values(:)
    complex(c_long_double_complex) :: total
    total = sum(values)
  end function sum_complex

end module fextended_handle_dtypes
