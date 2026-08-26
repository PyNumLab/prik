module module1
  implicit none
contains
  integer(4) function func1()
    func1 = 1
  end function func1

  integer(4) function update()
    update = 11
  end function update
end module module1

module module2
  implicit none
contains
  integer(4) function func2()
    func2 = 2
  end function func2

  integer(4) function update()
    update = 22
  end function update
end module module2

integer(4) function standalone()
  standalone = 3
end function standalone
