module refactoring_goldens
  implicit none
  private

  public :: vector, holder_item, counter, default_count, workspace, selected
  public :: active_vector, selected_vector
  public :: summarize, make_values, apply_callback, convert
  public :: reset_allocatable_item, shift_pointer_item
  public :: split_value
  public :: operator(+)

  integer(4), parameter :: default_count = 3
  integer(4) :: counter = 1
  real(8), allocatable :: workspace(:)
  real(8), pointer :: selected(:) => null()

  type :: holder_item
    integer(4) :: code = 0
    real(8) :: weight = 0.0_8
  end type holder_item

  type :: vector
    real(8) :: x = 0.0_8
    real(8) :: y = 0.0_8
    real(8), allocatable :: samples(:)
  contains
    procedure, public :: scale
    procedure, public, pass(owner) :: shift => shift_vector
    procedure, public :: magnitude
    procedure, public :: replace_samples
    final :: finalize_vector
  end type vector

  type(vector), allocatable :: active_vector
  type(vector), pointer :: selected_vector => null()

  abstract interface
    function scalar_callback(value) result(output)
      real(8), intent(in) :: value
      real(8) :: output
    end function scalar_callback
  end interface

  interface convert
    module procedure integer_to_real
    module procedure real_to_integer
  end interface convert

  interface operator(+)
    module procedure add_vectors
  end interface operator(+)

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

  subroutine replace_samples(self, values)
    class(vector), intent(inout) :: self
    real(8), intent(in) :: values(:)

    if (allocated(self%samples)) deallocate(self%samples)
    allocate(self%samples(size(values)))
    self%samples = values
  end subroutine replace_samples

  subroutine finalize_vector(self)
    type(vector), intent(inout) :: self

    if (allocated(self%samples)) deallocate(self%samples)
  end subroutine finalize_vector

  function add_vectors(left, right) result(output)
    type(vector), intent(in) :: left
    type(vector), intent(in) :: right
    type(vector) :: output

    output%x = left%x + right%x
    output%y = left%y + right%y
  end function add_vectors

  function integer_to_real(value) result(output)
    integer(4), intent(in) :: value
    real(8) :: output

    output = real(value, 8)
  end function integer_to_real

  function real_to_integer(value) result(output)
    real(8), intent(in) :: value
    integer(4) :: output

    output = int(value, 4)
  end function real_to_integer

  function summarize(required, scale, values, label, item) result(output)
    integer(4), intent(in) :: required
    integer(4), intent(in), optional :: scale
    real(8), intent(in), optional :: values(:)
    character(len=*), intent(in), optional :: label
    type(vector), intent(in), optional :: item
    integer(4) :: output

    output = required
    if (present(scale)) output = output + scale
    if (present(values)) output = output + int(sum(values), 4)
    if (present(label)) output = output + len_trim(label)
    if (present(item)) output = output + int(item%x + item%y, 4)
  end function summarize

  function make_values(count, fill_value) result(values)
    integer(4), intent(in) :: count
    real(8), intent(in) :: fill_value
    real(8), allocatable :: values(:)

    allocate(values(count))
    values = fill_value
  end function make_values

  function apply_callback(callback, value) result(output)
    procedure(scalar_callback) :: callback
    real(8), intent(in) :: value
    real(8) :: output

    output = callback(value)
  end function apply_callback

  subroutine split_value(value, doubled, status)
    real(8), intent(in) :: value
    real(8), intent(out) :: doubled
    integer(4), intent(out) :: status

    doubled = 2.0_8 * value
    status = 0
  end subroutine split_value

  subroutine reset_allocatable_item(value)
    type(holder_item), allocatable, intent(inout) :: value

    if (allocated(value)) deallocate(value)
    allocate(value)
  end subroutine reset_allocatable_item

  subroutine shift_pointer_item(value, amount)
    type(holder_item), pointer, intent(inout) :: value
    real(8), intent(in) :: amount

    if (associated(value)) then
      value%weight = value%weight + amount
    end if
  end subroutine shift_pointer_item

end module refactoring_goldens
