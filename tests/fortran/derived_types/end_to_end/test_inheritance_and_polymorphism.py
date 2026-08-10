"""Inheritance and supported polymorphism runtime evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
INHERITANCE_F90_SOURCE = FIXTURES / "finheritance_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_fortran_extension_types_generate_python_inheritance(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        INHERITANCE_F90_SOURCE,
        tmp_path,
        {
            "bind_c_finheritance_f90_wrapper.f90",
            "finheritance_f90_wrapper.c",
            "finheritance_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "finheritance_f90",
        pyi_parity_build_mode,
    )

    assert issubclass(module.circle, module.base_shape)
    assert issubclass(module.box, module.base_shape)

    base = module.base_shape()
    base.size = np.float64(3.0)
    assert base.area() == np.float64(3.0)
    assert module.describe_shape(base) == np.float64(3.0)

    circle = module.circle()
    assert isinstance(circle, module.base_shape)
    circle.set_size(np.float64(5.0))
    circle.radius = np.float64(2.0)
    assert circle.size == np.float64(5.0)
    expected_circle_area = np.float64(np.pi * circle.radius**2)
    np.testing.assert_allclose(circle.area(), expected_circle_area)
    np.testing.assert_allclose(module.describe_shape(circle), expected_circle_area)

    module.base_shape.set_size(circle, np.float64(7.0))
    assert circle.size == np.float64(7.0)

    box = module.box()
    assert isinstance(box, module.base_shape)
    box.set_size(np.float64(2.0))
    box.width = np.float64(3.0)
    assert box.area() == np.float64(32.0)
    assert module.describe_shape(box) == np.float64(32.0)
