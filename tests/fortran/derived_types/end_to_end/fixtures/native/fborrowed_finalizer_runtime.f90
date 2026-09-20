module derived_borrowed_finalizer
  implicit none
  integer :: final_count = 0

  type :: child
    integer :: marker = 0
  contains
    final :: cleanup_child
  end type child

  type :: parent
    type(child) :: value
  end type parent
contains
  subroutine cleanup_child(self)
    type(child) :: self
    final_count = final_count + 1
  end subroutine cleanup_child

  function make_parent() result(value)
    type(parent) :: value
  end function make_parent

  function get_final_count() result(value)
    integer :: value
    value = final_count
  end function get_final_count

  subroutine reset_final_count()
    final_count = 0
  end subroutine reset_final_count
end module derived_borrowed_finalizer
