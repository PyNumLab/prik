
module fborrowed_finalizer_f90
  implicit none
  private
  public :: child, parent, get_final_count, reset_final_count

  integer :: final_count = 0

  type :: child
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

  integer function get_final_count()
    get_final_count = final_count
  end function get_final_count

  subroutine reset_final_count()
    final_count = 0
  end subroutine reset_final_count
end module fborrowed_finalizer_f90
