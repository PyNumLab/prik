# LAPACK correctness example

This maintained example wraps and compiles the complete Reference LAPACK
implementation corpus once, then validates the reviewed SciPy-backed
double-precision real surface. The two scopes are deliberately different:

- compilation covers 2,062 LAPACK implementation sources and the required
  authoritative BLAS sources;
- correctness covers the 127 native `d*` routines exposed by
  `scipy.linalg.lapack` in pinned SciPy 1.18.0 for `dtype=np.float64`.

SciPy selects eligibility. Standard LAPACK problem families determine the test
layout. PRIK support is not a selection condition: a missing PRIK export fails
the coverage audit instead of shrinking the inventory.

## Source ownership, provenance, and license

`examples/lapack/native/` is the repository's only owner of the Reference
LAPACK implementation sources. It contains library implementation routines and
the `la_constants`/`la_xisnan` modules required by the build; it excludes the
upstream testing programs, timing programs, examples, and matrix generators.
The corpus was originally imported from the Netlib Reference LAPACK distribution
and is covered by the LAPACK three-clause BSD-style license. See the
[Reference LAPACK site](https://www.netlib.org/lapack/) and
[license](https://www.netlib.org/lapack/LICENSE.txt).

BLAS remains separately owned by `examples/blas/native/`. The complete LAPACK
native artifact consumes that source set directly, excluding any BLAS routine
stem already supplied by LAPACK. No BLAS source is copied below this directory.

## Build topology

On Python 3.12 and newer, NumPy's f2py uses its Meson backend. Install the
same Meson, Ninja, and SciPy versions used by the dedicated BLAS/LAPACK CI lane
before running this example:

```console
sudo apt-get install libblas-dev liblapack-dev
python3 -m pip install "meson==1.11.2" "ninja==1.13.0" "scipy==1.18.0"
```

The session fixture reuses the established complete-library integration path in
`tests/fortran/building_shared_library/end_to_end/real_libraries/test_full_libraries.py`.
It performs these operations once:

1. generate one semantic package for all LAPACK sources;
2. compile all 2,062 LAPACK sources plus required BLAS dependencies into one
   cached shared library;
3. build one PRIK extension from the complete generated contract and shared
   library;
4. independently build one raw f2py comparison surface from the 125 reviewed
   f2py-compatible routine sources and their minimal module dependency, linking unselected
   LAPACK and BLAS helper symbols from the system development libraries; and
5. reuse the three imported comparison surfaces for every correctness file.

The contract-generation command is:

```console
python3 -m prik generate --pyi examples/lapack/native --language fortran --out /tmp/prik-lapack/contracts/lapack
```

The extension build is performed by `build_pyi_extension` with the complete
contract, the cached `libprik_full_lapack.so`, and `-O0` wrapper flags. The raw
f2py command assembled by `conftest.py` is equivalent to:

```console
python3 -m numpy.f2py -c -m f2py_reference_lapack_example \
  examples/lapack/native/la_constants.f90 \
  <the 125 f2py-compatible source files recorded in routine_inventory.py> \
  only: <the 125 f2py-compatible routine names> : \
  --dep lapack --dep blas \
  --f2cmap /tmp/prik-lapack/.f2py_f2cmap \
  --build-dir /tmp/prik-lapack/f2py --f77flags=-O0 --f90flags=-O0 --opt=-O0
```

`dlartg.f90` imports the `LA_CONSTANTS` module and declares its arguments as
`REAL(wp)`. The f2py build therefore includes `la_constants.f90` as a build-only
dependency and supplies a kind map that resolves `wp` to C `double`. The
`only:` list makes the 125 f2py-compatible routine wrappers explicit; module support metadata
is not counted as a selected routine. The dependency is compiled only to
satisfy f2py's standalone selected-source build. f2py does not compile or link
PRIK's complete 2,062-source native artifact. The reviewed implementations come
from `examples/lapack/native/`; only their unselected transitive LAPACK and BLAS
dependencies come from the system libraries.

Build products stay in pytest temporary/cache directories. Failures report the
compiler identity, command, stdout, and stderr. Neither build dirties the
repository.

The fixtures import the complete PRIK module, the raw f2py module, and
`scipy.linalg.lapack`. Character flags are Python `str` through PRIK and
`bytes` through SciPy/f2py. PRIK retains the complete native argument order.
Raw f2py retains the order of the arguments it exposes, but infers and hides
leading dimensions and a few other shape-only scalar arguments; each visible
f2py call follows the generated wrapper signature. SciPy projects arrays and
optional arguments into its documented Python API.

The Reference LAPACK subroutines do not declare Fortran `intent`, so raw f2py
does not project their scalar writebacks. It still exposes in-place array
mutation, which provides enough output for the independent oracle in 112 of
the 121 exported subroutines; the four exported LAPACK functions return their
values normally. Nine subroutines have an essential scalar-only result, or need
an unprojected scalar to validate their mutated vector, and are explicitly
recorded in `F2PY_NUMERICAL_LIMITATIONS`.

`dgees` and `dgges` remain in the 127-routine correctness inventory but are
recorded in `F2PY_EXPORT_LIMITATIONS`. Their Reference LAPACK interfaces accept
external selection callbacks. From the unannotated implementation sources,
NumPy f2py 2.5.1 generates incomplete callback declarations (`select_t` and
`selctg_t`) and invalid C wrapper code. Those two routines are therefore
validated through PRIK, SciPy, and independent Schur reconstruction without a
raw-f2py call; the remaining 125 selected names must be exported by the one
f2py comparison module.

The nine reviewed limitations are:

- `dlarfg`: the vector writeback is compared, but `ALPHA` and `TAU` are not
  projected;
- `dlartg`: `C`, `S`, and `R` are all unprojected scalar writebacks; and
- `dgbcon`, `dgecon`, `dgtcon`, `dpocon`, `dppcon`, `dsycon`, and `dtrcon`:
  `RCOND` and `INFO` are unprojected scalar writebacks.

## Correctness evidence

The official LAPACK contract defines behavior. An independent mathematical
identity is the primary executable oracle. SciPy and f2py are differential
implementations, not the definition of correctness. Each applicable test keeps
the three calls visible and checks solutions, residuals, reconstructions,
orthogonality, eigen equations, singular values, storage, mutation, shape,
dtype, workspace, pivots, and `INFO` as appropriate.

Equivalent decompositions are compared by invariants. Eigenvectors and singular
vectors may change sign; repeated eigenspaces may use another orthonormal basis;
pivot ties may choose another valid permutation. Tests therefore use residuals,
subspaces, factor reconstruction, and orthogonality instead of byte equality
where the contract permits freedom.

All numerical arrays use `dtype=np.float64`. PRIK exposes the native scalar
contract exactly, so its visible calls use `np.int32(...)` for LAPACK `INTEGER`
arguments, `np.float64(...)` for scalar `DOUBLE PRECISION` arguments, and
`np.bool_(...)` for scalar `LOGICAL` arguments. SciPy and f2py calls retain their
own accepted Python conventions beside the PRIK call. `assert_allclose_float64`
scales tolerance with double-precision epsilon and operation length. Residual
checks also scale by matrix and solution norms. Integer results, `INFO`, shapes,
dtypes, pivot bounds, and untouched sentinel storage use exact comparisons.

`DTGSEN` and `DTRSEN` accept default-Fortran `LOGICAL` selection arrays. The
pinned GFortran ABI stores each such element in four bytes, while PRIK's Python
surface accepts a NumPy bool buffer. `gfortran_logical_mask` makes that genuine
ABI difference explicit by placing each truth byte at the start of its native
four-byte cell. The two affected calls remain visible, independently validate
the requested reorder, and are recorded in `PRIK_ABI_ADAPTERS` rather than
silently treating an ordinary two-byte NumPy mask as native storage.

## Arrays, storage, workspaces, and indexes

Matrices are explicitly Fortran contiguous where the native contract requires
column-major storage. Leading dimensions remain visible in PRIK calls and are
omitted only where the generated f2py signature explicitly infers them.
Tests use NaNs or sentinel values in unused triangles and padding, then prove
that those locations remain untouched. Helpers reconstruct general band,
symmetric band, tridiagonal, packed, triangular, and rectangular-full-packed
(RFP) representations before evaluating the logical matrix.

Workspace-bearing tests allocate the native `WORK`/`IWORK` arrays and keep
`LWORK`/`LIWORK` visible. The suite uses reviewed safe sizes; query behavior is
covered where the exposed API supports it. `INFO == 0` is exact on normal paths.
Invalid argument calls that could route through `XERBLA` are not made in-process.

Native LAPACK pivots and positions are one-based. PRIK and the raw f2py surface
preserve native values. SciPy converts several low-level pivot/index APIs to
zero-based values, but preserves one-based `JPVT` for `DGELSY`/`DGEQP3`, one-based
`IPIV` for the general-tridiagonal `DGTTRF`/`DGTTRS` family, and one-based Schur
reorder positions for `DTGEXC`/`DTREXC`. Each affected test keeps the observed
convention beside the call. The inventory marks every pivot/index-bearing
routine so a new conversion cannot be hidden in a generic adapter.

## Run and diagnose

The dedicated BLAS + LAPACK GitHub Actions lane runs runtime verification:

```console
python3 -m pytest -q examples/lapack
python3 -m pytest -q examples/lapack/test_linear_general.py
python3 -m pytest -q examples/lapack/test_linear_general.py::test_dgesv_solves_general_system
python3 -m pytest -q examples/lapack -k dgesvd
```

Repository policy leaves LAPACK wrapper/runtime execution to that lane unless a
maintainer explicitly requests a local run. Local work may collect tests and run
the structural inventory, documentation, architecture, and static-analysis
checks.

To diagnose CI, rerun the single named test with `-vv -s` and a retained
`--basetemp`; inspect the reported compiler command and the visible arrays,
wrapper calls, residual, `INFO`, and preservation assertions. The project is
deterministic and correctness-only: it collects no timings and makes no speed
claims.

## Coverage

`routine_inventory.py` explicitly classifies all 127 selected routines and
records their source, wrapper names, family, mutation/return/workspace/index
behavior, oracle class, and exact pytest owner. `test_routine_coverage.py`
fails on SciPy drift, duplicate or missing classification, a source-boundary
change, an absent explicit test, a missing PRIK/f2py export, or divergent
documented totals.

| Outcome | Count |
| --- | ---: |
| Authoritative LAPACK implementation sources | 2,062 |
| Discovered root LAPACK procedures | 2,064 |
| Selected SciPy-backed float64 routines | 127 |
| Explicit correctness tests | 127 |
| PRIK exports required in CI | 127 |
| SciPy exports used | 127 |
| f2py exports required in CI | 125 |
| Routines satisfying the independent oracle through f2py | 116 |
| Documented raw-f2py export limitations | 2 |
| Documented raw-f2py numerical projection limitations | 9 |
| Documented PRIK default-LOGICAL ABI adapters | 2 |
| Documented unsupported/skipped routines | 0 |

Runtime success, f2py projection limitations, and any PRIK failures are CI
outcomes and must be reported honestly; structural completion does not predict
them.

## Representative source-verified tests

The documentation checker extracts each named function from the real test AST
and fails if the displayed source diverges.

### DGESV

<!-- prik-doc-source: examples/lapack/test_linear_general.py::test_dgesv_solves_general_system -->
```python
def test_dgesv_solves_general_system(prik_lapack, scipy_lapack, f2py_lapack):
    original_a = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    original_b = np.array([[5.0], [5.0]], dtype=np.float64)
    expected_x = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(original_a), column_major(original_a)
    prik_b, f2py_b = column_major(original_b), column_major(original_b)
    prik_piv = np.empty(2, dtype=np.int32)
    f2py_piv = np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dgesv(
        np.int32(2), np.int32(1), prik_a, np.int32(2), prik_piv, prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dgesv(2, 1, f2py_a, f2py_piv, f2py_b, 0)
    scipy_lu, scipy_piv, scipy_x, scipy_info = scipy_lapack.dgesv(
        original_a.copy(order="F"), original_b.copy(order="F")
    )

    assert prik_scalars == (2, 1, 2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    assert_allclose_float64(active(prik_b, 2, 1), expected_x, operation_size=2)
    assert_allclose_float64(active(f2py_b, 2, 1), expected_x, operation_size=2)
    assert_allclose_float64(scipy_x, expected_x, operation_size=2)
    assert_allclose_float64(prik_a, scipy_lu, operation_size=2)
    assert_allclose_float64(f2py_a, scipy_lu, operation_size=2)
    np.testing.assert_array_equal(prik_piv, native_pivots(scipy_piv))
    np.testing.assert_array_equal(f2py_piv, native_pivots(scipy_piv))
    assert_small_residual(
        original_a @ prik_b - original_b,
        matrix_norm=np.linalg.norm(original_a, ord=np.inf),
        solution_norm=np.linalg.norm(prik_b, ord=np.inf),
        operation_size=2,
    )
```

### DGETRF

<!-- prik-doc-source: examples/lapack/test_linear_general.py::test_dgetrf_reconstructs_pivoted_lu -->
```python
def test_dgetrf_reconstructs_pivoted_lu(prik_lapack, scipy_lapack, f2py_lapack):
    original = np.array([[0.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(original), column_major(original)
    prik_piv = np.empty(2, dtype=np.int32)
    f2py_piv = np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dgetrf(np.int32(2), np.int32(2), prik_a, np.int32(2), prik_piv, np.int32(0))
    f2py_result = f2py_lapack.dgetrf(2, 2, f2py_a, f2py_piv, 0)
    scipy_lu, scipy_piv, scipy_info = scipy_lapack.dgetrf(original.copy(order="F"))

    assert prik_scalars == (2, 2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    expected_native_piv = native_pivots(scipy_piv)
    np.testing.assert_array_equal(prik_piv, expected_native_piv)
    np.testing.assert_array_equal(f2py_piv, expected_native_piv)
    assert_allclose_float64(prik_a, scipy_lu, operation_size=2)
    assert_allclose_float64(f2py_a, scipy_lu, operation_size=2)
    lower, upper = unpack_lu(prik_a)
    permutation = pivot_matrix(prik_piv, 2, one_based=True)
    assert_allclose_float64(permutation @ original, lower @ upper, operation_size=2)
```

### DPOTRF

<!-- prik-doc-source: examples/lapack/test_linear_positive_definite.py::test_dpotrf_reconstructs_spd_matrix -->
```python
def test_dpotrf_reconstructs_spd_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    logical = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    stored = np.array([[4.0, np.nan], [1.0, 3.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = column_major(stored), column_major(stored)

    prik_scalars = prik_lapack.dpotrf("L", np.int32(2), prik_a, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dpotrf(b"L", 2, f2py_a, 0)
    scipy_factor, scipy_info = scipy_lapack.dpotrf(stored.copy(order="F"), lower=1, clean=0)

    assert prik_scalars == (2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    prik_lower = np.tril(prik_a)
    f2py_lower = np.tril(f2py_a)
    scipy_lower = np.tril(scipy_factor)
    assert_allclose_float64(prik_lower @ prik_lower.T, logical, operation_size=2)
    assert_allclose_float64(f2py_lower @ f2py_lower.T, logical, operation_size=2)
    assert_allclose_float64(scipy_lower @ scipy_lower.T, logical, operation_size=2)
    assert_allclose_float64(prik_lower, scipy_lower, operation_size=2)
    assert_allclose_float64(f2py_lower, scipy_lower, operation_size=2)
    assert_storage_unchanged(np.triu(prik_a, 1), np.triu(stored, 1))
    assert_storage_unchanged(np.triu(f2py_a, 1), np.triu(stored, 1))
```

### DGEQRF

<!-- prik-doc-source: examples/lapack/test_orthogonal_factorizations.py::test_dgeqrf_reconstructs_qr_factorization -->
```python
def test_dgeqrf_reconstructs_qr_factorization(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(matrix), column_major(matrix)
    prik_tau = np.empty(2, dtype=np.float64)
    f2py_tau = np.empty(2, dtype=np.float64)

    prik_scalars = prik_lapack.dgeqrf(
        np.int32(3), np.int32(2), prik_a, np.int32(3), prik_tau, np.empty(16), np.int32(16), np.int32(0)
    )
    f2py_result = f2py_lapack.dgeqrf(3, 2, f2py_a, f2py_tau, np.empty(16), 16, 0)
    scipy_qr, scipy_tau, _scipy_work, scipy_info = scipy_lapack.dgeqrf(matrix.copy(order="F"), lwork=16)

    assert prik_scalars == (3, 2, 3, 16, 0)
    assert f2py_result is None
    assert scipy_info == 0
    for factor, tau in ((prik_a, prik_tau), (f2py_a, f2py_tau), (scipy_qr, scipy_tau)):
        q = qr_q_from_reflectors(factor, tau)
        r = np.triu(factor[:2, :])
        assert_orthogonal(q)
        assert_allclose_float64(q @ r, matrix, operation_size=3)
    assert_allclose_float64(prik_a, scipy_qr, operation_size=3)
    assert_allclose_float64(f2py_a, scipy_qr, operation_size=3)
    assert_allclose_float64(prik_tau, scipy_tau, operation_size=3)
    assert_allclose_float64(f2py_tau, scipy_tau, operation_size=3)
```

### DSYEV

<!-- prik-doc-source: examples/lapack/test_eigen_symmetric.py::test_dsyev_returns_orthonormal_eigenvectors -->
```python
def test_dsyev_returns_orthonormal_eigenvectors(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[2.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    expected_w = np.array([1.0, 3.0], dtype=np.float64)
    prik_vectors, f2py_vectors = column_major(matrix), column_major(matrix)
    prik_w = np.empty(2, dtype=np.float64)
    f2py_w = np.empty(2, dtype=np.float64)

    prik_scalars = prik_lapack.dsyev(
        "V", "U", np.int32(2), prik_vectors, np.int32(2), prik_w, np.empty(16), np.int32(16), np.int32(0)
    )
    f2py_result = f2py_lapack.dsyev(b"V", b"U", 2, f2py_vectors, f2py_w, np.empty(16), 16, 0)
    scipy_w, scipy_vectors, scipy_info = scipy_lapack.dsyev(matrix.copy(order="F"), compute_v=1, lower=0, lwork=16)

    assert prik_scalars == (2, 2, 16, 0)
    assert f2py_result is None
    assert scipy_info == 0
    for values, vectors in (
        (prik_w, prik_vectors),
        (f2py_w, f2py_vectors),
        (scipy_w, scipy_vectors),
    ):
        assert_allclose_float64(values, expected_w, operation_size=2)
        assert_orthogonal(vectors)
        assert_allclose_float64(matrix @ vectors, vectors @ np.diag(values), operation_size=2)
```

### DGESVD

<!-- prik-doc-source: examples/lapack/test_svd.py::test_dgesvd_reconstructs_matrix -->
```python
def test_dgesvd_reconstructs_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(matrix), column_major(matrix)
    prik_s, f2py_s = np.empty(2, dtype=np.float64), np.empty(2, dtype=np.float64)
    prik_u, f2py_u = column_major(np.zeros((3, 3))), column_major(np.zeros((3, 3)))
    prik_vt, f2py_vt = column_major(np.zeros((2, 2))), column_major(np.zeros((2, 2)))

    prik_scalars = prik_lapack.dgesvd(
        "A",
        "A",
        np.int32(3),
        np.int32(2),
        prik_a,
        np.int32(3),
        prik_s,
        prik_u,
        np.int32(3),
        prik_vt,
        np.int32(2),
        np.empty(32),
        np.int32(32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgesvd(b"A", b"A", 3, 2, f2py_a, f2py_s, f2py_u, f2py_vt, np.empty(32), 32, 0)
    scipy_u, scipy_s, scipy_vt, scipy_info = scipy_lapack.dgesvd(
        matrix.copy(order="F"), compute_uv=1, full_matrices=1, lwork=32
    )

    assert prik_scalars == (3, 2, 3, 3, 2, 32, 0)
    assert f2py_result is None
    assert scipy_info == 0
    for u, values, vt in (
        (prik_u, prik_s, prik_vt),
        (f2py_u, f2py_s, f2py_vt),
        (scipy_u, scipy_s, scipy_vt),
    ):
        assert np.all(np.diff(values) <= 0.0)
        assert_orthogonal(u)
        assert_orthogonal(vt.T)
        assert_allclose_float64(u[:, :2] @ np.diag(values) @ vt, matrix, operation_size=3)
    assert_allclose_float64(prik_s, scipy_s, operation_size=3)
    assert_allclose_float64(f2py_s, scipy_s, operation_size=3)
```

### DTBTRS (banded storage)

<!-- prik-doc-source: examples/lapack/test_linear_banded_tridiagonal.py::test_dtbtrs_solves_triangular_band_system -->
```python
def test_dtbtrs_solves_triangular_band_system(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[2.0, 1.0], [0.0, 3.0]], dtype=np.float64)
    band = symmetric_band_storage(matrix, 1, lower=False)
    rhs = np.array([[4.0], [6.0]], dtype=np.float64, order="F")
    expected = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dtbtrs(
        "U", "N", "N", np.int32(2), np.int32(1), np.int32(1), band, np.int32(2), prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dtbtrs(b"U", b"N", b"N", 2, 1, 1, band, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dtbtrs(band, rhs.copy(order="F"), uplo=b"U", trans=b"N", diag=b"N")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, expected, operation_size=2)
    assert_allclose_float64(f2py_b, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)
    assert_allclose_float64(matrix @ prik_b, rhs, operation_size=2)
```

### DGECON (condition estimation)

<!-- prik-doc-source: examples/lapack/test_linear_general.py::test_dgecon_estimates_reciprocal_condition -->
```python
def test_dgecon_estimates_reciprocal_condition(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[4.0]], dtype=np.float64, order="F")
    expected = 1.0

    prik_scalars = prik_lapack.dgecon(
        "1",
        np.int32(1),
        factor.copy(order="F"),
        np.int32(1),
        np.float64(4.0),
        np.float64(0.0),
        np.empty(4),
        np.empty(1, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgecon(
        b"1", 1, factor.copy(order="F"), 4.0, 0.0, np.empty(4), np.empty(1, dtype=np.int32), 0
    )
    scipy_rcond, scipy_info = scipy_lapack.dgecon(factor.copy(order="F"), 4.0, norm=b"1")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], expected)
    assert_allclose_float64(scipy_rcond, expected)
```
