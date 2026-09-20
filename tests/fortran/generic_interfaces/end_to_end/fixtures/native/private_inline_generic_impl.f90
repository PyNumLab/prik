submodule(private_inline_generic) private_inline_generic_impl
contains
  module procedure shift_integer
    output = value + 1
  end procedure shift_integer

  module procedure shift_real
    output = value + 0.5_8
  end procedure shift_real
end submodule private_inline_generic_impl
