module ucs4_strings
  implicit none
  integer, parameter :: ucs4 = selected_char_kind('ISO_10646')

  character(kind=ucs4, len=4) :: label = ucs4_'abcd'
  character(kind=ucs4, len=:), allocatable :: note
  character(kind=ucs4, len=2) :: grid(3) = [character(kind=ucs4, len=2) :: ucs4_'aa', ucs4_'bb', ucs4_'cc']
  character(kind=ucs4, len=3), allocatable :: words(:)

  type :: record
    character(kind=ucs4, len=3) :: code = ucs4_'xyz'
  end type record

  abstract interface
    subroutine visitor(text)
      import :: ucs4
      character(kind=ucs4, len=3), intent(in) :: text
    end subroutine visitor
  end interface
contains
  function count_code(text, code) result(n)
    character(kind=ucs4, len=*), intent(in) :: text
    integer, intent(in) :: code
    integer :: n, i
    n = 0
    do i = 1, len(text)
      if (ichar(text(i:i)) == code) n = n + 1
    end do
  end function count_code

  function tag() result(text)
    character(kind=ucs4, len=3) :: text
    text = char(960, ucs4) // ucs4_'ab'
  end function tag

  subroutine reverse(text)
    character(kind=ucs4, len=4), intent(inout) :: text
    text = text(4:4) // text(3:3) // text(2:2) // text(1:1)
  end subroutine reverse

  function describe(n) result(text)
    integer, intent(in) :: n
    character(kind=ucs4, len=:), allocatable :: text
    text = repeat(char(960, ucs4), n)
  end function describe

  subroutine grow(text)
    character(kind=ucs4, len=:), allocatable, intent(inout) :: text
    text = text // char(20013, ucs4)
  end subroutine grow

  subroutine shift(items)
    character(kind=ucs4, len=2), intent(inout) :: items(:)
    items = items(size(items):1:-1)
  end subroutine shift

  function pair() result(items)
    character(kind=ucs4, len=2) :: items(2)
    items = [character(kind=ucs4, len=2) :: char(960, ucs4) // ucs4_'1', ucs4_'z2']
  end function pair

  subroutine each(f)
    procedure(visitor) :: f
    call f(ucs4_'ab' // char(960, ucs4))
  end subroutine each

  subroutine fill_words()
    allocate(words(2))
    words = [character(kind=ucs4, len=3) :: ucs4_'abc', char(960, ucs4) // ucs4_'xy']
  end subroutine fill_words

  function label_code(i) result(code)
    integer, intent(in) :: i
    integer :: code
    code = ichar(label(i:i))
  end function label_code
end module ucs4_strings
