module fchar_module_descriptors_f90
  implicit none
  character(len=:), allocatable :: deferred
  character(len=6), allocatable :: fixed
  character(len=:), pointer :: link => null()
  character(len=6), target :: store = 'STORED'
  character(len=2), parameter :: pair(2) = ['ab', 'cd']
  character(len=3), parameter :: grid(2, 2) = reshape(['aaa', 'bbb', 'ccc', 'ddd'], [2, 2])
  character(len=*), parameter :: inferred(3) = ['alpha', 'beta ', 'gamma']
contains
  subroutine setup()
    deferred = 'alpha'
    fixed = 'FIXEDV'
    link => store
  end subroutine setup

  subroutine grow()
    deferred = deferred // '-more'
  end subroutine grow

  subroutine clear()
    if (allocated(deferred)) deallocate(deferred)
    if (allocated(fixed)) deallocate(fixed)
    nullify(link)
  end subroutine clear
end module fchar_module_descriptors_f90
