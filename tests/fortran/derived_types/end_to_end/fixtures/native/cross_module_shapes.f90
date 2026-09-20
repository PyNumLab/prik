module shapes
  implicit none
  type :: box
    integer :: value = 0
  end type box
  type, extends(box) :: tagged_box
    integer :: tag = 0
  end type tagged_box
end module shapes
