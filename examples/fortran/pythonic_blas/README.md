# Design a Pythonic API over Reference BLAS

This example reshapes four Reference BLAS routines into:

```python
from prik_linalg import DenseMatrix, dot, matmul, matvec, norm
```

Follow the [Pythonic BLAS tutorial](../../../docs/user/tutorials/pythonic-blas.md)
for the complete walkthrough.

## Project layout

| File | Role |
| --- | --- |
| [`_prik_linalg_native.pyi`](_prik_linalg_native.pyi) | Edited contract for the private native extension |
| [`prik_linalg.py`](prik_linalg.py) | Public functional API and `DenseMatrix` |
| [`build.sh`](build.sh) | Builds the extension and sets `PYTHONPATH` |
| [`test_pythonic_blas.py`](test_pythonic_blas.py) | NumPy comparisons and API validation |

The example reuses six files from [`../blas/native/`](../blas/native/): the
four wrapped routines plus the `LSAME` and `XERBLA` helpers they call.
The functional matrix operations require Fortran-contiguous arrays;
`DenseMatrix` performs that layout conversion once when it is constructed.

## Run it

Install PRIK, NumPy, pytest and GNU Fortran. Then run from the repository root:

```bash
source examples/fortran/pythonic_blas/build.sh
python3 -m pytest -q examples/fortran/pythonic_blas/test_pythonic_blas.py
```

Use `source` so the build paths exported by `build.sh` remain available to the
test process. The script builds in a temporary directory, so the example tree
remains free of generated `.so`, object and module files.

## Sources and license

The sources are from the Reference BLAS snapshot in Netlib LAPACK 3.12.1. See
the [BLAS example README](../blas/README.md#sources-and-license) for provenance
and license.
