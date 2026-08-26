subroutine row_sums_c(n, values, result)
  integer, intent(in) :: n
  double precision, intent(in) :: values(*)
  double precision, intent(out) :: result(*)
  integer :: i

  do i = 1, n
    result(i) = values((i - 1) * 3 + 1) + values((i - 1) * 3 + 2) + values((i - 1) * 3 + 3)
  end do
end subroutine row_sums_c
