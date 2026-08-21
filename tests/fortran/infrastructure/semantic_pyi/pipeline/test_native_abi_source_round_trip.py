from prik.parsers.fortran import parse_fortran_file
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module


def test_bind_c_source_emits_and_loads_native_abi_with_renamed_label():
    parsed = parse_fortran_file(
        """
module native_api
  use iso_c_binding
contains
  real(c_double) function scale(value) bind(C, name="scaled_value") result(output)
    real(c_double), value, intent(in) :: value
    output = value
  end function scale
end module native_api
"""
    )
    source_module = fortran_module_to_semantic_module(parsed.modules[0])

    rendered = emit_module(source_module)
    loaded = pyi_text_to_semantic_module(rendered, module_name="native_api")
    function = loaded.functions[0]

    assert '@native_abi("c")' in rendered
    assert '@bind("scaled_value")' in rendered
    assert function.native_name == "scale"
    assert function.origin.native_name == "scale"
    assert function.origin.native_abi == "c"
    assert function.origin.native_symbol == "scaled_value"
    assert function.origin.source_language == "fortran"


def test_bind_c_callable_prototype_emits_and_loads_native_abi():
    parsed = parse_fortran_file(
        """
module callback_api
  use iso_c_binding
  abstract interface
    subroutine callback(value) bind(C)
      import c_double
      real(c_double), value :: value
    end subroutine callback
  end interface
contains
  subroutine apply(callback_argument)
    procedure(callback) :: callback_argument
  end subroutine apply
end module callback_api
"""
    )
    source_module = fortran_module_to_semantic_module(parsed.modules[0])

    rendered = emit_module(source_module)
    loaded = pyi_text_to_semantic_module(rendered, module_name="callback_api")
    prototype = loaded.prototypes[0]

    assert '@native_abi("c")' in rendered
    assert prototype.origin.source_language == "fortran"
    assert prototype.origin.native_abi == "c"
    assert prototype.origin.native_symbol == "callback"
