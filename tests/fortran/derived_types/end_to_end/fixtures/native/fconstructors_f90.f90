
module fconstructors_f90
  implicit none
  private
  public :: initialized, get_final_count, reset_final_count

  integer :: final_count = 0

  type :: initialized
    integer :: id = 7
    real(8) :: scale = 2.5
  contains
    final :: cleanup_initialized
  end type initialized

contains
  subroutine cleanup_initialized(self)
    type(initialized) :: self

    final_count = final_count + 1
  end subroutine cleanup_initialized

  integer function get_final_count()
    get_final_count = final_count
  end function get_final_count

  subroutine reset_final_count()
    final_count = 0
  end subroutine reset_final_count
end module fconstructors_f90
