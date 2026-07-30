module fallocatable_views_f90
  implicit none
  private

  public :: buffer
  public :: module_values
  public :: allocate_module_values, deallocate_module_values, scale_module_values
  public :: module_values_sum
  public :: build_values, build_matrix, make_values, make_matrix, replace_values
  public :: zero_alloc_vector, zero_alloc_matrix
  public :: maybe_alloc_vector, maybe_alloc_matrix

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

    allocate(values(max(n, 0)))
    do i = 1, n
      values(i) = real(i * 3, kind=8)
    end do
  end function make_values

  subroutine replace_values(values, mode)
    real(8), allocatable, intent(inout) :: values(:)
    integer, intent(in) :: mode
    integer :: i

    if (mode == 0) then
      if (allocated(values)) deallocate(values)
    else if (mode == 1) then
      if (allocated(values)) then
        values = values + 10.0_8
      else
        allocate(values(2))
        values = [1.0_8, 2.0_8]
      end if
    else
      if (allocated(values)) deallocate(values)
      allocate(values(3))
      do i = 1, 3
        values(i) = real(i * mode, 8)
      end do
    end if
  end subroutine replace_values

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
