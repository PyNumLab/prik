module multid_arrays
  implicit none

contains

  subroutine scale2_contiguous(a, out)
    implicit none

    real(8), contiguous, intent(in) :: a(:, :)
    real(8), contiguous, intent(out) :: out(:, :)

    out = 2.0d0 * a
  end subroutine scale2_contiguous

  subroutine scale2_strided(a, out)
    implicit none

    real(8), intent(in) :: a(:, :)
    real(8), intent(out) :: out(:, :)

    out = 3.0d0 * a
  end subroutine scale2_strided

  subroutine checksum2_strided(a, checksum)
    implicit none

    real(8), intent(in) :: a(:, :)
    real(8), intent(out) :: checksum(1)
    integer :: i
    integer :: j

    checksum(1) = 0.0d0
    do j = 1, size(a, 2)
      do i = 1, size(a, 1)
        checksum(1) = checksum(1) + a(i, j) * &
              (1000.0d0 * real(i, 8) + 10.0d0 * real(j, 8))
      end do
    end do
  end subroutine checksum2_strided

  subroutine scale2_explicit(rows, cols, a, out)
    implicit none

    integer, intent(in) :: rows
    integer, intent(in) :: cols
    real(8), intent(in) :: a(rows, cols)
    real(8), intent(out) :: out(rows, cols)

    out = 4.0d0 * a
  end subroutine scale2_explicit

  subroutine shift3_contiguous(a, out)
    implicit none

    real(8), contiguous, intent(in) :: a(:, :, :)
    real(8), contiguous, intent(out) :: out(:, :, :)

    out = a + 10.0d0
  end subroutine shift3_contiguous

  subroutine shift3_strided(a, out)
    implicit none

    real(8), intent(in) :: a(:, :, :)
    real(8), intent(out) :: out(:, :, :)

    out = a + 20.0d0
  end subroutine shift3_strided

  subroutine checksum3_strided(a, checksum)
    implicit none

    real(8), intent(in) :: a(:, :, :)
    real(8), intent(out) :: checksum(1)
    integer :: i
    integer :: j
    integer :: k

    checksum(1) = 0.0d0
    do k = 1, size(a, 3)
      do j = 1, size(a, 2)
        do i = 1, size(a, 1)
          checksum(1) = checksum(1) + a(i, j, k) * &
                (10000.0d0 * real(i, 8) + 100.0d0 * real(j, 8) + &
                real(k, 8))
        end do
      end do
    end do
  end subroutine checksum3_strided

end module multid_arrays
