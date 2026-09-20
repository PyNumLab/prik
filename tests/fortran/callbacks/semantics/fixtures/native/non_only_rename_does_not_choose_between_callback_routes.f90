module callback_types
  abstract interface
    subroutine x(value)
      real, intent(in) :: value
    end subroutine x
    subroutine y(value)
      integer, intent(in) :: value
    end subroutine y
  end interface
end module callback_types

module callback_user
  use callback_types, x => y
contains
  subroutine apply_x(callback)
    procedure(x) :: callback
  end subroutine apply_x
  subroutine apply_y(callback)
    procedure(y) :: callback
  end subroutine apply_y
end module callback_user
