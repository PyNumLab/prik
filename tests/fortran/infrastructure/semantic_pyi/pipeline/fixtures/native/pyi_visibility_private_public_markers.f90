module visibility_mod
  implicit none
  private
  public :: pub_proc, visible_t

  type :: visible_t
     integer :: a
     integer :: b
  end type visible_t

  type :: hidden_t
     integer :: z
  end type hidden_t

contains
  subroutine pub_proc(x)
    integer, intent(in) :: x
  end subroutine pub_proc

  subroutine hidden_proc(x)
    integer, intent(in) :: x
  end subroutine hidden_proc
end module visibility_mod
