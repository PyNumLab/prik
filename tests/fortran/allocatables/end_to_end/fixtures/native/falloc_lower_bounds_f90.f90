module falloc_lower_bounds_f90
  use iso_fortran_env, only: int32, real64
  implicit none
  real(real64), allocatable :: plain_a(:)
  real(real64), allocatable, target :: tgt_a(:)
  real(real64), allocatable, target :: defaulted(:)
  character(len=5), allocatable, target :: fixed_words(:)
  character(len=5), allocatable :: missing_words(:)
  character(len=5), pointer :: missing_pointer(:) => null()
  character(len=:), allocatable, target :: deferred_words(:)
contains
  function lower_bound_of(x) result(bound)
    real(real64), allocatable, intent(in) :: x(:)
    integer(int32) :: bound
    bound = lbound(x, 1)
  end function lower_bound_of

  function element_at(x, index) result(value)
    real(real64), allocatable, intent(in) :: x(:)
    integer(int32), intent(in) :: index
    real(real64) :: value
    value = x(index)
  end function element_at

  function deferred_word_bound_and_width(x) result(packed)
    character(len=:), allocatable, intent(in) :: x(:)
    integer(int32) :: packed
    packed = 100 * lbound(x, 1) + len(x)
  end function deferred_word_bound_and_width

  subroutine setup()
    allocate(plain_a(5:8))
    plain_a = 1.0d0
    allocate(tgt_a(5:8))
    tgt_a = 2.0d0
    allocate(defaulted(4))
    defaulted = 3.0d0
    allocate(character(len=5) :: fixed_words(5:8))
    fixed_words = 'aaaaa'
    allocate(character(len=6) :: deferred_words(5:8))
    deferred_words = 'bbbbbb'
  end subroutine setup
end module falloc_lower_bounds_f90
