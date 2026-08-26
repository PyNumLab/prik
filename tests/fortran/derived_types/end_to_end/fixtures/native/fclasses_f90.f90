module fclasses_f90
  implicit none

  type :: vector
    real(8) :: x
    real(8) :: y
  contains
    procedure :: scale
    procedure, pass(owner) :: shift => shift_vector
    procedure :: magnitude
  end type vector

  type :: vector_store
    real(8), allocatable :: values(:)
    real(8), allocatable :: matrix(:, :)
  contains
    procedure :: allocate_values
    procedure :: set_values
    procedure :: allocate_matrix
    procedure :: set_matrix
    procedure, nopass :: make => make_vector_store
  end type vector_store

contains
  subroutine scale(self, factor)
    class(vector), intent(inout) :: self
    real(8), intent(in) :: factor

    self%x = self%x * factor
    self%y = self%y * factor
  end subroutine scale

  subroutine shift_vector(dx, owner, dy)
    real(8), intent(in) :: dx
    class(vector), intent(inout) :: owner
    real(8), intent(in) :: dy

    owner%x = owner%x + dx
    owner%y = owner%y + dy
  end subroutine shift_vector

  function magnitude(self) result(value)
    class(vector), intent(in) :: self
    real(8) :: value

    value = sqrt(self%x * self%x + self%y * self%y)
  end function magnitude

  subroutine allocate_values(self, n)
    class(vector_store), intent(inout) :: self
    integer(8), intent(in) :: n

    if (allocated(self%values)) then
      deallocate(self%values)
    end if
    allocate(self%values(n))
  end subroutine allocate_values

  subroutine set_values(self, source)
    class(vector_store), intent(inout) :: self
    real(8), intent(in) :: source(:)

    if (allocated(self%values)) then
      deallocate(self%values)
    end if
    allocate(self%values(size(source, 1)))
    self%values = source
  end subroutine set_values

  subroutine allocate_matrix(self, rows, cols)
    class(vector_store), intent(inout) :: self
    integer(8), intent(in) :: rows
    integer(8), intent(in) :: cols

    if (allocated(self%matrix)) then
      deallocate(self%matrix)
    end if
    allocate(self%matrix(rows, cols))
  end subroutine allocate_matrix

  subroutine set_matrix(self, source)
    class(vector_store), intent(inout) :: self
    real(8), intent(in) :: source(:, :)

    if (allocated(self%matrix)) then
      deallocate(self%matrix)
    end if
    allocate(self%matrix(size(source, 1), size(source, 2)))
    self%matrix = source
  end subroutine set_matrix

  function make_vector_store(n, fill_value) result(self)
    integer(8), intent(in) :: n
    real(8), intent(in) :: fill_value
    type(vector_store) :: self

    allocate(self%values(n))
    self%values = fill_value
  end function make_vector_store
end module fclasses_f90
