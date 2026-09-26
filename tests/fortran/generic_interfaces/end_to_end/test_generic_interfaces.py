"""Generic procedure interface runtime wrapper tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_and_import,
    _build_source_or_generated_pyi_and_import,
    _build_sources_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
OVERLOAD_F90_SOURCE = FIXTURES / "native" / "foverloads_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

PRIVATE_INLINE_GENERIC_MODULE = (NATIVE_FIXTURES / "private_inline_generic.f90").read_text(encoding="utf-8")

PRIVATE_INLINE_GENERIC_SUBMODULE = (NATIVE_FIXTURES / "private_inline_generic_impl.f90").read_text(encoding="utf-8")

INTERFACE_BODY_GENERIC_MODULE = (NATIVE_FIXTURES / "interface_body_generic.f90").read_text(encoding="utf-8")

INTERFACE_BODY_GENERIC_IMPL = (NATIVE_FIXTURES / "interface_body_generic_impl.f90").read_text(encoding="utf-8")


@pytest.fixture
def compiled_generic_module(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    return _build_source_or_generated_pyi_and_import(
        OVERLOAD_F90_SOURCE,
        tmp_path,
        {
            "bind_c_foverloads_f90_wrapper.f90",
            "foverloads_f90_wrapper.c",
            "foverloads_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "foverloads_f90",
        pyi_parity_build_mode,
    )


def test_fortran_generic_interfaces_dispatch_in_generated_c_extension(
    compiled_generic_module,
):
    module = compiled_generic_module

    assert "Module Attributes" not in module.__doc__
    assert "convert(*args, **kwargs)" in module.__doc__
    assert "_prik_overload_" not in module.__doc__
    assert "convert_integer" not in module.__doc__
    assert "convert(value: int32) -> int32" in module.convert.__doc__
    assert "convert(value: float64) -> float64" in module.convert.__doc__
    assert "convert(value: complex128) -> complex128" in module.convert.__doc__
    assert "convert_integer" not in module.convert.__doc__
    assert "convert_real" not in module.convert.__doc__
    assert "convert_complex" not in module.convert.__doc__

    assert module.convert(np.int32(4)) == np.int32(14)
    assert module.convert(np.array(4, dtype=np.int32)) == np.int32(14)
    assert module.convert(np.float64(4.0)) == np.float64(4.5)
    assert module.convert(np.array(4.0, dtype=np.float64)) == np.float64(4.5)
    assert module.convert(value=np.int32(5)) == np.int32(15)
    assert module.convert(np.complex128(2.0 + 3.0j)) == np.complex128(3.0 + 2.0j)
    assert module.summarize(np.float64(2.5)) == np.float64(2.5)
    assert module.summarize(np.array([1.0, 2.0, 3.0], dtype=np.float64)) == np.float64(6.0)

    value = module.Accumulator()
    value.add(np.int32(2))
    value.add(value=np.float64(0.5))
    assert value.total == np.float64(2.5)
    assert module.inspect(value) == np.float64(2.5)

    sample = module.Sample()
    sample.value = np.float64(7.25)
    assert module.inspect(sample) == np.float64(7.25)

    with pytest.raises(TypeError):
        module.convert("not numeric")
    with pytest.raises(TypeError, match="no matching overload for convert"):
        module.convert(np.int32(1), value=np.int32(2))
    with pytest.raises(TypeError):
        value.add(np.complex128(1.0 + 0.0j))


def test_public_generic_dispatches_to_private_inline_submodule_specifics(tmp_path: Path):
    module, _payload = _build_sources_and_import(
        [
            ("private_inline_generic.f90", PRIVATE_INLINE_GENERIC_MODULE),
            ("private_inline_generic_impl.f90", PRIVATE_INLINE_GENERIC_SUBMODULE),
        ],
        tmp_path,
    )

    assert module.private_inline_generic.shift(np.int32(4)) == np.int32(5)
    assert module.private_inline_generic.shift(np.float64(4.0)) == np.float64(4.5)
    bridge = (tmp_path / "bind_c_private_inline_generic_wrapper.f90").read_text(encoding="utf-8").lower()
    assert "native__prik_overload_shift_0 => shift" in bridge
    assert "native__prik_overload_shift_1 => shift" in bridge
    assert "=> shift_integer" not in bridge
    assert "=> shift_real" not in bridge


def test_public_generic_calls_public_interface_body_specifics_by_their_own_names(tmp_path: Path):
    """A public specific an interface body declares needs no route through the generic."""
    module, _payload = _build_sources_and_import(
        [
            ("interface_body_generic.f90", INTERFACE_BODY_GENERIC_MODULE),
            ("interface_body_generic_impl.f90", INTERFACE_BODY_GENERIC_IMPL),
        ],
        tmp_path,
    )

    assert module.interface_body_generic.scale(np.int32(4)) == np.int32(8)
    assert module.interface_body_generic.scale(np.float64(4.0)) == np.float64(10.0)
    bridge = (tmp_path / "bind_c_interface_body_generic_wrapper.f90").read_text(encoding="utf-8").lower()
    assert "native__prik_overload_scale_0 => scale_integer" in bridge
    assert "native__prik_overload_scale_1 => scale_real" in bridge


EXTENDED_GENERIC_SOURCE = (NATIVE_FIXTURES / "extended_generic.f90").read_text(encoding="utf-8")


def test_generic_extended_across_modules_dispatches_to_every_specific(tmp_path: Path):
    """A local interface block extends the generic it imports, not replaces it.

    The extending module resolves both the specific it declares and the one
    that reached it through the import, while the declaring module keeps only
    its own: a generic accumulates along the `use` chain in one direction.
    """
    source = tmp_path / "gen_extended.f90"
    source.write_text(EXTENDED_GENERIC_SOURCE, encoding="utf-8")
    module = _build_source_and_import(
        source,
        tmp_path / "build",
        {
            "bind_c_gen_extended_wrapper.f90",
            "gen_extended_wrapper.c",
            "gen_extended_wrapper.h",
        },
    )

    assert module.gen_extended_mod.report(np.int32(3)) == np.int32(3)
    assert module.gen_extended_mod.report(np.float64(4.0)) == np.int32(40)
    assert module.gen_base_mod.report(np.int32(3)) == np.int32(3)

    # The inherited specific is reachable only through the generic, because
    # `use gen_base_mod, only : report` never bound its own name.
    assert "report_int" not in dir(module.gen_extended_mod)
    with pytest.raises(TypeError, match="no matching overload"):
        module.gen_base_mod.report(np.float64(4.0))
