module fruntime_recursion_f90
contains
  recursive integer function factorial(n) result(output)
    integer, intent(in) :: n
    if (n <= 1) then
      output = 1
    else
      output = n * factorial(n - 1)
    end if
  end function factorial

  integer function add_one(n) result(output)
    integer, intent(in) :: n
    output = n + 1
  end function add_one
end module fruntime_recursion_f90
