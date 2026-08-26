module fstring_descriptors_f90
  implicit none
  character(len=6), target, private :: static_six = 'STATIC'
  character(len=4), target, private :: static_four = 'FOUR'
contains
  ! --- character(len=:), allocatable ---
  subroutine grow(value)
    character(len=:), allocatable, intent(inout) :: value

    if (allocated(value)) value = value // '!!!'
  end subroutine grow

  subroutine shrink(value)
    character(len=:), allocatable, intent(inout) :: value

    if (allocated(value)) then
      if (len(value) > 2) value = value(1:2)
    end if
  end subroutine shrink

  subroutine drop(value)
    character(len=:), allocatable, intent(inout) :: value

    if (allocated(value)) deallocate(value)
  end subroutine drop

  subroutine optional_grow(value)
    character(len=:), allocatable, intent(inout), optional :: value

    if (present(value)) then
      if (allocated(value)) value = value // '?'
    end if
  end subroutine optional_grow

  subroutine grow_both(first, second)
    character(len=:), allocatable, intent(inout) :: first
    character(len=:), allocatable, intent(inout) :: second

    if (allocated(first)) first = first // '-1'
    if (allocated(second)) second = second // '-2'
  end subroutine grow_both

  subroutine grow_and_measure(value, length)
    character(len=:), allocatable, intent(inout) :: value
    integer(4), intent(out) :: length

    if (allocated(value)) value = value // '-tail'
    length = 0
    if (allocated(value)) length = len(value)
  end subroutine grow_and_measure

  subroutine measure(value, length)
    character(len=:), allocatable, intent(in) :: value
    integer(4), intent(out) :: length

    length = len(value)
  end subroutine measure

  subroutine make(value)
    character(len=:), allocatable, intent(out) :: value

    value = 'made'
  end subroutine make

  ! --- character(len=n), allocatable ---
  subroutine measure_fixed_allocatable(value, length)
    character(len=4), allocatable, intent(in) :: value
    integer(4), intent(out) :: length

    length = -1
    if (allocated(value)) length = len(value)
  end subroutine measure_fixed_allocatable

  subroutine make_fixed_allocatable(value)
    character(len=4), allocatable, intent(out) :: value

    value = 'MADE'
  end subroutine make_fixed_allocatable

  subroutine relabel_fixed_allocatable(value)
    character(len=4), allocatable, intent(inout) :: value

    if (allocated(value)) value = 'X' // value(2:4)
  end subroutine relabel_fixed_allocatable

  subroutine drop_fixed_allocatable(value)
    character(len=4), allocatable, intent(inout) :: value

    if (allocated(value)) deallocate(value)
  end subroutine drop_fixed_allocatable

  ! --- character(len=:), pointer ---
  subroutine measure_pointer(value, length)
    character(len=:), pointer, intent(in) :: value
    integer(4), intent(out) :: length

    length = -1
    if (associated(value)) length = len(value)
  end subroutine measure_pointer

  subroutine point_at_static(value)
    character(len=:), pointer, intent(out) :: value

    value => static_six
  end subroutine point_at_static

  subroutine edit_pointer_in_place(value)
    character(len=:), pointer, intent(inout) :: value

    if (associated(value)) value = 'Z'
  end subroutine edit_pointer_in_place

  subroutine reassociate_pointer(value)
    character(len=:), pointer, intent(inout) :: value

    value => static_six
  end subroutine reassociate_pointer

  subroutine deallocate_pointer(value)
    character(len=:), pointer, intent(inout) :: value

    if (associated(value)) deallocate(value)
  end subroutine deallocate_pointer

  subroutine nullify_pointer(value)
    character(len=:), pointer, intent(inout) :: value

    nullify(value)
  end subroutine nullify_pointer

  subroutine optional_pointer_measure(value, length)
    character(len=:), pointer, intent(in), optional :: value
    integer(4), intent(out) :: length

    length = -1
    if (present(value)) then
      length = -2
      if (associated(value)) length = len(value)
    end if
  end subroutine optional_pointer_measure

  subroutine optional_pointer_edit(value)
    character(len=:), pointer, intent(inout), optional :: value

    if (present(value)) then
      if (associated(value)) value = 'q'
    end if
  end subroutine optional_pointer_edit

  subroutine regrow_pointer(value)
    character(len=:), pointer, intent(inout) :: value
    character(len=:), pointer :: fresh

    if (associated(value)) then
      allocate(character(len=len(value) + 3) :: fresh)
      fresh = value // '>>>'
      deallocate(value)
      value => fresh
    end if
  end subroutine regrow_pointer

  ! --- character(len=n), pointer ---
  subroutine measure_fixed_pointer(value, length)
    character(len=4), pointer, intent(in) :: value
    integer(4), intent(out) :: length

    length = -1
    if (associated(value)) length = len(value)
  end subroutine measure_fixed_pointer

  subroutine point_at_fixed_static(value)
    character(len=4), pointer, intent(out) :: value

    value => static_four
  end subroutine point_at_fixed_static

  subroutine relabel_fixed_pointer(value)
    character(len=4), pointer, intent(inout) :: value

    if (associated(value)) value = 'P' // value(2:4)
  end subroutine relabel_fixed_pointer

  ! --- descriptor function results ---
  function allocatable_result() result(value)
    character(len=:), allocatable :: value

    value = 'allocatable'
  end function allocatable_result

  function fixed_allocatable_result() result(value)
    character(len=4), allocatable :: value

    value = 'FIXA'
  end function fixed_allocatable_result

  function pointer_result() result(value)
    character(len=:), pointer :: value

    value => static_six
  end function pointer_result

  function fixed_pointer_result() result(value)
    character(len=4), pointer :: value

    value => static_four
  end function fixed_pointer_result
end module fstring_descriptors_f90
