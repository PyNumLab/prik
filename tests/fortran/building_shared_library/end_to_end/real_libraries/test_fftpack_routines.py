"""Build actual FFTPACK sources and verify representative transform answers."""

from __future__ import annotations

import numpy as np
import pytest

from tests.fortran.building_shared_library.end_to_end.real_libraries._support import (
    build_real_fortran_library,
    real_library_source_dir,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


@pytest.fixture(scope="module")
def fftpack(tmp_path_factory: pytest.TempPathFactory):
    source_dir = real_library_source_dir("fftpack")
    public_sources = [
        source_dir / "rk.f90",
        source_dir / "fftpack.f90",
        *sorted(source_dir.glob("fftpack_*.f90")),
    ]
    public_source_names = {source.name for source in public_sources}
    link_only_sources = [
        source for source in sorted(source_dir.glob("*.f90")) if source.name not in public_source_names
    ]
    extension = build_real_fortran_library(
        "fftpack",
        public_sources,
        tmp_path_factory.mktemp("fftpack-showcase"),
        native_fortran_sources=link_only_sources,
    )
    return extension.fftpack


def test_fft_and_ifft_return_known_impulse_transforms(fftpack):
    impulse = np.array([1.0 + 0.0j, 0.0j, 0.0j, 0.0j], dtype=np.complex128)
    spectrum = fftpack.fft(impulse)
    inverse = fftpack.ifft(np.ones(4, dtype=np.complex128))
    try:
        np.testing.assert_allclose(spectrum.to_numpy(), np.ones(4, dtype=np.complex128))
        np.testing.assert_allclose(
            inverse.to_numpy(),
            np.array([4.0 + 0.0j, 0.0j, 0.0j, 0.0j], dtype=np.complex128),
            atol=1.0e-12,
        )
    finally:
        spectrum.close()
        inverse.close()


def test_fftshift_and_ifftshift_are_inverse_permutations(fftpack):
    values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)

    shifted = fftpack.fftshift(values)

    np.testing.assert_array_equal(shifted, np.array([3.0, 4.0, 1.0, 2.0]))
    np.testing.assert_array_equal(fftpack.ifftshift(shifted), values)
