module fchar_declared_arrays_f90
  implicit none
  character(len=4), allocatable :: fixed_alloc(:)
  character(len=:), pointer :: deferred_ptr(:) => null()
  character(len=4), pointer :: fixed_ptr(:) => null()
  character(len=4), target :: store(2) = ['aaaa', 'bbbb']
contains
  subroutine setup()
    allocate(fixed_alloc(2))
    fixed_alloc = ['xxxx', 'yyyy']
    fixed_ptr => store
    deferred_ptr => store
  end subroutine setup

  subroutine allocate_deferred()
    if (associated(deferred_ptr)) nullify(deferred_ptr)
    allocate(character(len=6) :: deferred_ptr(3))
    deferred_ptr = ['a     ', 'bb    ', 'ccc   ']
  end subroutine allocate_deferred
end module fchar_declared_arrays_f90
