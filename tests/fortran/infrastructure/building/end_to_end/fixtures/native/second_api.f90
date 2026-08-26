module second_api
  use first_api, only: add_one
  integer :: counter = 3
contains
  integer function double_value(value) result(output)
    integer, intent(in) :: value
    output = add_one(value) * 2
  end function double_value
end module second_api
