"""Public FFTPACK module surface and its explicit test mapping."""

from __future__ import annotations

ROUTINE_GROUPS: dict[str, tuple[str, ...]] = {
    "Complex work-array transforms": ("zffti", "zfftf", "zfftb"),
    "Real work-array transforms": ("dffti", "dfftf", "dfftb", "dzffti", "dzfftf", "dzfftb"),
    "Cosine and sine work-array transforms": (
        "dcosqi",
        "dcosqf",
        "dcosqb",
        "dcosti",
        "dcost",
        "dsinti",
        "dsint",
    ),
    "High-level Fourier transforms": ("fft", "ifft", "rfft", "irfft"),
    "High-level cosine transforms": ("dct", "idct", "dct_t1i", "dct_t1", "dct_t23i", "dct_t2", "dct_t3"),
    "Frequency and spectrum ordering": ("fftfreq", "rfftfreq", "fftshift", "ifftshift"),
}

ALL_ROUTINES = tuple(routine for group in ROUTINE_GROUPS.values() for routine in group)
PRIK_TESTED_ROUTINES = frozenset(ALL_ROUTINES)
UNSUPPORTED_ROUTINES: dict[str, str] = {}
EXPLICIT_TEST_NAMES = {routine: f"test_{routine}" for routine in ALL_ROUTINES}
