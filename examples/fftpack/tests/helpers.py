"""Reference conversions for FFTPACK's documented unnormalized conventions."""

from __future__ import annotations

import numpy as np


def numpy_rfft_packing(values: np.ndarray) -> np.ndarray:
    """Return NumPy's real FFT in FFTPACK's one-dimensional packed layout."""
    spectrum = np.fft.rfft(values)
    packed = np.empty(values.size, dtype=np.float64)
    packed[0] = spectrum[0].real
    if values.size % 2 == 0:
        packed[-1] = spectrum[-1].real
        stop = spectrum.size - 1
    else:
        stop = spectrum.size
    for index in range(1, stop):
        packed[2 * index - 1] = spectrum[index].real
        packed[2 * index] = spectrum[index].imag
    return packed


def take_owned_array(handle) -> np.ndarray:
    """Copy one PRIK allocatable result and release its native allocation."""
    try:
        return handle.to_numpy().copy()
    finally:
        handle.close()
