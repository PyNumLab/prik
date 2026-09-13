module kernel
  implicit none
contains

  pure function diffuse(values, rate) result(output)
    !! One explicit diffusion step across an interior with fixed boundaries.
    real(8), intent(in) :: values(:)
    real(8), intent(in) :: rate
    real(8) :: output(size(values))
    integer :: cell

    output = values
    do cell = 2, size(values) - 1
      output(cell) = values(cell) + rate * (values(cell - 1) - 2 * values(cell) + values(cell + 1))
    end do
  end function diffuse

  pure function total(values) result(amount)
    !! The quantity a caller can compare before and after any number of steps.
    real(8), intent(in) :: values(:)
    real(8) :: amount

    amount = sum(values)
  end function total

end module kernel
