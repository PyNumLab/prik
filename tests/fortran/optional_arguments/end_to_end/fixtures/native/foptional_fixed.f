
      integer function optional_scale(base, factor)
      integer, intent(in) :: base
      integer, intent(in), optional :: factor
      optional_scale = base
      if (present(factor)) optional_scale = optional_scale + factor
      end function optional_scale
