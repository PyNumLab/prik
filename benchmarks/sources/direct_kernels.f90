subroutine noop() bind(C)
    use iso_c_binding
end subroutine noop

real(c_double) function add_scalars(a, b) bind(C) result(c)
    use iso_c_binding
    real(c_double), value, intent(in) :: a, b

    c = a + b
end function add_scalars

subroutine add_scalars_out(a, b, c) bind(C)
    use iso_c_binding
    real(c_double), value, intent(in) :: a, b
    real(c_double), intent(out) :: c

    c = a + b
end subroutine add_scalars_out
