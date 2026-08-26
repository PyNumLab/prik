integer function free_square(value) result(out)
  integer, intent(in) :: value
  out = value * value
end function free_square
