module foperators_f90
  implicit none
  private

  public :: vector, offset, counter, convert
  public :: operator(+), operator(-), operator(*), operator(/), operator(**)
  public :: operator(==), operator(/=), operator(<), operator(<=), operator(>), operator(>=)
  public :: operator(.and.), operator(.or.), operator(.not.), operator(.eqv.), operator(.neqv.)
  public :: operator(.dot.), operator(.shift.)
  public :: assignment(=)

  interface convert
    module procedure convert_integer
    module procedure convert_real
  end interface convert

  type :: vector
    real(8) :: value = 0.0d0
  end type vector

  type :: offset
    real(8) :: value = 0.0d0
  end type offset

  type :: counter
    integer :: value = 0
  contains
    procedure, private :: add_integer => counter_add_integer
    generic, public :: operator(+) => add_integer
  end type counter

  interface operator(+)
    module procedure add_vectors
    module procedure add_vector_integer
    module procedure add_vector_real
    module procedure add_real_vector
    module procedure add_vector_array
    module procedure add_vector_offset
    module procedure positive_vector
  end interface operator(+)

  interface operator(-)
    module procedure subtract_vector_real
    module procedure subtract_real_vector
    module procedure negative_vector
  end interface operator(-)

  interface operator(*)
    module procedure multiply_vector_real
  end interface operator(*)

  interface operator(/)
    module procedure divide_vector_real
  end interface operator(/)

  interface operator(**)
    module procedure power_vector_integer
  end interface operator(**)

  interface operator(==)
    module procedure equal_vectors
  end interface operator(==)

  interface operator(/=)
    module procedure not_equal_vectors
  end interface operator(/=)

  interface operator(<)
    module procedure less_vectors
    module procedure less_vector_real
    module procedure less_real_vector
  end interface operator(<)

  interface operator(<=)
    module procedure less_equal_vectors
  end interface operator(<=)

  interface operator(>)
    module procedure greater_vectors
  end interface operator(>)

  interface operator(>=)
    module procedure greater_equal_vectors
  end interface operator(>=)

  interface operator(.and.)
    module procedure and_vectors
  end interface operator(.and.)

  interface operator(.or.)
    module procedure or_vectors
  end interface operator(.or.)

  interface operator(.not.)
    module procedure not_vector
  end interface operator(.not.)

  interface operator(.eqv.)
    module procedure equivalent_vector_offset
  end interface operator(.eqv.)

  interface operator(.neqv.)
    module procedure not_equivalent_vector_integer
  end interface operator(.neqv.)

  interface operator(.dot.)
    module procedure dot_vectors
  end interface operator(.dot.)

  interface operator(.shift.)
    module procedure shift_real_vector
  end interface operator(.shift.)

  interface assignment(=)
    module procedure assign_vector_integer
    module procedure assign_vector_real
  end interface assignment(=)

contains

  integer function convert_integer(value) result(output)
    integer, intent(in) :: value
    output = value + 10
  end function convert_integer

  real(8) function convert_real(value) result(output)
    real(8), intent(in) :: value
    output = value + 0.5d0
  end function convert_real

  type(vector) function add_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output%value = left%value + right%value
  end function add_vectors

  type(vector) function add_vector_integer(left, right) result(output)
    type(vector), intent(in) :: left
    integer, intent(in) :: right
    output%value = left%value + real(right, kind=8)
  end function add_vector_integer

  type(vector) function add_vector_real(left, right) result(output)
    type(vector), intent(in) :: left
    real(8), intent(in) :: right
    output%value = left%value + right
  end function add_vector_real

  type(vector) function add_real_vector(left, right) result(output)
    real(8), intent(in) :: left
    type(vector), intent(in) :: right
    output%value = left + right%value + 100.0d0
  end function add_real_vector

  type(vector) function add_vector_array(left, right) result(output)
    type(vector), intent(in) :: left
    real(8), intent(in) :: right(:)
    output%value = left%value + sum(right)
  end function add_vector_array

  type(vector) function add_vector_offset(left, right) result(output)
    type(vector), intent(in) :: left
    type(offset), intent(in) :: right
    output%value = left%value + right%value
  end function add_vector_offset

  type(vector) function positive_vector(value) result(output)
    type(vector), intent(in) :: value
    output%value = value%value
  end function positive_vector

  type(vector) function subtract_vector_real(left, right) result(output)
    type(vector), intent(in) :: left
    real(8), intent(in) :: right
    output%value = left%value - right
  end function subtract_vector_real

  type(vector) function subtract_real_vector(left, right) result(output)
    real(8), intent(in) :: left
    type(vector), intent(in) :: right
    output%value = left - right%value
  end function subtract_real_vector

  type(vector) function negative_vector(value) result(output)
    type(vector), intent(in) :: value
    output%value = -value%value
  end function negative_vector

  type(vector) function multiply_vector_real(left, right) result(output)
    type(vector), intent(in) :: left
    real(8), intent(in) :: right
    output%value = left%value * right
  end function multiply_vector_real

  type(vector) function divide_vector_real(left, right) result(output)
    type(vector), intent(in) :: left
    real(8), intent(in) :: right
    output%value = left%value / right
  end function divide_vector_real

  type(vector) function power_vector_integer(left, right) result(output)
    type(vector), intent(in) :: left
    integer, intent(in) :: right
    output%value = left%value ** right
  end function power_vector_integer

  logical function equal_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value == right%value
  end function equal_vectors

  logical function not_equal_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value /= right%value
  end function not_equal_vectors

  logical function less_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value < right%value
  end function less_vectors

  logical function less_vector_real(left, right) result(output)
    type(vector), intent(in) :: left
    real(8), intent(in) :: right
    output = left%value < right
  end function less_vector_real

  logical function less_real_vector(left, right) result(output)
    real(8), intent(in) :: left
    type(vector), intent(in) :: right
    output = left < right%value
  end function less_real_vector

  logical function less_equal_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value <= right%value
  end function less_equal_vectors

  logical function greater_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value > right%value
  end function greater_vectors

  logical function greater_equal_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value >= right%value
  end function greater_equal_vectors

  logical function and_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value /= 0.0d0 .and. right%value /= 0.0d0
  end function and_vectors

  logical function or_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value /= 0.0d0 .or. right%value /= 0.0d0
  end function or_vectors

  logical function not_vector(value) result(output)
    type(vector), intent(in) :: value
    output = .not. (value%value /= 0.0d0)
  end function not_vector

  logical function equivalent_vector_offset(left, right) result(output)
    type(vector), intent(in) :: left
    type(offset), intent(in) :: right
    output = (left%value /= 0.0d0) .eqv. (right%value /= 0.0d0)
  end function equivalent_vector_offset

  logical function not_equivalent_vector_integer(left, right) result(output)
    type(vector), intent(in) :: left
    integer, intent(in) :: right
    output = (left%value /= 0.0d0) .neqv. (right /= 0)
  end function not_equivalent_vector_integer

  real(8) function dot_vectors(left, right) result(output)
    type(vector), intent(in) :: left, right
    output = left%value * right%value
  end function dot_vectors

  type(vector) function shift_real_vector(left, right) result(output)
    real(8), intent(in) :: left
    type(vector), intent(in) :: right
    output%value = left + right%value + 200.0d0
  end function shift_real_vector

  subroutine assign_vector_integer(left, right)
    type(vector), intent(out) :: left
    integer, intent(in) :: right
    left%value = real(right, kind=8)
  end subroutine assign_vector_integer

  subroutine assign_vector_real(left, right)
    type(vector), intent(out) :: left
    real(8), intent(in) :: right
    left%value = right
  end subroutine assign_vector_real

  type(counter) function counter_add_integer(self, right) result(output)
    class(counter), intent(in) :: self
    integer, intent(in) :: right
    output%value = self%value + right
  end function counter_add_integer

end module foperators_f90
