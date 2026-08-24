module generic_constructor
  implicit none
  private

  public :: box, plain

  type, public :: box
    integer(4) :: count = 0
    real(8) :: value = 0.0d0
  end type box

  !> An interface named for the type is that type's constructor.
  interface box
    module procedure box_empty, box_from_count, box_from_value
  end interface box

  !> A type with no such interface keeps its keyword-field constructor.
  type, public :: plain
    integer(4) :: tag = 0
  end type plain

contains

  pure type(box) function box_empty() result(new_box)
    new_box%count = 0
    new_box%value = 0.0d0
  end function box_empty

  pure type(box) function box_from_count(count) result(new_box)
    integer(4), intent(in) :: count
    new_box%count = count
    new_box%value = real(count, 8)
  end function box_from_count

  pure type(box) function box_from_value(value) result(new_box)
    real(8), intent(in) :: value
    new_box%count = int(value, 4)
    new_box%value = value
  end function box_from_value

end module generic_constructor
