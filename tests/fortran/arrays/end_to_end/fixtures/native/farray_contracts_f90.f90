
module farray_contracts_f90
contains
  real(8) function sum_assumed_size(n, values) result(total)
    integer, intent(in) :: n
    real(8), intent(in) :: values(*)
    integer :: i

    total = 0.0_8
    do i = 1, n
      total = total + values(i)
    end do
  end function sum_assumed_size

  subroutine scale_lower(n, values)
    integer, intent(in) :: n
    real(8), intent(inout) :: values(0:n - 1)

    values = values * 2.0_8
  end subroutine scale_lower

  real(8) function sum_in(values) result(total)
    real(8), intent(in) :: values(:)

    total = sum(values)
  end function sum_in

  subroutine bump_inout(values)
    real(8), intent(inout) :: values(:)

    values = values + 1.0_8
  end subroutine bump_inout

  subroutine fill_out(values)
    real(8), intent(out) :: values(:)

    values = 7.0_8
  end subroutine fill_out

  subroutine shift1(values, out)
    real(8), intent(in) :: values(:)
    real(8), intent(out) :: out(:)

    out = values + 1.0_8
  end subroutine shift1

  subroutine shift2(values, out)
    real(8), intent(in) :: values(:, :)
    real(8), intent(out) :: out(:, :)

    out = values + 2.0_8
  end subroutine shift2

  subroutine shift3(values, out)
    real(8), intent(in) :: values(:, :, :)
    real(8), intent(out) :: out(:, :, :)

    out = values + 3.0_8
  end subroutine shift3

  subroutine shift4(values, out)
    real(8), intent(in) :: values(:, :, :, :)
    real(8), intent(out) :: out(:, :, :, :)

    out = values + 4.0_8
  end subroutine shift4

  subroutine shift5(values, out)
    real(8), intent(in) :: values(:, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :)

    out = values + 5.0_8
  end subroutine shift5

  subroutine shift6(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :)

    out = values + 6.0_8
  end subroutine shift6

  subroutine shift7(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :)

    out = values + 7.0_8
  end subroutine shift7

  subroutine shift8(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :)

    out = values + 8.0_8
  end subroutine shift8

  subroutine shift9(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :, :)

    out = values + 9.0_8
  end subroutine shift9

  subroutine shift10(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :, :, :)

    out = values + 10.0_8
  end subroutine shift10

  subroutine shift11(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :, :, :, :)

    out = values + 11.0_8
  end subroutine shift11

  subroutine shift12(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :, :, :, :, :)

    out = values + 12.0_8
  end subroutine shift12

  subroutine shift13(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :, :, :, :, :, :)

    out = values + 13.0_8
  end subroutine shift13

  subroutine shift14(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :, :, :, :, :, :, :)

    out = values + 14.0_8
  end subroutine shift14

  subroutine shift15(values, out)
    real(8), intent(in) :: values(:, :, :, :, :, :, :, :, :, :, :, :, :, :, :)
    real(8), intent(out) :: out(:, :, :, :, :, :, :, :, :, :, :, :, :, :, :)

    out = values + 15.0_8
  end subroutine shift15

end module farray_contracts_f90
