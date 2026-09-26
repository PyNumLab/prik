
module fassumed_rank_f90
  real(8), target :: pointer_values(2) = [3.0_8, 4.0_8]
  private :: pointer_values, flat_sum, flat_add
contains
  function allocatable_handle() result(values)
    real(8), allocatable :: values(:)

    allocate(values(2))
    values = [1.0_8, 2.0_8]
  end function allocatable_handle

  function pointer_handle() result(values)
    real(8), pointer :: values(:)

    values => pointer_values
  end function pointer_handle

  integer function optional_rank(values) result(observed)
    real(8), intent(in), optional :: values(..)

    if (present(values)) then
      observed = rank(values)
    else
      observed = -1
    end if
  end function optional_rank

  real(8) function rank_weighted_sum(values) result(total)
    real(8), intent(in) :: values(..)

    total = -1.0_8
    select rank(values)

    rank(1)
      total = real(1, 8) + flat_sum(size(values), values)

    rank(2)
      total = real(2, 8) + flat_sum(size(values), values)

    rank(3)
      total = real(3, 8) + flat_sum(size(values), values)

    rank(4)
      total = real(4, 8) + flat_sum(size(values), values)

    rank(5)
      total = real(5, 8) + flat_sum(size(values), values)

    rank(6)
      total = real(6, 8) + flat_sum(size(values), values)

    rank(7)
      total = real(7, 8) + flat_sum(size(values), values)

    rank(8)
      total = real(8, 8) + flat_sum(size(values), values)

    rank(9)
      total = real(9, 8) + flat_sum(size(values), values)

    rank(10)
      total = real(10, 8) + flat_sum(size(values), values)

    rank(11)
      total = real(11, 8) + flat_sum(size(values), values)

    rank(12)
      total = real(12, 8) + flat_sum(size(values), values)

    rank(13)
      total = real(13, 8) + flat_sum(size(values), values)

    rank(14)
      total = real(14, 8) + flat_sum(size(values), values)

    rank(15)
      total = real(15, 8) + flat_sum(size(values), values)

    rank default
      total = -99.0_8
    end select
  end function rank_weighted_sum

  subroutine bump_assumed_rank(values)
    real(8), intent(inout) :: values(..)

    select rank(values)

    rank(1)
      call flat_add(size(values), values, real(1, 8))

    rank(2)
      call flat_add(size(values), values, real(2, 8))

    rank(3)
      call flat_add(size(values), values, real(3, 8))

    rank(4)
      call flat_add(size(values), values, real(4, 8))

    rank(5)
      call flat_add(size(values), values, real(5, 8))

    rank(6)
      call flat_add(size(values), values, real(6, 8))

    rank(7)
      call flat_add(size(values), values, real(7, 8))

    rank(8)
      call flat_add(size(values), values, real(8, 8))

    rank(9)
      call flat_add(size(values), values, real(9, 8))

    rank(10)
      call flat_add(size(values), values, real(10, 8))

    rank(11)
      call flat_add(size(values), values, real(11, 8))

    rank(12)
      call flat_add(size(values), values, real(12, 8))

    rank(13)
      call flat_add(size(values), values, real(13, 8))

    rank(14)
      call flat_add(size(values), values, real(14, 8))

    rank(15)
      call flat_add(size(values), values, real(15, 8))

    rank default
      return
    end select
  end subroutine bump_assumed_rank

  integer function rank_pair_score(left, right) result(score)
    real(8), intent(in) :: left(..)
    real(8), intent(in) :: right(..)

    score = 0
    select rank(left)

    rank(1)
      score = score + 100 + int(size(left))

    rank(2)
      score = score + 200 + int(size(left))

    rank(3)
      score = score + 300 + int(size(left))

    rank(4)
      score = score + 400 + int(size(left))

    rank(5)
      score = score + 500 + int(size(left))

    rank(6)
      score = score + 600 + int(size(left))

    rank(7)
      score = score + 700 + int(size(left))

    rank(8)
      score = score + 800 + int(size(left))

    rank(9)
      score = score + 900 + int(size(left))

    rank(10)
      score = score + 1000 + int(size(left))

    rank(11)
      score = score + 1100 + int(size(left))

    rank(12)
      score = score + 1200 + int(size(left))

    rank(13)
      score = score + 1300 + int(size(left))

    rank(14)
      score = score + 1400 + int(size(left))

    rank(15)
      score = score + 1500 + int(size(left))

    rank default
      score = score - 100000
    end select

    select rank(right)

    rank(1)
      score = score + 1 + int(size(right))

    rank(2)
      score = score + 2 + int(size(right))

    rank(3)
      score = score + 3 + int(size(right))

    rank(4)
      score = score + 4 + int(size(right))

    rank(5)
      score = score + 5 + int(size(right))

    rank(6)
      score = score + 6 + int(size(right))

    rank(7)
      score = score + 7 + int(size(right))

    rank(8)
      score = score + 8 + int(size(right))

    rank(9)
      score = score + 9 + int(size(right))

    rank(10)
      score = score + 10 + int(size(right))

    rank(11)
      score = score + 11 + int(size(right))

    rank(12)
      score = score + 12 + int(size(right))

    rank(13)
      score = score + 13 + int(size(right))

    rank(14)
      score = score + 14 + int(size(right))

    rank(15)
      score = score + 15 + int(size(right))

    rank default
      score = score - 100000
    end select
  end function rank_pair_score

  pure real(8) function flat_sum(n, values) result(total)
    integer, intent(in) :: n
    real(8), intent(in) :: values(n)

    total = sum(values)
  end function flat_sum

  pure subroutine flat_add(n, values, delta)
    integer, intent(in) :: n
    real(8), intent(inout) :: values(n)
    real(8), intent(in) :: delta

    values = values + delta
  end subroutine flat_add
end module fassumed_rank_f90
