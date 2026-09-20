module reserved_extent_provider
  implicit none
contains
  pure integer function lambda(n)
    integer, intent(in) :: n
    lambda = n
  end function lambda
  pure integer function lambda_(n)
    integer, intent(in) :: n
    lambda_ = n + 1
  end function lambda_
end module reserved_extent_provider
