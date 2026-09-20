module second_mod
  implicit none
  type :: box
    real(8) :: weight = 2.0d0
  end type box
  abstract interface
    function producer() result(out)
      import :: box
      type(box) :: out
    end function producer
  end interface
contains
  real(8) function weigh(make) result(total)
    procedure(producer) :: make
    type(box) :: item
    item = make()
    total = item%weight
  end function weigh
end module second_mod
