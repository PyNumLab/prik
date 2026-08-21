
module fnaming_f90
  implicit none
  private
  public :: lambda, lambda_, get_value, value, visible_t

  integer :: value = 7

  type :: hidden_t
    integer :: value = 99
  end type hidden_t

  type :: visible_t
    integer :: lambda = 3
    integer :: lambda_ = 4
  contains
    procedure, public :: from => visible_from
    procedure, private :: hidden => visible_hidden
  end type visible_t

contains
  integer function lambda(value) result(out)
    integer, intent(in) :: value

    out = value + 1
  end function lambda

  integer function lambda_(value) result(out)
    integer, intent(in) :: value

    out = value + 2
  end function lambda_

  integer function get_value() result(out)
    out = 100
  end function get_value

  integer function visible_from(self) result(out)
    class(visible_t), intent(in) :: self

    out = self%lambda + self%lambda_
  end function visible_from

  integer function visible_hidden(self) result(out)
    class(visible_t), intent(in) :: self

    out = -1
  end function visible_hidden

  integer function hidden_proc() result(out)
    out = -10
  end function hidden_proc
end module fnaming_f90
