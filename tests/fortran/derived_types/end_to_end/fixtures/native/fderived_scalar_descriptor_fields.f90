module scalar_descriptor_fields
  implicit none

  type :: record
    real(8) :: plain = 0
    real(8), allocatable :: scale
    real(8), pointer :: weight => null()
    character(len=:), allocatable :: name
    character(len=4), pointer :: tag => null()
  end type record

  type(record) :: shared
contains
  subroutine fill(item)
    type(record), intent(inout) :: item
    item%scale = 1.5d0
    allocate(item%weight)
    item%weight = 2.5d0
    item%name = 'hello'
    allocate(item%tag)
    item%tag = 'abcd'
  end subroutine fill

  function total(item) result(value)
    type(record), intent(in) :: item
    real(8) :: value
    value = item%scale + item%weight
  end function total

  function shared_name() result(value)
    character(len=:), allocatable :: value
    value = shared%name
  end function shared_name
end module scalar_descriptor_fields
