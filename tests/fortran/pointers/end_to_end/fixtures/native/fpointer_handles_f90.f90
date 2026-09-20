module fpointer_handles_f90
  implicit none

  real(8), target :: module_storage(5) = [1.0_8, 2.0_8, 3.0_8, 4.0_8, 5.0_8]
  real(8), target :: field_storage(4) = [6.0_8, 7.0_8, 8.0_8, 9.0_8]
  real(8), pointer :: module_values(:) => null()
  real(8), allocatable, target :: module_allocatable(:)

  type :: pointer_box
    real(8), pointer :: values(:) => null()
  contains
    procedure :: associate_values => box_associate_values
    procedure :: associate_values_strided => box_associate_values_strided
  end type pointer_box

contains

  subroutine associate_module_slice()
    module_values => module_storage(2:5:2)
  end subroutine associate_module_slice

  subroutine associate_module_contiguous()
    module_values => module_storage(2:4)
  end subroutine associate_module_contiguous

  subroutine associate_module_reversed()
    module_values => module_storage(5:2:-1)
  end subroutine associate_module_reversed

  subroutine select_module_values(values)
    real(8), pointer, intent(out) :: values(:)
    values => module_storage(2:4)
  end subroutine select_module_values

  subroutine select_no_values(values)
    real(8), pointer, intent(out) :: values(:)
    nullify(values)
  end subroutine select_no_values

  subroutine allocate_module_values()
    if (allocated(module_allocatable)) deallocate(module_allocatable)
    allocate(module_allocatable(3))
    module_allocatable = [10.0_8, 20.0_8, 30.0_8]
  end subroutine allocate_module_values

  subroutine box_associate_values(self)
    class(pointer_box), intent(inout) :: self
    self%values => field_storage(2:4)
  end subroutine box_associate_values

  subroutine box_associate_values_strided(self)
    class(pointer_box), intent(inout) :: self
    self%values => field_storage(1:4:2)
  end subroutine box_associate_values_strided

  function sum_values(values) result(total)
    real(8), intent(in) :: values(:)
    real(8) :: total
    total = sum(values)
  end function sum_values

  function sum_pointer_descriptor(values) result(total)
    real(8), pointer, intent(in) :: values(:)
    real(8) :: total
    if (associated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function sum_pointer_descriptor

  function sum_allocatable_descriptor(values) result(total)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: total
    if (allocated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function sum_allocatable_descriptor

end module fpointer_handles_f90
