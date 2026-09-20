subroutine column_sums_f(rows, columns, values, result)
  integer, intent(in) :: rows
  integer, intent(in) :: columns
  double precision, intent(in) :: values(rows, *)
  double precision, intent(out) :: result(*)
  integer :: column

  do column = 1, columns
    result(column) = sum(values(:, column))
  end do
end subroutine column_sums_f

subroutine bump_storage(value)
  integer, intent(inout) :: value
  value = value + 1
end subroutine bump_storage

subroutine make_storage(value)
  integer, intent(out) :: value
  value = 42
end subroutine make_storage

function storage_value() result(value)
  integer :: value
  value = 43
end function storage_value
