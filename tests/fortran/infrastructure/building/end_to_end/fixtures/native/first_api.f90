module first_api
contains
  integer function add_one(value) result(output)
    integer, intent(in) :: value
    output = value + 1
  end function add_one
end module first_api
