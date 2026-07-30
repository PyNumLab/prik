module fopenmp_runtime_f90
contains
  real(8) function parallel_sum(values) result(total)
    real(8), intent(in) :: values(:)
    integer :: i
    total = 0.0_8
!$omp parallel do default(none) shared(values) reduction(+:total)
    do i = 1, size(values)
      total = total + values(i)
    end do
!$omp end parallel do
  end function parallel_sum
end module fopenmp_runtime_f90
