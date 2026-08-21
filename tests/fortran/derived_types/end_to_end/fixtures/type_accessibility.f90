module type_accessibility
  implicit none
  private

  public :: gated

  type,public :: gated
    private
    integer(4) :: hidden = 7
    integer(4),public :: shown = 3
  contains
    private
    procedure :: internal_step
    procedure,public :: step => internal_step
    procedure,public :: peek => gated_peek
  end type gated

contains

  subroutine internal_step(self)
    class(gated),intent(inout) :: self
    self%hidden = self%hidden + 1
  end subroutine internal_step

  integer(4) function gated_peek(self)
    class(gated),intent(in) :: self
    gated_peek = self%hidden
  end function gated_peek

end module type_accessibility
