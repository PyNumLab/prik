"""Checks for the reference BLAS auxiliary and error-reporting routines."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from .helpers import assert_allclose_for_dtype


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_scabs1(prik_blas, f2py_blas):
    value = np.complex64(-3.0 + 4.0j)

    prik_result, prik_value = prik_blas.scabs1(value)
    f2py_result = f2py_blas.scabs1(value)

    expected = np.float32(abs(value.real) + abs(value.imag))
    assert_allclose_for_dtype(prik_result, expected)
    assert_allclose_for_dtype(f2py_result, expected)
    assert_allclose_for_dtype(prik_result, f2py_result)
    assert prik_value == value
    assert prik_result.dtype == np.dtype(np.float32)


def test_dcabs1(prik_blas, f2py_blas):
    value = np.complex128(-3.0 + 4.0j)

    prik_result, prik_value = prik_blas.dcabs1(value)
    f2py_result = f2py_blas.dcabs1(value)

    expected = np.float64(abs(value.real) + abs(value.imag))
    assert_allclose_for_dtype(prik_result, expected)
    assert_allclose_for_dtype(f2py_result, expected)
    assert_allclose_for_dtype(prik_result, f2py_result)
    assert prik_value == value
    assert isinstance(prik_result, float)


def test_lsame(prik_blas, f2py_blas):
    prik_equal = prik_blas.lsame("n", "N")
    f2py_equal = f2py_blas.lsame(b"n", b"N")
    prik_different = prik_blas.lsame("N", "T")
    f2py_different = f2py_blas.lsame(b"N", b"T")

    assert prik_equal is True
    assert f2py_equal == 1
    assert bool(prik_equal) == bool(f2py_equal)
    assert prik_different is False
    assert f2py_different == 0
    assert bool(prik_different) == bool(f2py_different)


def test_xerbla(prik_blas, f2py_blas):
    prik_environment = dict(os.environ)
    prik_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(Path(prik_blas.__file__).resolve().parent), prik_environment.get("PYTHONPATH")))
    )
    f2py_environment = dict(os.environ)
    f2py_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(Path(f2py_blas.__file__).resolve().parent), f2py_environment.get("PYTHONPATH")))
    )

    prik_result = subprocess.run(  # nosec B603 - fixed interpreter and test program
        (
            sys.executable,
            "-c",
            "import numpy as np, prik_reference_blas as blas; blas.xerbla('DTEST ', np.int32(3))",
        ),
        env=prik_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    f2py_result = subprocess.run(  # nosec B603 - fixed interpreter and test program
        (
            sys.executable,
            "-c",
            "import numpy as np, f2py_reference_blas as blas; blas.xerbla(b'DTEST ', np.int32(3))",
        ),
        env=f2py_environment,
        capture_output=True,
        text=True,
        check=False,
    )

    expected_message = "On entry to DTEST parameter number  3 had an illegal value"
    assert prik_result.returncode == 0
    assert f2py_result.returncode == 0
    assert expected_message in prik_result.stdout
    assert expected_message in f2py_result.stdout
    assert prik_result.stdout == f2py_result.stdout
    assert prik_result.stderr == ""
    assert f2py_result.stderr == ""


def test_xerbla_array(prik_blas, f2py_blas):
    prik_environment = dict(os.environ)
    prik_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(Path(prik_blas.__file__).resolve().parent), prik_environment.get("PYTHONPATH")))
    )
    f2py_environment = dict(os.environ)
    f2py_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(Path(f2py_blas.__file__).resolve().parent), f2py_environment.get("PYTHONPATH")))
    )

    prik_result = subprocess.run(  # nosec B603 - fixed interpreter and test program
        (
            sys.executable,
            "-c",
            "import numpy as np, prik_reference_blas as blas; "
            "name=np.frombuffer(b'DTEST ', dtype='S1').copy(); "
            "blas.xerbla_array(name, np.int32(6), np.int32(4))",
        ),
        env=prik_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    # f2py infers SRNAME_LEN and therefore exposes it as an optional keyword.
    f2py_result = subprocess.run(  # nosec B603 - fixed interpreter and test program
        (
            sys.executable,
            "-c",
            "import numpy as np, f2py_reference_blas as blas; "
            "name=np.frombuffer(b'DTEST ', dtype='S1').copy(); "
            "blas.xerbla_array(name, np.int32(4), srname_len=np.int32(6))",
        ),
        env=f2py_environment,
        capture_output=True,
        text=True,
        check=False,
    )

    expected_message = "On entry to DTEST parameter number  4 had an illegal value"
    assert prik_result.returncode == 0
    assert f2py_result.returncode == 0
    assert expected_message in prik_result.stdout
    assert expected_message in f2py_result.stdout
    assert prik_result.stdout == f2py_result.stdout
    assert prik_result.stderr == ""
    assert f2py_result.stderr == ""
