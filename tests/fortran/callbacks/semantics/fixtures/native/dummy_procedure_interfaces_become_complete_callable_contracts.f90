module callbacks
  type :: point_t
    real(8) :: x
  end type point_t
    abstract interface
      function transform_iface(count, values, point) result(output)
        import :: point_t
        integer, intent(in) :: count
        real(8), intent(in) :: values(count)
        type(point_t), intent(in) :: point
        real(8) :: output(count)
      end function transform_iface
      subroutine no_intent_iface(count, values)
        integer :: count
        real(8) :: values(count)
      end subroutine no_intent_iface
      subroutine value_iface(value, ref)
        integer, value, intent(in) :: value
        real(8) :: ref
      end subroutine value_iface
      subroutine notify_iface(value)
        integer, intent(in) :: value
      end subroutine notify_iface
      subroutine string_iface(read_label, write_label, update_label)
        character(len=8), intent(in) :: read_label
        character(len=8), intent(out) :: write_label
        character(len=8), intent(inout) :: update_label
      end subroutine string_iface
  end interface
contains
  subroutine abstract_case(callback)
    procedure(transform_iface) :: callback
  end subroutine abstract_case
  subroutine explicit_case(callback)
    interface
      integer function callback(value) result(output)
        integer, intent(in) :: value
      end function callback
    end interface
  end subroutine explicit_case
  subroutine notify_case(callback)
    procedure(notify_iface) :: callback
  end subroutine notify_case
  subroutine no_intent_case(callback)
    procedure(no_intent_iface) :: callback
  end subroutine no_intent_case
  subroutine value_case(callback)
    procedure(value_iface) :: callback
  end subroutine value_case
  subroutine string_case(callback)
    procedure(string_iface) :: callback
  end subroutine string_case
end module callbacks
