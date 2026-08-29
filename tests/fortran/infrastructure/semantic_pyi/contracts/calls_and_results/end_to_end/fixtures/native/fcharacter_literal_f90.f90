module fcharacter_literal_f90
  implicit none
  private

  public :: select_value

contains

  subroutine select_value(mode, left, right, chosen)
    character(len=1), intent(in) :: mode
    real(8), intent(in) :: left
    real(8), intent(in) :: right
    real(8), intent(out) :: chosen

    if (mode == "L") then
      chosen = left
    else
      chosen = right
    end if
  end subroutine select_value

end module fcharacter_literal_f90

function pick_bind_c(mode, left, right) bind(c, name="pick_bind_c") result(chosen)
  use iso_c_binding, only: c_char, c_double
  implicit none
  character(kind=c_char, len=1), value :: mode
  real(c_double), value :: left
  real(c_double), value :: right
  real(c_double) :: chosen

  if (mode == "L") then
    chosen = left
  else
    chosen = right
  end if
end function pick_bind_c
