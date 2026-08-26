module matrix_left_types
  use iso_c_binding, only: c_int32_t
  implicit none

  type :: item
    integer(c_int32_t) :: value = 3_c_int32_t
  end type item

  type(item) :: state

contains

  function make_item(initial) result(value)
    integer(c_int32_t), intent(in) :: initial
    type(item) :: value
    value%value = initial
  end function make_item

end module matrix_left_types

module matrix_right_types
  use iso_c_binding, only: c_int32_t
  implicit none

  type :: item
    integer(c_int32_t) :: value = 7_c_int32_t
  end type item

  type(item) :: state

contains

  function make_item(initial) result(value)
    integer(c_int32_t), intent(in) :: initial
    type(item) :: value
    value%value = initial
  end function make_item

end module matrix_right_types

module fscalar_derived_actual_dummy_matrix_f90
  use iso_c_binding, only: c_bool, c_int, c_int32_t
  use matrix_left_types, only: left_item => item
  use matrix_right_types, only: right_item => item
  implicit none

  type :: item
    integer(c_int32_t) :: value = 0_c_int32_t
  end type item

  type :: sequence_item
    sequence
    integer(c_int32_t) :: value = 0_c_int32_t
  end type sequence_item

  ! The five rank-zero module actual declaration forms.
  type(item) :: ordinary_module
  type(item) :: ordinary_module_two
  type(item), target :: target_module
  type(item), allocatable :: allocatable_module
  type(item), allocatable, target :: allocatable_target_module
  type(item), pointer :: pointer_module => null()

  ! Extra distinct origins let one native call exercise several transactions.
  type(item), target :: pointer_target_one
  type(item), target :: pointer_target_two
  type(item), pointer :: pointer_module_two => null()
  type(item), pointer :: allocation_follower => null()
  integer(c_int32_t) :: writable_call_count = 0_c_int32_t

contains

  subroutine reset_state()
    ordinary_module%value = 10_c_int32_t
    ordinary_module_two%value = 12_c_int32_t
    target_module%value = 20_c_int32_t
    pointer_target_one%value = 50_c_int32_t
    pointer_target_two%value = 60_c_int32_t
    if (allocated(allocatable_module)) deallocate(allocatable_module)
    if (allocated(allocatable_target_module)) deallocate(allocatable_target_module)
    allocate(allocatable_module)
    allocate(allocatable_target_module)
    allocatable_module%value = 30_c_int32_t
    allocatable_target_module%value = 40_c_int32_t
    pointer_module => pointer_target_one
    pointer_module_two => pointer_target_two
    nullify(allocation_follower)
    writable_call_count = 0_c_int32_t
  end subroutine reset_state

  subroutine clear_allocatable_module()
    if (allocated(allocatable_module)) deallocate(allocatable_module)
  end subroutine clear_allocatable_module

  subroutine clear_allocatable_target_module()
    nullify(allocation_follower)
    if (allocated(allocatable_target_module)) deallocate(allocatable_target_module)
  end subroutine clear_allocatable_target_module

  subroutine clear_pointer_module()
    nullify(pointer_module)
  end subroutine clear_pointer_module

  subroutine associate_allocation_follower()
    if (allocated(allocatable_target_module)) then
      allocation_follower => allocatable_target_module
    else
      nullify(allocation_follower)
    end if
  end subroutine associate_allocation_follower

  function allocation_follower_value() result(value)
    integer(c_int32_t) :: value
    value = -1_c_int32_t
    if (associated(allocation_follower)) value = allocation_follower%value
  end function allocation_follower_value

  function get_writable_call_count() result(value)
    integer(c_int32_t) :: value
    value = writable_call_count
  end function get_writable_call_count

  function make_item(initial) result(value)
    integer(c_int32_t), intent(in) :: initial
    type(item) :: value
    value%value = initial
  end function make_item

  function make_sequence_item(initial) result(value)
    integer(c_int32_t), intent(in) :: initial
    type(sequence_item) :: value
    value%value = initial
  end function make_sequence_item

  subroutine make_target_item(initial, value)
    integer(c_int32_t), intent(in) :: initial
    type(item), target, intent(out) :: value
    value%value = initial
  end subroutine make_target_item

  subroutine make_allocatable_item(initial, make_present, value)
    integer(c_int32_t), intent(in) :: initial
    logical(c_bool), intent(in) :: make_present
    type(item), allocatable, intent(out) :: value
    if (make_present) then
      allocate(value)
      value%value = initial
    end if
  end subroutine make_allocatable_item

  subroutine make_allocatable_target_item(initial, make_present, value)
    integer(c_int32_t), intent(in) :: initial
    logical(c_bool), intent(in) :: make_present
    type(item), allocatable, target, intent(out) :: value
    if (make_present) then
      allocate(value)
      value%value = initial
    end if
  end subroutine make_allocatable_target_item

  function make_pointer_item(selector) result(value)
    integer(c_int32_t), intent(in) :: selector
    type(item), pointer :: value
    select case (selector)
    case (1_c_int32_t)
      value => pointer_target_one
    case (2_c_int32_t)
      value => pointer_target_two
    case default
      nullify(value)
    end select
  end function make_pointer_item

  ! The six exact native dummy forms.
  function read_object(value) result(observed)
    type(item), intent(in) :: value
    integer(c_int32_t) :: observed
    observed = value%value
  end function read_object

  function read_target(value) result(observed)
    type(item), target, intent(in) :: value
    integer(c_int32_t) :: observed
    observed = value%value
  end function read_target

  function read_allocatable(value) result(observed)
    type(item), allocatable, intent(in) :: value
    integer(c_int32_t) :: observed
    observed = -1_c_int32_t
    if (allocated(value)) observed = value%value
  end function read_allocatable

  function read_allocatable_target(value) result(observed)
    type(item), allocatable, target, intent(in) :: value
    integer(c_int32_t) :: observed
    observed = -1_c_int32_t
    if (allocated(value)) observed = value%value
  end function read_allocatable_target

  function read_pointer_input(value) result(observed)
    type(item), pointer, intent(in) :: value
    integer(c_int32_t) :: observed
    observed = -1_c_int32_t
    if (associated(value)) observed = value%value
  end function read_pointer_input

  function read_value(value) result(observed)
    type(item), value :: value
    integer(c_int32_t) :: observed
    observed = value%value
  end function read_value

  function read_sequence_value(value) result(observed)
    type(sequence_item), value :: value
    integer(c_int32_t) :: observed
    observed = value%value
  end function read_sequence_value

  subroutine increment_object(value, amount)
    type(item), intent(inout) :: value
    integer(c_int32_t), intent(in) :: amount
    value%value = value%value + amount
  end subroutine increment_object

  subroutine set_allocatable(value, new_value)
    type(item), allocatable, intent(inout) :: value
    integer(c_int32_t), intent(in) :: new_value
    if (new_value < 0_c_int32_t) then
      if (allocated(value)) deallocate(value)
      return
    end if
    if (.not. allocated(value)) allocate(value)
    value%value = new_value
  end subroutine set_allocatable

  subroutine set_allocatable_target(value, new_value)
    type(item), allocatable, target, intent(inout) :: value
    integer(c_int32_t), intent(in) :: new_value
    if (new_value < 0_c_int32_t) then
      if (allocated(value)) deallocate(value)
      return
    end if
    if (.not. allocated(value)) allocate(value)
    value%value = new_value
  end subroutine set_allocatable_target

  subroutine set_pointer(value, selector)
    type(item), pointer, intent(inout) :: value
    integer(c_int32_t), intent(in) :: selector
    select case (selector)
    case (1_c_int32_t)
      value => pointer_target_one
    case (2_c_int32_t)
      value => pointer_target_two
    case (3_c_int32_t)
      nullify(value)
      allocate(value)
      value%value = 70_c_int32_t
    case (4_c_int32_t)
      if (associated(value)) deallocate(value)
      nullify(value)
    case default
      nullify(value)
    end select
  end subroutine set_pointer

  function read_six_forms(object_value, target_value, allocatable_value, &
                          allocatable_target_value, pointer_value, value_value) result(total)
    type(item), intent(in) :: object_value
    type(item), target, intent(in) :: target_value
    type(item), allocatable, intent(in) :: allocatable_value
    type(item), allocatable, target, intent(in) :: allocatable_target_value
    type(item), pointer, intent(in) :: pointer_value
    type(item), value :: value_value
    integer(c_int32_t) :: total
    total = object_value%value + target_value%value + value_value%value
    if (allocated(allocatable_value)) total = total + allocatable_value%value
    if (allocated(allocatable_target_value)) total = total + allocatable_target_value%value
    if (associated(pointer_value)) total = total + pointer_value%value
  end function read_six_forms

  function read_qualified(left, right) result(total)
    type(left_item), intent(in) :: left
    type(right_item), intent(in) :: right
    integer(c_int32_t) :: total
    total = left%value * 100_c_int32_t + right%value
  end function read_qualified

  subroutine mutate_three_descriptors(first, second, third, amount)
    type(item), allocatable, intent(inout) :: first
    type(item), allocatable, target, intent(inout) :: second
    type(item), pointer, intent(inout) :: third
    integer(c_int32_t), intent(in) :: amount
    if (.not. allocated(first)) allocate(first)
    if (.not. allocated(second)) allocate(second)
    first%value = first%value + amount
    second%value = second%value + amount
    third => pointer_target_two
  end subroutine mutate_three_descriptors

  function read_duplicate(first, second) result(total)
    type(item), intent(in) :: first
    type(item), intent(in) :: second
    integer(c_int32_t) :: total
    total = first%value + second%value
  end function read_duplicate

  function read_optional(first, second) result(total)
    type(item), intent(in), optional :: first
    type(item), intent(in), optional :: second
    integer(c_int32_t) :: total
    total = 0_c_int32_t
    if (present(first)) total = total + first%value
    if (present(second)) total = total + second%value
  end function read_optional

  subroutine mutate_duplicate(first, second)
    type(item), intent(inout) :: first
    type(item), intent(inout) :: second
    writable_call_count = writable_call_count + 1_c_int32_t
    first%value = first%value + 1_c_int32_t
    second%value = second%value + 1_c_int32_t
  end subroutine mutate_duplicate

  subroutine hold_allocatable(value, milliseconds)
    type(item), allocatable, intent(inout) :: value
    integer(c_int32_t), intent(in) :: milliseconds
    integer(c_int) :: start_count, current_count, count_rate
    call system_clock(start_count, count_rate)
    do
      call system_clock(current_count)
      if ((current_count - start_count) * 1000_c_int / count_rate >= milliseconds) exit
    end do
    if (allocated(value)) value%value = value%value + 1_c_int32_t
  end subroutine hold_allocatable

  subroutine hold_object(value, milliseconds)
    type(item), intent(inout) :: value
    integer(c_int32_t), intent(in) :: milliseconds
    integer(c_int) :: start_count, current_count, count_rate
    call system_clock(start_count, count_rate)
    do
      call system_clock(current_count)
      if ((current_count - start_count) * 1000_c_int / count_rate >= milliseconds) exit
    end do
    value%value = value%value + 1_c_int32_t
  end subroutine hold_object

end module fscalar_derived_actual_dummy_matrix_f90
