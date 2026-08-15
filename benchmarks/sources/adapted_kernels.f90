subroutine noop()
end subroutine noop

real(8) function add_scalars(a, b) result(c)
    real(8), intent(in) :: a, b

    c = a + b
end function add_scalars

subroutine add_scalars_out(a, b, c)
    real(8), intent(in) :: a, b
    real(8), intent(out) :: c

    c = a + b
end subroutine add_scalars_out
