module first_mod
  implicit none
  interface report
    module procedure report_first
  end interface report
contains
  subroutine report_first()
  end subroutine report_first
end module first_mod

module second_mod
  implicit none
  interface report
    module procedure report_second
  end interface report
contains
  subroutine report_second()
  end subroutine report_second
end module second_mod
