
module fassumed_rank_f90
contains
  real(8) function rank_weighted_sum(values) result(total)
    real(8), intent(in) :: values(..)

    total = -1.0_8
    select rank(values)

    rank(1)
      total = real(1, 8) + sum(values)

    rank(2)
      total = real(2, 8) + sum(values)

    rank(3)
      total = real(3, 8) + sum(values)

    rank(4)
      total = real(4, 8) + sum(values)

    rank(5)
      total = real(5, 8) + sum(values)

    rank(6)
      total = real(6, 8) + sum(values)

    rank(7)
      total = real(7, 8) + sum(values)

    rank(8)
      total = real(8, 8) + sum(values)

    rank(9)
      total = real(9, 8) + sum(values)

    rank(10)
      total = real(10, 8) + sum(values)

    rank(11)
      total = real(11, 8) + sum(values)

    rank(12)
      total = real(12, 8) + sum(values)

    rank(13)
      total = real(13, 8) + sum(values)

    rank(14)
      total = real(14, 8) + sum(values)

    rank(15)
      total = real(15, 8) + sum(values)

    rank default
      total = -99.0_8
    end select
  end function rank_weighted_sum

  subroutine bump_assumed_rank(values)
    real(8), intent(inout) :: values(..)

    select rank(values)

    rank(1)
      values = values + real(1, 8)

    rank(2)
      values = values + real(2, 8)

    rank(3)
      values = values + real(3, 8)

    rank(4)
      values = values + real(4, 8)

    rank(5)
      values = values + real(5, 8)

    rank(6)
      values = values + real(6, 8)

    rank(7)
      values = values + real(7, 8)

    rank(8)
      values = values + real(8, 8)

    rank(9)
      values = values + real(9, 8)

    rank(10)
      values = values + real(10, 8)

    rank(11)
      values = values + real(11, 8)

    rank(12)
      values = values + real(12, 8)

    rank(13)
      values = values + real(13, 8)

    rank(14)
      values = values + real(14, 8)

    rank(15)
      values = values + real(15, 8)

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
      score = score + 100 + int(sum(left))

    rank(2)
      score = score + 200 + int(sum(left))

    rank(3)
      score = score + 300 + int(sum(left))

    rank(4)
      score = score + 400 + int(sum(left))

    rank(5)
      score = score + 500 + int(sum(left))

    rank(6)
      score = score + 600 + int(sum(left))

    rank(7)
      score = score + 700 + int(sum(left))

    rank(8)
      score = score + 800 + int(sum(left))

    rank(9)
      score = score + 900 + int(sum(left))

    rank(10)
      score = score + 1000 + int(sum(left))

    rank(11)
      score = score + 1100 + int(sum(left))

    rank(12)
      score = score + 1200 + int(sum(left))

    rank(13)
      score = score + 1300 + int(sum(left))

    rank(14)
      score = score + 1400 + int(sum(left))

    rank(15)
      score = score + 1500 + int(sum(left))

    rank default
      score = score - 100000
    end select

    select rank(right)

    rank(1)
      score = score + 1 + int(sum(right))

    rank(2)
      score = score + 2 + int(sum(right))

    rank(3)
      score = score + 3 + int(sum(right))

    rank(4)
      score = score + 4 + int(sum(right))

    rank(5)
      score = score + 5 + int(sum(right))

    rank(6)
      score = score + 6 + int(sum(right))

    rank(7)
      score = score + 7 + int(sum(right))

    rank(8)
      score = score + 8 + int(sum(right))

    rank(9)
      score = score + 9 + int(sum(right))

    rank(10)
      score = score + 10 + int(sum(right))

    rank(11)
      score = score + 11 + int(sum(right))

    rank(12)
      score = score + 12 + int(sum(right))

    rank(13)
      score = score + 13 + int(sum(right))

    rank(14)
      score = score + 14 + int(sum(right))

    rank(15)
      score = score + 15 + int(sum(right))

    rank default
      score = score - 100000
    end select
  end function rank_pair_score
end module fassumed_rank_f90
