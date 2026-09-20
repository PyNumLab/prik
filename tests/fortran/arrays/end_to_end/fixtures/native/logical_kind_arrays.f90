module logical_kind_arrays
  use, intrinsic :: iso_c_binding, only: c_bool, c_int32_t
  implicit none
contains

  subroutine exercise_c_bool(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=c_bool), intent(in) :: input_values(n)
    logical(kind=c_bool), intent(out) :: output_values(n)
    logical(kind=c_bool), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_c_bool

  subroutine exercise_8(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=1), intent(in) :: input_values(n)
    logical(kind=1), intent(out) :: output_values(n)
    logical(kind=1), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_8

  subroutine exercise_16(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=2), intent(in) :: input_values(n)
    logical(kind=2), intent(out) :: output_values(n)
    logical(kind=2), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_16

  subroutine exercise_32(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=4), intent(in) :: input_values(n)
    logical(kind=4), intent(out) :: output_values(n)
    logical(kind=4), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_32

  subroutine exercise_64(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=8), intent(in) :: input_values(n)
    logical(kind=8), intent(out) :: output_values(n)
    logical(kind=8), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_64

  subroutine replace_c_bool(values)
    logical(kind=c_bool), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_c_bool

  subroutine replace_8(values)
    logical(kind=1), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_8

  subroutine replace_16(values)
    logical(kind=2), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_16

  subroutine replace_32(values)
    logical(kind=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_32

  subroutine replace_64(values)
    logical(kind=8), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_64

end module logical_kind_arrays
