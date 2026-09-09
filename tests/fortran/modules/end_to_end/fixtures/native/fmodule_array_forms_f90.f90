module fmodule_array_forms_f90
  use iso_c_binding, only: c_bool
  use iso_fortran_env, only: int32, real64
  implicit none

  type :: sample
    real(real64) :: grid(2, 3)
    integer(int32) :: n
  end type sample

  ! Fixed shape: the declaration holds the shape; only the address is unknown.
  real(real64) :: fixed_plain(4) = [1.0d0, 2.0d0, 3.0d0, 4.0d0]
  real(real64), target :: fixed_target(4) = [5.0d0, 6.0d0, 7.0d0, 8.0d0]
  real(real64) :: fixed_matrix(2, 3)
  real(real64) :: fixed_shifted(5:8) = [9.0d0, 10.0d0, 11.0d0, 12.0d0]
  integer(int32) :: fixed_counts(3) = [7, 8, 9]
  logical(c_bool) :: fixed_flags(3) = [.true., .false., .true.]

  ! Allocatable: bounds, strides and element length are runtime facts.
  real(real64), allocatable :: alloc_plain(:)
  real(real64), allocatable, target :: alloc_target(:)
  real(real64), allocatable :: alloc_matrix(:, :)
  real(real64), allocatable :: alloc_shifted(:)

  ! Pointer: association is runtime state.
  real(real64), pointer :: ptr_link(:) => null()

  ! Character, in every storage form its element length can take.
  character(len=5) :: char_fixed(2) = ['alpha', 'bravo']
  character(len=5), target :: char_target(2) = ['gamma', 'delta']
  character(len=5), allocatable :: char_alloc(:)
  character(len=:), allocatable :: char_deferred(:)

  ! Derived objects whose array field is reached through the owner.
  type(sample) :: obj_plain
  type(sample), target :: obj_target

contains

  subroutine setup()
    fixed_matrix = reshape([1.0d0, 2.0d0, 3.0d0, 4.0d0, 5.0d0, 6.0d0], [2, 3])
    allocate(alloc_plain(4));      alloc_plain = [1.0d0, 2.0d0, 3.0d0, 4.0d0]
    allocate(alloc_target(3));     alloc_target = [9.0d0, 8.0d0, 7.0d0]
    allocate(alloc_matrix(2, 3));  alloc_matrix = 2.0d0
    allocate(alloc_shifted(5:8));  alloc_shifted = [1.0d0, 2.0d0, 3.0d0, 4.0d0]
    allocate(character(len=5) :: char_alloc(2));    char_alloc = ['epsil', 'zetaa']
    allocate(character(len=6) :: char_deferred(2)); char_deferred = ['etaaaa', 'thetaa']
    obj_plain%grid = 1.0d0;  obj_plain%n = 3
    obj_target%grid = 2.0d0; obj_target%n = 4
    ptr_link => alloc_target
  end subroutine setup

  ! One ordinary array dummy every numeric form above can be passed to.
  function total(values) result(sum_of)
    real(real64), intent(in) :: values(:)
    real(real64) :: sum_of
    sum_of = sum(values)
  end function total

  function total_2d(values) result(sum_of)
    real(real64), intent(in) :: values(:, :)
    real(real64) :: sum_of
    sum_of = sum(values)
  end function total_2d

  function count_set(values) result(how_many)
    logical(c_bool), intent(in) :: values(:)
    integer(int32) :: how_many
    how_many = count(values)
  end function count_set

  function total_counts(values) result(sum_of)
    integer(int32), intent(in) :: values(:)
    integer(int32) :: sum_of
    sum_of = sum(values)
  end function total_counts

  function first_word(values) result(word)
    character(len=5), intent(in) :: values(:)
    character(len=5) :: word
    word = values(1)
  end function first_word

  ! An allocatable dummy adopts the descriptor's bounds, unlike the ones above.
  function lower_bound_of(values) result(bound)
    real(real64), allocatable, intent(in) :: values(:)
    integer(int32) :: bound
    bound = lbound(values, 1)
  end function lower_bound_of

  subroutine bump_all()
    fixed_plain(1) = fixed_plain(1) + 100.0d0
    alloc_plain(1) = alloc_plain(1) + 100.0d0
    obj_plain%grid(1, 1) = obj_plain%grid(1, 1) + 100.0d0
  end subroutine bump_all

end module fmodule_array_forms_f90
