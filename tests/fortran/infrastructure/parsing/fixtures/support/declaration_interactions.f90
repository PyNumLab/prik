module declaration_interactions
  implicit none
  type legacy_state
    integer :: enabled = 1 < 2
  end type legacy_state
  type :: parent_state
  end type parent_state
  type, extends(parent_state) :: child_state
  end type child_state
  type, extends(remote_state) :: external_child_state
  end type external_child_state
  integer, target :: selected
  integer, public :: exposed
  integer, parameter :: truth = 1 < 2
  real, parameter :: scale = 1.25d0
  character(len=*), parameter :: label = "timer"
  character*1, parameter :: prefix = 'D'
  complex, parameter :: imaginary = (0.d0, 1.d0)
end module declaration_interactions
