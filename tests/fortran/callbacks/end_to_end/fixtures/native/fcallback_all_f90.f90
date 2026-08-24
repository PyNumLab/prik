! Final feature-owned fixture for callback shape and storage coverage.
module fcallback_all_f90
  implicit none

  type :: point_t
    real(8) :: x
    real(8) :: y
  end type point_t

  abstract interface
    integer function value_callback(value) result(output)
      integer, value, intent(in) :: value
    end function value_callback

    subroutine scalar_storage_callback(value, output, missing)
      real(8), intent(inout) :: value
      real(8), intent(out) :: output
      real(8) :: missing
    end subroutine scalar_storage_callback

    subroutine array_storage_callback(count, values, output)
      integer, intent(in) :: count
      real(8), intent(in) :: values(count)
      real(8), intent(out) :: output(count)
    end subroutine array_storage_callback

    subroutine string_storage_callback(read_label, write_label, update_label)
      character(len=8), intent(in) :: read_label
      character(len=8), intent(out) :: write_label
      character(len=8), intent(inout) :: update_label
    end subroutine string_storage_callback

    function point_callback(value) result(output)
      import :: point_t
      type(point_t), intent(in) :: value
      type(point_t) :: output
    end function point_callback
  end interface

contains
  integer function apply_value_callback(callback, value) result(output)
    procedure(value_callback) :: callback
    integer, intent(in) :: value

    output = callback(value)
  end function apply_value_callback

  subroutine apply_scalar_storage_callback(callback, value, missing, output)
    procedure(scalar_storage_callback) :: callback
    real(8), intent(inout) :: value
    real(8), intent(inout) :: missing
    real(8), intent(out) :: output

    call callback(value, output, missing)
  end subroutine apply_scalar_storage_callback

  subroutine apply_array_storage_callback(callback, count, values, output)
    procedure(array_storage_callback) :: callback
    integer, intent(in) :: count
    real(8), intent(in) :: values(count)
    real(8), intent(out) :: output(count)

    call callback(count, values, output)
  end subroutine apply_array_storage_callback

  subroutine apply_string_storage_callback(callback, update_label, write_label)
    procedure(string_storage_callback) :: callback
    character(len=8), intent(inout) :: update_label
    character(len=8), intent(out) :: write_label
    character(len=8) :: read_label

    read_label = "READONLY"
    call callback(read_label, write_label, update_label)
  end subroutine apply_string_storage_callback

  subroutine apply_point_callback(callback, value, output)
    procedure(point_callback) :: callback
    type(point_t), intent(in) :: value
    type(point_t), intent(out) :: output

    output = callback(value)
  end subroutine apply_point_callback
end module fcallback_all_f90
