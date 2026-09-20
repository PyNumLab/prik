module declaration_extent_expressions
  use, intrinsic :: iso_c_binding, only: c_double
  implicit none

  integer, parameter :: base_extent = 2
  integer, parameter :: field_extent = max(3, base_extent + 1)

  type :: record
    real(c_double) :: values(field_extent)
  end type record

  real(c_double), target :: module_values(base_extent ** 2)
  type(record), target :: current

contains

  pure integer function local_extent(n) result(extent)
    integer, intent(in) :: n
    extent = max(0, n)
  end function local_extent

  subroutine initialize_state()
    module_values = [1.0_c_double, 2.0_c_double, 3.0_c_double, 4.0_c_double]
    current%values = [5.0_c_double, 6.0_c_double, 7.0_c_double]
  end subroutine initialize_state

  subroutine exercise_inquiries( &
      source, destination, total, rank_values, reduced, constructed, conditional, lower_bound, upper_bound)
    real(c_double), intent(in) :: source(2:, 2:)
    real(c_double), intent(out) :: destination( &
      ubound(source, 1) - lbound(source, 1) + 1, &
      max(1, size(source, dim=2, kind=8)))
    real(c_double), intent(out) :: total(size(source, kind=8))
    real(c_double), intent(out) :: rank_values(2 ** rank(source))
    real(c_double), intent(out) :: reduced(sum(shape(source, kind=8)))
    real(c_double), intent(out) :: constructed(product((/ size(source, 1), 1 /)))
    real(c_double), intent(out) :: conditional(merge(size(source, 1), 1, size(source, 2) > 0))
    real(c_double), intent(out) :: lower_bound(lbound(source, 1))
    real(c_double), intent(out) :: upper_bound(ubound(source, 1))

    destination = source
    total = reshape(source, [size(source)])
    rank_values = 8.0_c_double
    reduced = 9.0_c_double
    constructed = 10.0_c_double
    conditional = 11.0_c_double
    lower_bound = 12.0_c_double
    upper_bound = 13.0_c_double
  end subroutine exercise_inquiries

  function copied(source) result(values)
    real(c_double), intent(in) :: source(:, :)
    real(c_double) :: values(size(source, 1), size(source, 2))
    values = source
  end function copied

  function local_extent_values(n) result(values)
    integer, intent(in) :: n
    real(c_double) :: values(local_extent(n))
    values = 14.0_c_double
  end function local_extent_values

  subroutine fill_local_extent(n, values)
    integer, intent(in) :: n
    real(c_double), intent(out) :: values(local_extent(n))
    values = 15.0_c_double
  end subroutine fill_local_extent

end module declaration_extent_expressions
