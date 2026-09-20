module compile_time_expression_examples
  use iso_fortran_env, only: real64
  implicit none

  integer, parameter :: n = 10
  integer, parameter :: m = 5
  integer, parameter :: expr_int = 2 * n + m - 3
  integer, parameter :: abs_value = abs(-12)
  integer, parameter :: max_value = max(3, 7, 2)
  integer, parameter :: mod_value = mod(17, 5)
  integer, parameter :: len_value = len("abcdef")
  integer, parameter :: len_trim_value = len_trim("abc   ")
  integer, parameter :: char_code = iachar("A")
  integer, parameter :: cast_int = int(3.9)

  character(len=len("compile")) :: length_from_len
  character(len=n) :: length_from_parameter
  character(len=len_trim("abc   ")) :: length_from_len_trim

  real(real64) :: array_from_parameter(n)
  real(real64) :: array_from_expression(2 * n + 1)
  integer :: matrix_from_constants(m, n)
  integer, parameter :: small_array(3) = [1, 2, 3]

  type :: buffer_type(k, n)
     integer, kind :: k
     integer, len  :: n
     real(kind=k) :: values(n)
  end type buffer_type

  type(buffer_type(real64, 4)) :: compile_time_buffer
end module compile_time_expression_examples
