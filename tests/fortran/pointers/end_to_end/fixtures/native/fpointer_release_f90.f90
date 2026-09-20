module fpointer_release_f90
  implicit none
  real(8), allocatable, target :: pool(:)
contains
  function mint(n) result(values)
    integer(4), intent(in) :: n
    real(8), pointer :: values(:)
    allocate(values(n))
    values = 1.0d0
  end function mint

  function borrow(n) result(values)
    integer(4), intent(in) :: n
    real(8), pointer :: values(:)
    if (.not. allocated(pool)) allocate(pool(n))
    pool = 2.0d0
    values => pool
  end function borrow
end module fpointer_release_f90
