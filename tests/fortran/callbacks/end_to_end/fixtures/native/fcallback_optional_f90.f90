module fcallback_optional_f90
  use iso_c_binding
  implicit none

  abstract interface
    subroutine report(value, status, values, terminate)
      integer, intent(in) :: value
      integer, intent(in), optional :: status
      real(8), intent(in), optional :: values(:)
      logical, intent(out), optional :: terminate
    end subroutine report

    subroutine c_report(value, status) bind(C)
      import c_int
      integer(c_int), value, intent(in) :: value
      integer(c_int), intent(in), optional :: status
    end subroutine c_report
  end interface

contains

  integer function run(mode, callback) result(output)
    integer, intent(in) :: mode
    procedure(report), optional :: callback
    integer :: status
    real(8) :: values(2)
    logical :: terminate

    output = -1
    if (.not. present(callback)) return
    output = mode
    select case (mode)
    case (0)
      call callback(4)
    case (1)
      status = 9
      call callback(4, status)
    case (2)
      status = 9
      values = [1.5d0, 2.5d0]
      call callback(4, status, values)
    case (3)
      terminate = .false.
      call callback(4, terminate=terminate)
      if (terminate) output = 99
    end select
  end function run

  integer(c_int) function direct_run(mode, callback) bind(C) result(output)
    integer(c_int), value, intent(in) :: mode
    procedure(c_report), optional :: callback
    integer(c_int) :: status

    output = -1_c_int
    if (.not. present(callback)) return
    output = mode
    if (mode == 0_c_int) then
      call callback(4_c_int)
    else
      status = 9_c_int
      call callback(4_c_int, status)
    end if
  end function direct_run
end module fcallback_optional_f90
