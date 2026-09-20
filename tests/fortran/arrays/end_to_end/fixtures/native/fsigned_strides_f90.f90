module fsigned_strides_f90
  use iso_c_binding
  implicit none

  type :: holder
    real(8), pointer :: field_ptr(:) => null()
  end type holder

  real(8), target :: store(24)
  real(8), pointer :: reversed_ptr(:) => null()
  real(8), pointer :: strided_ptr(:) => null()
  real(8), pointer :: unassociated_ptr(:) => null()
  type(holder) :: parent
  character(len=4), allocatable, target :: words(:)
  character(len=4), pointer :: reversed_words(:) => null()

contains

  subroutine setup()
    integer :: i

    do i = 1, 24
      store(i) = real(i, kind=8)
    end do
    reversed_ptr => store(8:1:-1)
    strided_ptr => store(1:8:2)
    parent%field_ptr => store(6:1:-1)
    if (allocated(words)) deallocate(words)
    allocate(words(4))
    words = ['abcd', 'efgh', 'ijkl', 'mnop']
    reversed_words => words(4:1:-1)
  end subroutine setup

  ! Bridged assumed-shape: not bind(C), so a bridge exists.
  function total1(a) result(t)
    real(8), intent(in) :: a(:)
    real(8) :: t

    t = sum(a)
  end function total1

  ! Direct assumed-shape: bind(C), so C calls it with no bridge at all.
  function total1_bindc(a) result(t) bind(c, name="fsigned_total1_bindc")
    real(c_double), intent(in) :: a(:)
    real(c_double) :: t

    t = sum(a)
  end function total1_bindc

  ! Weighted so that reading the axes in the wrong order changes the answer.
  function checksum2(a) result(t)
    real(8), intent(in) :: a(:, :)
    real(8) :: t
    integer :: i, j

    t = 0.0_8
    do j = 1, size(a, 2)
      do i = 1, size(a, 1)
        t = t + a(i, j) * (100.0_8 * i + 10.0_8 * j)
      end do
    end do
  end function checksum2

  function total3(a) result(t)
    real(8), intent(in) :: a(:, :, :)
    real(8) :: t

    t = sum(a)
  end function total3

  subroutine negate1(a)
    real(8), intent(inout) :: a(:)

    a = -a
  end subroutine negate1

  ! Two descriptor dummies in one call.
  function dot2(a, b) result(t)
    real(8), intent(in) :: a(:), b(:)
    real(8) :: t

    t = sum(a * b)
  end function dot2

  function optional_total(a) result(t)
    real(8), intent(in), optional :: a(:)
    real(8) :: t

    if (present(a)) then
      t = sum(a)
    else
      t = -1.0_8
    end if
  end function optional_total

  function rank_and_size(a) result(s)
    real(8), intent(in) :: a(..)
    integer(4) :: s

    s = 100_4 * int(rank(a), 4) + int(size(a), 4)
  end function rank_and_size

  ! An assumed-shape dummy always sees lower bound 1, whatever the actual had.
  function first_and_last(a) result(t)
    real(8), intent(in) :: a(:)
    real(8) :: t

    t = a(1) * 1000.0_8 + a(size(a)) + real(lbound(a, 1), kind=8)
  end function first_and_last

  ! Raw-address dummies: the declaration says the layout, nothing is conveyed.
  function explicit_total(a, n) result(t)
    integer(4), intent(in) :: n
    real(8), intent(in) :: a(n)
    real(8) :: t

    t = sum(a)
  end function explicit_total

  function flat_total(a, n) result(t)
    integer(4), intent(in) :: n
    real(8), intent(in) :: a(*)
    real(8) :: t

    t = sum(a(:n))
  end function flat_total

  function contig_total(a) result(t)
    real(8), intent(in), contiguous :: a(:)
    real(8) :: t

    t = sum(a)
  end function contig_total

  function word_width(a) result(w)
    character(len=*), intent(in) :: a(:)
    integer(4) :: w

    w = int(len(a), 4)
  end function word_width

  ! Reads every element the section names, in the section's own order.
  function word_join(a) result(joined)
    character(len=*), intent(in) :: a(:)
    character(len=64) :: joined
    integer :: i

    joined = ''
    do i = 1, size(a)
      joined = trim(joined) // a(i)
    end do
  end function word_join

  subroutine word_stamp(a)
    character(len=*), intent(inout) :: a(:)
    integer :: i

    do i = 1, size(a)
      a(i)(1:1) = achar(iachar('0') + i)
    end do
  end subroutine word_stamp
end module fsigned_strides_f90
