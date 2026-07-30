module foverloads_f90
  implicit none
  private

  public :: accumulator, sample, convert, inspect, summarize

  interface convert
    module procedure convert_integer
    module procedure convert_real
    module procedure convert_complex
  end interface convert

  interface summarize
    module procedure summarize_scalar
    module procedure summarize_vector
  end interface summarize

  interface inspect
    module procedure inspect_accumulator
    module procedure inspect_sample
  end interface inspect

  type :: accumulator
    real(8) :: total = 0.0d0
  contains
    procedure, private :: add_integer => accumulator_add_integer
    procedure, private :: add_real => accumulator_add_real
    generic, public :: add => add_integer, add_real
  end type accumulator

  type :: sample
    real(8) :: value = 0.0d0
  end type sample

contains

  integer function convert_integer(value) result(converted)
    integer, intent(in) :: value
    converted = value + 10
  end function convert_integer

  real(8) function convert_real(value) result(converted)
    real(8), intent(in) :: value
    converted = value + 0.5d0
  end function convert_real

  complex(8) function convert_complex(value) result(converted)
    complex(8), intent(in) :: value
    converted = value + cmplx(1.0d0, -1.0d0, kind=8)
  end function convert_complex

  real(8) function summarize_scalar(value) result(summary)
    real(8), intent(in) :: value
    summary = value
  end function summarize_scalar

  real(8) function summarize_vector(values) result(summary)
    real(8), intent(in) :: values(:)
    summary = sum(values)
  end function summarize_vector

  real(8) function inspect_accumulator(value) result(summary)
    type(accumulator), intent(in) :: value
    summary = value%total
  end function inspect_accumulator

  real(8) function inspect_sample(value) result(summary)
    type(sample), intent(in) :: value
    summary = value%value
  end function inspect_sample

  subroutine accumulator_add_integer(self, value)
    class(accumulator), intent(inout) :: self
    integer, intent(in) :: value
    self%total = self%total + real(value, kind=8)
  end subroutine accumulator_add_integer

  subroutine accumulator_add_real(self, value)
    class(accumulator), intent(inout) :: self
    real(8), intent(in) :: value
    self%total = self%total + value
  end subroutine accumulator_add_real

end module foverloads_f90
