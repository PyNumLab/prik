module ops
  use shapes, only: box, tagged_box
  implicit none
  private
  public :: holder, boxed, total, visit, describe, weigh, maybe_box, producer, consumer
  type :: holder
    type(box) :: inner
  end type holder
  abstract interface
    function producer() result(out)
      import :: box
      type(box) :: out
    end function producer
    subroutine consumer(item)
      import :: box
      type(box), intent(in) :: item
    end subroutine consumer
  end interface
  interface weigh
    module procedure weigh_box, weigh_int
  end interface weigh
contains
  function boxed(v) result(out)
    integer, intent(in) :: v
    type(box) :: out
    out%value = v
  end function boxed

  integer function total(make)
    procedure(producer) :: make
    type(box) :: item
    item = make()
    total = item%value
  end function total

  subroutine visit(fn)
    procedure(consumer) :: fn
    type(box) :: item
    item%value = 41
    call fn(item)
  end subroutine visit

  integer function describe(item)
    class(box), intent(in) :: item
    select type (item)
    type is (tagged_box)
      describe = 2
    class default
      describe = 1
    end select
  end function describe

  integer function weigh_box(item)
    type(box), intent(in) :: item
    weigh_box = item%value
  end function weigh_box

  integer function weigh_int(n)
    integer, intent(in) :: n
    weigh_int = -n
  end function weigh_int

  function maybe_box(v) result(out)
    integer, intent(in) :: v
    type(box), allocatable :: out
    allocate(out)
    out%value = v
  end function maybe_box
end module ops
