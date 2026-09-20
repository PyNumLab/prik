module fscalar_module_state_f90
  implicit none
  integer(4), parameter :: nmax = 12
  integer(4), parameter :: computed_limit = kind(1.0) * 2
  character*1, parameter :: prefix = 'D'
  integer(4) :: counter = 3
  real(8), target :: target_scale = 1.5_8
  real(8), allocatable :: optional_scale
  real(8), pointer :: selected_scale => null()
  real(8), allocatable :: values(:)
contains
  function summarize() result(value)
    integer(4) :: value

    value = counter + nmax
  end function summarize

  function set_allocatable(value) result(current)
    real(8), intent(in) :: value
    real(8) :: current

    if (allocated(optional_scale)) deallocate(optional_scale)
    allocate(optional_scale)
    optional_scale = value
    current = optional_scale
  end function set_allocatable

  function point_to_target(value) result(current)
    real(8), intent(in) :: value
    real(8) :: current

    target_scale = value
    selected_scale => target_scale
    current = selected_scale
  end function point_to_target

  function bump_native() result(total)
    real(8) :: total

    if (allocated(optional_scale)) optional_scale = optional_scale + 10.0_8
    if (associated(selected_scale)) selected_scale = selected_scale + 20.0_8
    total = 0.0_8
    if (allocated(optional_scale)) total = total + optional_scale
    if (associated(selected_scale)) total = total + selected_scale
  end function bump_native

  function clear_all() result(status)
    integer(4) :: status

    if (allocated(optional_scale)) deallocate(optional_scale)
    nullify(selected_scale)
    status = 0
  end function clear_all

  subroutine allocate_values(n)
    integer(4), intent(in) :: n
    integer(4) :: i

    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = [(real(i, 8), i = 1, n)]
  end subroutine allocate_values

  subroutine scale_values(factor)
    real(8), intent(in) :: factor

    values = factor * values
  end subroutine scale_values

  subroutine deallocate_values()
    if (allocated(values)) deallocate(values)
  end subroutine deallocate_values
end module fscalar_module_state_f90
