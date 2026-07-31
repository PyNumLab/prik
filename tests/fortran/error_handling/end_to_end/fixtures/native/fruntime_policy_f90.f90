module fruntime_policy_f90
contains
  subroutine pause_for_one_second()
    call sleep(1)
  end subroutine pause_for_one_second

  subroutine pause_with_gil()
    call sleep(1)
  end subroutine pause_with_gil

  subroutine solve(value, status, message)
    integer, intent(in) :: value
    integer, intent(out) :: status
    character(len=32), intent(out) :: message
    if (value < 0) then
      status = 2
      message = "negative input"
    else
      status = 0
      message = ""
    end if
  end subroutine solve
end module fruntime_policy_f90
