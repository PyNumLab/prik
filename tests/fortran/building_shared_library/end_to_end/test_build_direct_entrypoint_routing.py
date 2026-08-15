"""Compiled all-direct and mixed multi-source entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_sources_and_import

FIXTURES = Path(__file__).parent / "fixtures" / "routing" / "native"
pytestmark = pytest.mark.fortran_end_to_end


def _source(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_multi_source_all_direct_route_preserves_dependency_order_and_has_no_adapter(tmp_path: Path):
    module, payload = _build_sources_and_import(
        [
            ("multi_source_direct_bind_c_f90.f90", _source("multi_source_direct_bind_c_f90.f90")),
            ("multi_source_direct_helper_f90.f90", _source("multi_source_direct_helper_f90.f90")),
        ],
        tmp_path,
    )

    assert module.multi_source_direct_helper_f90.helper_double(np.int32(4)) == np.int32(8)
    assert module.multi_source_direct_bind_c_f90.direct_combined(np.int32(4)) == np.int32(9)
    assert {Path(path).name for path in payload["generated_sources"]} == {
        "multi_source_direct_bind_c_f90_wrapper.c",
        "multi_source_direct_bind_c_f90_wrapper.h",
    }
    assert [Path(item["source"]).name for item in payload["native_build_plan"]["compilation_units"]] == [
        "multi_source_direct_bind_c_f90.f90",
        "multi_source_direct_helper_f90.f90",
    ]
    assert [Path(item["path"]).name for item in payload["native_build_plan"]["link_items"][:2]] == [
        "multi_source_direct_bind_c_f90.o",
        "multi_source_direct_helper_f90.o",
    ]


def test_multi_source_mixed_route_adapts_only_ordinary_dependent_operation(tmp_path: Path):
    module, _payload = _build_sources_and_import(
        [
            ("multi_source_mixed_bind_c_f90.f90", _source("multi_source_mixed_bind_c_f90.f90")),
            ("multi_source_mixed_helper_f90.f90", _source("multi_source_mixed_helper_f90.f90")),
        ],
        tmp_path,
    )

    assert module.multi_source_mixed_helper_f90.helper_double(np.int32(4)) == np.int32(8)
    assert module.multi_source_mixed_bind_c_f90.adapted_combined(np.int32(4)) == np.int32(9)
    bridge = (tmp_path / "bind_c_multi_source_mixed_bind_c_f90_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_combined" in bridge
    assert "helper_double" not in bridge
