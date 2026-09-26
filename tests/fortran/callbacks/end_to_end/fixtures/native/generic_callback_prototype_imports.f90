module handles
  implicit none
  type, bind(c) :: handle
    integer :: val
  end type
end module handles

module cbs
  implicit none
  abstract interface
    subroutine copy_fn(h, x)
      use handles
      implicit none
      type(handle) :: h
      integer :: x
    end subroutine
  end interface
end module cbs

module ifaces
  implicit none
  interface register
    subroutine register_impl(fn, key)
      use :: cbs, only : copy_fn
      implicit none
      procedure(copy_fn) :: fn
      integer, intent(out) :: key
    end subroutine register_impl
  end interface register
end module ifaces

module facade
  use ifaces
end module facade

subroutine register_impl(fn, key)
  use handles
  use cbs, only: copy_fn
  procedure(copy_fn) :: fn
  integer, intent(out) :: key
  type(handle) :: h
  integer :: v
  h%val = 7
  v = 4
  call fn(h, v)
  key = v + h%val
end subroutine register_impl
