module fallocatable_views_f90
  implicit none
  private

  public :: buffer
  public :: module_values
  public :: allocate_module_values, deallocate_module_values, scale_module_values
  public :: module_values_sum
  public :: build_values, build_matrix, make_values, make_matrix

  real(8), allocatable, target :: module_values(:)

  type :: buffer
    real(8), allocatable :: values(:)
  contains
    procedure, public :: allocate_values
    procedure, public :: deallocate_values
    procedure, public :: scale_values
    procedure, public :: values_sum
  end type buffer

contains

  subroutine allocate_module_values(n)
    integer, intent(in) :: n
    integer :: i

    if (allocated(module_values)) deallocate(module_values)
    allocate(module_values(n))
    do i = 1, n
      module_values(i) = real(i, kind=8)
    end do
  end subroutine allocate_module_values

  subroutine deallocate_module_values()
    if (allocated(module_values)) deallocate(module_values)
  end subroutine deallocate_module_values

  subroutine scale_module_values(scale)
    real(8), intent(in) :: scale

    module_values = module_values * scale
  end subroutine scale_module_values

  real(8) function module_values_sum() result(total)
    if (allocated(module_values)) then
      total = sum(module_values)
    else
      total = -1.0d0
    end if
  end function module_values_sum

  subroutine build_values(n, values)
    integer, intent(in) :: n
    real(8), allocatable, intent(out) :: values(:)
    integer :: i

    if (n <= 0) return
    allocate(values(n))
    do i = 1, n
      values(i) = real(i * 2, kind=8)
    end do
  end subroutine build_values

  subroutine build_matrix(n, m, values)
    integer, intent(in) :: n
    integer, intent(in) :: m
    real(8), allocatable, intent(out) :: values(:, :)
    integer :: i
    integer :: j

    if (n <= 0 .or. m <= 0) return
    allocate(values(n, m))
    do j = 1, m
      do i = 1, n
        values(i, j) = real(i + 10 * j, kind=8)
      end do
    end do
  end subroutine build_matrix

  function make_values(n) result(values)
    integer, intent(in) :: n
    real(8), allocatable :: values(:)
    integer :: i

    if (n <= 0) return
    allocate(values(n))
    do i = 1, n
      values(i) = real(i * 3, kind=8)
    end do
  end function make_values

  subroutine make_matrix(n, m, values)
    integer, intent(in) :: n
    integer, intent(in) :: m
    real(8), allocatable, intent(out) :: values(:, :)
    integer :: i
    integer :: j

    if (n <= 0 .or. m <= 0) return
    allocate(values(n, m))
    do j = 1, m
      do i = 1, n
        values(i, j) = real(100 + i + 10 * j, kind=8)
      end do
    end do
  end subroutine make_matrix

  subroutine allocate_values(self, n)
    class(buffer), intent(inout) :: self
    integer, intent(in) :: n
    integer :: i

    if (allocated(self%values)) deallocate(self%values)
    allocate(self%values(n))
    do i = 1, n
      self%values(i) = real(i, kind=8)
    end do
  end subroutine allocate_values

  subroutine deallocate_values(self)
    class(buffer), intent(inout) :: self

    if (allocated(self%values)) deallocate(self%values)
  end subroutine deallocate_values

  subroutine scale_values(self, scale)
    class(buffer), intent(inout) :: self
    real(8), intent(in) :: scale

    self%values = self%values * scale
  end subroutine scale_values

  real(8) function values_sum(self) result(total)
    class(buffer), intent(in) :: self

    if (allocated(self%values)) then
      total = sum(self%values)
    else
      total = -1.0d0
    end if
  end function values_sum

end module fallocatable_views_f90
