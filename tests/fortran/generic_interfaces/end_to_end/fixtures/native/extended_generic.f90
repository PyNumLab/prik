module gen_base_mod
  implicit none
  interface report
    module procedure report_int
  end interface report
contains
  subroutine report_int(value, seen)
    integer, intent(in) :: value
    integer, intent(out) :: seen
    seen = value
  end subroutine report_int
end module gen_base_mod

module gen_extended_mod
  use gen_base_mod, only : report
  implicit none
  interface report
    module procedure report_real
  end interface report
contains
  subroutine report_real(value, seen)
    real(8), intent(in) :: value
    integer, intent(out) :: seen
    seen = int(value) * 10
  end subroutine report_real
end module gen_extended_mod
