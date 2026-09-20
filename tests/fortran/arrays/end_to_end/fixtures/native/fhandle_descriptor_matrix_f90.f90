module fhandle_descriptor_matrix_f90
  use iso_c_binding, only: c_bool
  implicit none

  type :: holder
    real(8), allocatable :: field_allocatable_values_with_long_name(:)
    logical(4), allocatable :: field_flags(:)
    character(len=4), allocatable :: field_fixed_words(:)
    character(len=4), allocatable :: field_missing_words(:)
    character(len=4), pointer :: field_missing_pointer(:) => null()
    real(8), pointer :: field_ptr(:) => null()
    character(len=:), pointer :: field_words(:) => null()
  end type holder

  integer(4), allocatable :: ints(:)
  real(4), allocatable :: reals(:)
  complex(8), allocatable :: complexes(:)
  logical(c_bool), allocatable :: flags(:)
  character(len=4), allocatable :: fixed_words(:)
  character(len=:), allocatable :: deferred_words(:)
  real(8), allocatable :: empty(:)
  real(8), allocatable :: spare(:)
  real(8), allocatable :: probe(:)
  real(8), allocatable :: optional_probe(:)
  real(8), allocatable :: pair_left(:)
  real(8), allocatable :: pair_right(:)
  real(8), allocatable :: pair_third(:)
  real(8), allocatable :: cube(:, :, :)
  real(8), target :: store(8)
  real(8), pointer :: reversed(:) => null()
  real(8), pointer :: strided(:) => null()
  real(8), pointer :: unassociated(:) => null()
  type(holder) :: parent

contains

  subroutine setup()
    integer :: i

    allocate(ints(3));        ints = [1_4, 2_4, 3_4]
    allocate(reals(2));       reals = [1.5_4, 2.5_4]
    allocate(complexes(2));   complexes = [(1.0_8, 2.0_8), (3.0_8, 4.0_8)]
    allocate(flags(3));       flags = [.true._c_bool, .false._c_bool, .true._c_bool]
    allocate(fixed_words(2)); fixed_words = ['abcd', 'efgh']
    allocate(character(len=6) :: deferred_words(2))
    deferred_words = ['alphas', 'bravos']
    allocate(empty(0))
    allocate(probe(3)); probe = 2.0_8
    allocate(optional_probe(3)); optional_probe = 2.0_8
    allocate(pair_left(3));  pair_left = 6.0_8
    allocate(pair_right(3)); pair_right = 7.0_8
    allocate(pair_third(3)); pair_third = 8.0_8
    allocate(cube(2, 3, 4)); cube = 1.0_8
    store = [(1.0_8 * i, i = 1, 8)]
    reversed => store(8:1:-1)
    strided => store(1:8:2)
    allocate(parent%field_allocatable_values_with_long_name(3))
    parent%field_allocatable_values_with_long_name = 5.0_8
    allocate(parent%field_flags(3)); parent%field_flags = [.true., .false., .true.]
    allocate(parent%field_fixed_words(2)); parent%field_fixed_words = ['abcd', 'efgh']
    parent%field_ptr => store(2:6:2)
    allocate(character(len=5) :: parent%field_words(2))
    parent%field_words = ['alpha', 'beta ']
  end subroutine setup

  subroutine reshape_alloc(values, n)
    real(8), allocatable, intent(inout) :: values(:)
    integer(4), intent(in) :: n

    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = 4.0_8
  end subroutine reshape_alloc

  subroutine grow_pair(first, second, n)
    real(8), allocatable, intent(inout) :: first(:), second(:)
    integer(4), intent(in) :: n

    if (allocated(first)) deallocate(first)
    if (allocated(second)) deallocate(second)
    allocate(first(n));  first = 8.0_8
    allocate(second(n)); second = 9.0_8
  end subroutine grow_pair

  subroutine grow_three(first, second, third, n)
    real(8), allocatable, intent(inout) :: first(:), second(:), third(:)
    integer(4), intent(in) :: n

    if (allocated(first)) deallocate(first)
    if (allocated(second)) deallocate(second)
    if (allocated(third)) deallocate(third)
    allocate(first(n));  first = 8.0_8
    allocate(second(n)); second = 9.0_8
    allocate(third(n));  third = 10.0_8
  end subroutine grow_three

  function optional_state(values) result(state)
    real(8), allocatable, optional, intent(in) :: values(:)
    integer(4) :: state

    if (.not. present(values)) then
      state = 0
    else if (.not. allocated(values)) then
      state = 1
    else
      state = int(sum(values), kind=4)
    end if
  end function optional_state

  subroutine grow_and_count(values, n, produced)
    real(8), allocatable, intent(inout) :: values(:)
    integer(4), intent(in) :: n
    integer(4), intent(out) :: produced

    if (allocated(values)) deallocate(values)
    allocate(values(n)); values = 11.0_8
    produced = n
  end subroutine grow_and_count

  function optional_alloc_state(values) result(state)
    real(8), allocatable, intent(in), optional :: values(:)
    integer(4) :: state

    if (.not. present(values)) then
      state = 0
    else if (allocated(values)) then
      state = 2
    else
      state = 1
    end if
  end function optional_alloc_state

  function assumed_total(actual) result(total)
    real(8), intent(in) :: actual(:)
    real(8) :: total

    total = sum(actual)
  end function assumed_total

  function int_total(actual) result(total)
    integer(4), intent(in) :: actual(:)
    integer(4) :: total

    total = sum(actual)
  end function int_total

  function real4_total(actual) result(total)
    real(4), intent(in) :: actual(:)
    real(4) :: total

    total = sum(actual)
  end function real4_total

  function complex_total(actual) result(total)
    complex(8), intent(in) :: actual(:)
    complex(8) :: total

    total = sum(actual)
  end function complex_total

  function true_count(actual) result(counted)
    logical(c_bool), intent(in) :: actual(:)
    integer(4) :: counted

    counted = count(actual)
  end function true_count

  function word_width(actual) result(width)
    character(len=*), intent(in) :: actual(:)
    integer(4) :: width

    width = len(actual)
  end function word_width

  function cube_score(actual) result(score)
    real(8), intent(in) :: actual(:, :, :)
    integer(4) :: score

    score = size(actual)
  end function cube_score
end module fhandle_descriptor_matrix_f90
