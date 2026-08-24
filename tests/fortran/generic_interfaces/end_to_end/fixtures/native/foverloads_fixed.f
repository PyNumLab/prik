      module foverloads_fixed
      implicit none
      private
      public :: convert

      interface convert
      module procedure convert_integer
      module procedure convert_real
      end interface convert

      contains

      integer function convert_integer(value) result(converted)
      integer, intent(in) :: value
      converted = value + 20
      end function convert_integer

      real(8) function convert_real(value) result(converted)
      real(8), intent(in) :: value
      converted = value + 0.25d0
      end function convert_real

      end module foverloads_fixed
