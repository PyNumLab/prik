module scope_name_reuse_combinations
  implicit none

  type :: same_name
    integer :: payload
  end type same_name

  integer :: same_name_i
  real :: same_name_r
  logical :: same_name_l
  complex :: same_name_c
  character(len=8) :: same_name_s

  interface do_work
    module procedure do_work_i
    module procedure do_work_r
    module procedure do_work_l
  end interface do_work

contains

  subroutine do_work_i(same_name)
    implicit none
    integer, intent(inout) :: same_name
    real :: shared

    shared = same_name
    call nested_block(shared)

  contains

    subroutine nested_block(shared)
      implicit none
      real, intent(inout) :: shared
      character(len=12) :: same_name

      same_name = 'inner-string'
      shared = shared + len_trim(same_name)
    end subroutine nested_block

  end subroutine do_work_i

  subroutine do_work_r(same_name)
    implicit none
    real, intent(in) :: same_name
    logical :: shared

    shared = same_name > 0.0
  end subroutine do_work_r

  subroutine do_work_l(same_name)
    implicit none
    logical, intent(in) :: same_name
    type(same_name) :: shared

    if (same_name) then
      shared%payload = 1
    else
      shared%payload = 0
    end if
  end subroutine do_work_l


  subroutine host_one(same_name)
    implicit none
    integer, intent(inout) :: same_name

    call helper(same_name)

  contains

    subroutine helper(same_name)
      implicit none
      integer, intent(inout) :: same_name
      same_name = same_name + 1
    end subroutine helper

  end subroutine host_one

  subroutine host_two(same_name)
    implicit none
    real, intent(inout) :: same_name

    call helper(same_name)

  contains

    subroutine helper(same_name)
      implicit none
      real, intent(inout) :: same_name
      same_name = same_name + 1.0
    end subroutine helper

  end subroutine host_two

  function convert_to_complex(same_name) result(shared)
    implicit none
    integer, intent(in) :: same_name
    complex :: shared

    shared = cmplx(real(same_name), -real(same_name))
  end function convert_to_complex

  function convert_to_char(same_name) result(shared)
    implicit none
    real, intent(in) :: same_name
    character(len=16) :: shared

    write(shared, '(f6.2)') same_name
  end function convert_to_char

  function convert_to_logical(same_name) result(shared)
    implicit none
    character(len=*), intent(in) :: same_name
    logical :: shared

    shared = len_trim(same_name) > 0
  end function convert_to_logical

end module scope_name_reuse_combinations
