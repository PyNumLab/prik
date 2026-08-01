module kernels
    implicit none

contains

    subroutine noop()
    end subroutine noop

    function add_scalars(a, b) result(c)
        double precision, intent(in) :: a, b
        double precision :: c

        c = a + b
    end function add_scalars

    subroutine increment_vector(x)
        double precision, intent(inout), contiguous :: x(:)
        integer :: i

        do i = 1, size(x)
            x(i) = x(i) + 1.0d0
        end do
    end subroutine increment_vector

    function sum_matrix(a) result(total)
        double precision, intent(in) :: a(:, :)
        double precision :: total
        integer :: i, j

        total = 0.0d0

        do j = 1, size(a, 2)
            do i = 1, size(a, 1)
                total = total + a(i, j)
            end do
        end do
    end function sum_matrix

    subroutine matrix_update(a, value)
        double precision, intent(inout), contiguous :: a(:, :)
        double precision, intent(in) :: value
        integer :: i, j

        do j = 1, size(a, 2)
            do i = 1, size(a, 1)
                a(i, j) = a(i, j) + value
            end do
        end do
    end subroutine matrix_update

end module kernels
