integer function triple_value(value) result(out)
  integer, intent(in) :: value
  out = 3 * value
end function triple_value

integer function offset_value(value) result(out)
  integer, intent(in) :: value
  out = value + 10
end function offset_value
