
! Final feature-owned fixture for array callback results.
module fcallback_array_f90
  implicit none

  abstract interface
    real(8) function reduce_callback(count, values) result(output)
      integer, intent(in) :: count
      real(8), intent(in) :: values(count)
    end function reduce_callback

    function transform_callback(count, values) result(output)
      integer, intent(in) :: count
      real(8), intent(in) :: values(count)
      real(8) :: output(count)
    end function transform_callback
  end interface

contains
  real(8) function apply_reduce(callback, count, values) result(output)
    procedure(reduce_callback) :: callback
    integer, intent(in) :: count
    real(8), intent(in) :: values(count)

    output = callback(count, values)
  end function apply_reduce

  subroutine apply_transform(callback, count, values, output)
    procedure(transform_callback) :: callback
    integer, intent(in) :: count
    real(8), intent(in) :: values(count)
    real(8), intent(out) :: output(count)

    output = callback(count, values)
  end subroutine apply_transform
end module fcallback_array_f90
