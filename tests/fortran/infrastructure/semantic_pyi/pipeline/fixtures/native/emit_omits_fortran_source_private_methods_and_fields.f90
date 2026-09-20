module private_method_mod
  implicit none
  private
  public :: box
  type :: box
    private
    integer, public :: id
    integer, private :: secret
  contains
    procedure, private :: hidden => hidden_impl
    procedure, public :: visible => visible_impl
  end type box
contains
  subroutine hidden_impl(self)
    class(box) :: self
  end subroutine hidden_impl
  subroutine visible_impl(self)
    class(box) :: self
  end subroutine visible_impl
end module
