module fhandle_array_forms_f90
  implicit none
  real(8), allocatable :: values(:)
  real(8), allocatable :: matrix(:, :)
  real(8), allocatable :: hyper(:, :, :, :, :, :, :, :, :, :, :, :, :, :, :)
  real(8), target :: backing(8)
  real(8), pointer :: strided_values(:)
  character(len=:), allocatable :: words(:)
contains
  subroutine setup()
    integer :: i

    allocate(values(4))
    values = [1.0_8, 2.0_8, 3.0_8, 4.0_8]
    allocate(matrix(2, 3))
    matrix = reshape([(1.0_8 * i, i = 1, 6)], [2, 3])
    allocate(hyper(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1))
    hyper = 1.0_8
    backing = [(1.0_8 * i, i = 1, 8)]
    strided_values => backing(1:8:2)
    allocate(character(len=5) :: words(2))
    words = [character(len=5) :: "alpha", "bravo"]
  end subroutine setup

  function explicit_total(actual, n) result(total)
    integer(4), intent(in) :: n
    real(8), intent(in) :: actual(n)
    real(8) :: total

    total = sum(actual)
  end function explicit_total

  function assumed_total(actual) result(total)
    real(8), intent(in) :: actual(:)
    real(8) :: total

    total = sum(actual)
  end function assumed_total

  function flat_total(actual, n) result(total)
    integer(4), intent(in) :: n
    real(8), intent(in) :: actual(*)
    real(8) :: total

    total = sum(actual(:n))
  end function flat_total

  function optional_total(actual) result(total)
    real(8), intent(in), optional :: actual(:)
    real(8) :: total

    if (present(actual)) then
      total = sum(actual)
    else
      total = -1.0_8
    end if
  end function optional_total

  function rank_score(actual) result(score)
    real(8), intent(in) :: actual(..)
    integer(4) :: score

    select rank (actual)
    rank (1)
      score = 100 + size(actual)
    rank (2)
      score = 200 + size(actual)
    rank (15)
      score = 1500 + size(actual)
    rank default
      score = -1
    end select
  end function rank_score

  function element_width(actual) result(width)
    character(len=*), intent(in) :: actual(:)
    integer(4) :: width

    width = len(actual)
  end function element_width
end module fhandle_array_forms_f90
