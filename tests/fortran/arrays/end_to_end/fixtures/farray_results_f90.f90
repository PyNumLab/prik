
module farray_results_f90
contains
  function fixed_vector() result(values)
    real(8) :: values(3)

    values = [1.0_8, 2.0_8, 3.0_8]
  end function fixed_vector

  function automatic_vector(n) result(values)
    integer, intent(in) :: n
    real(8) :: values(n)
    integer :: i

    do i = 1, n
      values(i) = real(i, 8) * 2.0_8
    end do
  end function automatic_vector

  function size_intrinsic_vector(x) result(values)
    real(8), intent(in) :: x(:)
    real(8), dimension(size(x)) :: values

    values = 3.0_8 * x
  end function size_intrinsic_vector

  function automatic_matrix(rows, cols) result(values)
    integer, intent(in) :: rows
    integer, intent(in) :: cols
    real(8) :: values(0:rows - 1, 2:cols + 1)
    integer :: i
    integer :: j

    do j = 2, cols + 1
      do i = 0, rows - 1
        values(i, j) = real(10 * (i + 1) + j, 8)
      end do
    end do
  end function automatic_matrix

  function rank3_cube(n1, n2, n3) result(values)
    integer, intent(in) :: n1
    integer, intent(in) :: n2
    integer, intent(in) :: n3
    real(8) :: values(n1, n2, n3)
    integer :: i
    integer :: j
    integer :: k

    do k = 1, n3
      do j = 1, n2
        do i = 1, n1
          values(i, j, k) = real(100 * i + 10 * j + k, 8)
        end do
      end do
    end do
  end function rank3_cube

  function rank1_result() result(values)
    real(8) :: values(2)

    values = real(1, 8)
    values(2) = real(1, 8) + 0.5_8
  end function rank1_result

  function rank2_result() result(values)
    real(8) :: values(2, 1)

    values = real(2, 8)
    values(2, 1) = real(2, 8) + 0.5_8
  end function rank2_result

  function rank3_result() result(values)
    real(8) :: values(2, 1, 1)

    values = real(3, 8)
    values(2, 1, 1) = real(3, 8) + 0.5_8
  end function rank3_result

  function rank4_result() result(values)
    real(8) :: values(2, 1, 1, 1)

    values = real(4, 8)
    values(2, 1, 1, 1) = real(4, 8) + 0.5_8
  end function rank4_result

  function rank5_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1)

    values = real(5, 8)
    values(2, 1, 1, 1, 1) = real(5, 8) + 0.5_8
  end function rank5_result

  function rank6_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1)

    values = real(6, 8)
    values(2, 1, 1, 1, 1, 1) = real(6, 8) + 0.5_8
  end function rank6_result

  function rank7_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1)

    values = real(7, 8)
    values(2, 1, 1, 1, 1, 1, 1) = real(7, 8) + 0.5_8
  end function rank7_result

  function rank8_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1)

    values = real(8, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1) = real(8, 8) + 0.5_8
  end function rank8_result

  function rank9_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1, 1)

    values = real(9, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1, 1) = real(9, 8) + 0.5_8
  end function rank9_result

  function rank10_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    values = real(10, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1) = real(10, 8) + 0.5_8
  end function rank10_result

  function rank11_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    values = real(11, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1) = real(11, 8) + 0.5_8
  end function rank11_result

  function rank12_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    values = real(12, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1) = real(12, 8) + 0.5_8
  end function rank12_result

  function rank13_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    values = real(13, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1) = real(13, 8) + 0.5_8
  end function rank13_result

  function rank14_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    values = real(14, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1) = real(14, 8) + 0.5_8
  end function rank14_result

  function rank15_result() result(values)
    real(8) :: values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    values = real(15, 8)
    values(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1) = real(15, 8) + 0.5_8
  end function rank15_result


  function zero_vector() result(values)
    real(8) :: values(0)
  end function zero_vector

  function zero_alloc_vector() result(values)
    real(8), allocatable :: values(:)

    allocate(values(0))
  end function zero_alloc_vector

  function maybe_alloc_vector(n) result(values)
    integer, intent(in) :: n
    real(8), allocatable :: values(:)
    integer :: i

    if (n > 0) then
      allocate(values(n))
      do i = 1, n
        values(i) = real(5 * i, 8)
      end do
    end if
  end function maybe_alloc_vector

  function zero_alloc_matrix(cols) result(values)
    integer, intent(in) :: cols
    real(8), allocatable :: values(:, :)

    allocate(values(0, cols))
  end function zero_alloc_matrix

  function maybe_alloc_matrix(rows, cols) result(values)
    integer, intent(in) :: rows
    integer, intent(in) :: cols
    real(8), allocatable :: values(:, :)
    integer :: i
    integer :: j

    if (rows > 0 .and. cols > 0) then
      allocate(values(rows, cols))
      do j = 1, cols
        do i = 1, rows
          values(i, j) = real(100 * i + 10 * j, 8)
        end do
      end do
    end if
  end function maybe_alloc_matrix
end module farray_results_f90
