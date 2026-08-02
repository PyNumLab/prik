# Complete Reference BLAS correctness example

This directory is a runnable, correctness-only example of building the complete
Reference BLAS with both PRIK and NumPy's f2py. It validates every one of the
155 callable routines discovered in the 155 source files. The tests compare
both wrappers with an independent mathematical result and then with each other;
f2py is useful differential evidence, but it is not the behavioral oracle.

The authoritative source set is [`native/`](native/). It is the repository's
only copy of the full BLAS sources and is also consumed by the full-library
integration test, the LAPACK CI build, and the build comparison tooling.

## Provenance and license

The sources are the Reference BLAS distributed by the University of Tennessee
through [Netlib BLAS](https://www.netlib.org/blas/). The repository imported
this corpus in commit `9113acde1f7d30af4c3eb3d90bb9f9da422639f2` on 2026-05-02;
this change relocates those bytes without modifying or duplicating them. Their
upstream provenance notices are retained in the files. No separate license file
was present beside the imported corpus. The
[Netlib BLAS FAQ](https://www.netlib.org/blas/faq.html#1_5) describes BLAS as
freely available, permits commercial use, and asks users to acknowledge Netlib
and the authors. Consult that upstream statement when redistributing the native
sources; this example's Python test code remains covered by the repository
license.

## Reproduce the two builds

The session fixtures use the following effective commands. Both commands
receive the same sorted absolute source list and `-O0`; all artifacts stay in a
temporary directory.

```bash
REPOSITORY_ROOT="$(pwd)"
BUILD_ROOT="$(mktemp -d)"
mapfile -t BLAS_SOURCES < <(find "$REPOSITORY_ROOT/examples/blas/native" -maxdepth 1 -type f \( -name '*.f' -o -name '*.f90' \) -print | sort)
mkdir -p "$BUILD_ROOT/prik" "$BUILD_ROOT/f2py"
cd "$BUILD_ROOT/prik"
python3 -m prik "${BLAS_SOURCES[@]}" --out prik_reference_blas --out-dir "$BUILD_ROOT/prik/generated" --compiler "$(command -v gfortran)" --jobs 8 --native-compile-flags=-O0 --wrapper-fortran-flags=-O0 --wrapper-c-flags=-O0
```

```bash
cd "$BUILD_ROOT/f2py"
python3 -m numpy.f2py -c -m f2py_reference_blas "${BLAS_SOURCES[@]}" --build-dir "$BUILD_ROOT/f2py/generated" --f77flags=-O0 --f90flags=-O0 --opt=-O0
```

Import the modules from their build directories:

```python
import sys

sys.path.insert(0, f"{BUILD_ROOT}/prik")
sys.path.insert(0, f"{BUILD_ROOT}/f2py")
import prik_reference_blas
import f2py_reference_blas
```

For normal use, let pytest create, report, and clean those directories:

```bash
python3 -m pytest -q examples/blas
python3 -m pytest -q examples/blas/test_level1_real.py
python3 -m pytest -q examples/blas/test_level1_real.py::test_daxpy
python3 -m pytest -q examples/blas -k dgemm
```

## What each test proves

Numerical tests normally establish all three relationships:

```text
PRIK result == independent expected result
f2py result == independent expected result
PRIK result == f2py result
```

Small explicit formulas are preferred. Matrix cases first reconstruct the
logical matrix from the declared storage and then calculate the operation.
Solve routines additionally use residuals. Input-only arrays are copied and
checked exactly; output arrays are checked with dtype-aware tolerances; unused
triangles, band rows, leading-dimension padding, and stride gaps retain their
NaN or finite sentinels exactly.

`assert_allclose_for_dtype` starts from machine epsilon for the real component
of `float32`, `float64`, `complex64`, or `complex128`, then scales the tolerance
by the reduction or multiplication length and expected magnitude. Integers,
native indexes, shapes, dtypes, and untouched storage use exact checks. NumPy
matrix operations are concise secondary calculations in some cases; explicit
scalar formulas and residual identities keep the independent oracle from
being merely another BLAS call.

### Increments and indexes

A BLAS vector is represented by its full storage plus `N` and `INCX`/`INCY`.
For positive increments the first logical element is storage index zero. For a
negative increment the native starting index is `(N - 1) * -INCX`; subsequent
logical positions add the signed increment. Tests cover `1`, values greater
than one, and negative increments while checking all gaps.

`ISAMAX`, `IDAMAX`, `ICAMAX`, and `IZAMAX` expose the native one-based BLAS
index through both wrappers. Their tests independently identify the maximum
and assert the one-based value; no automatic Python zero-basing is assumed.

### Matrix storage

The PRIK calls preserve the native argument order, including explicit leading
dimensions. f2py infers leading dimensions and moves them to optional keyword
arguments. Tests allocate non-minimal Fortran-order matrices and prove that
padding is not modified.

General routines cover no-transpose, transpose, and conjugate-transpose.
Symmetric, Hermitian, and triangular cases reconstruct only the selected upper
or lower triangle; the unused triangle contains NaNs. Hermitian reconstruction
conjugates the reflected entries and ignores stored diagonal imaginary parts.
Unit-diagonal triangular cases put NaNs on the stored diagonal and validate the
operation against a logical diagonal of ones. Level 3 triangular tests cover
both left and right multiplication and solve residuals.

Packed helpers implement the column-major BLAS packed order before reconstructing
the full logical matrix. Banded helpers use the BLAS row mapping for general,
symmetric, Hermitian, and triangular band storage. The tests reconstruct the
logical matrix before calculating the independent expectation and preserve
unused band rows exactly.

## Representative tests (source verified)

These examples are copied verbatim from the real tests. Documentation tests
select the named function from its source AST and fail if a displayed example
diverges.

### DAXPY

<!-- prik-doc-source: examples/blas/test_level1_real.py::test_daxpy -->
```python
def test_daxpy(prik_blas, f2py_blas):
    alpha = np.float64(-1.5)
    x = np.array([2.0, -4.0, 1.0], dtype=np.float64)
    original_y = np.array([3.0, 5.0, -2.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.daxpy(np.int32(3), alpha, prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_result = f2py_blas.daxpy(np.int32(3), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected_y = alpha * x + original_y
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert prik_scalars == (np.int32(3), alpha, np.int32(1), np.int32(1))
    assert f2py_result is None
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
```

### DDOT

<!-- prik-doc-source: examples/blas/test_level1_real.py::test_ddot -->
```python
def test_ddot(prik_blas, f2py_blas):
    x = np.array([1.0, -2.0, 4.0], dtype=np.float64)
    y = np.array([3.0, 5.0, -1.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, n, incx, incy = prik_blas.ddot(np.int32(3), prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_value = f2py_blas.ddot(np.int32(3), f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected = np.float64(1.0 * 3.0 + (-2.0) * 5.0 + 4.0 * (-1.0))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert (n, incx, incy) == (np.int32(3), np.int32(1), np.int32(1))
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)
```

### DGEMV

<!-- prik-doc-source: examples/blas/test_level2_general.py::test_dgemv_no_transpose -->
```python
def test_dgemv_no_transpose(prik_blas, f2py_blas):
    alpha, beta = np.float64(2.0), np.float64(-1.0)
    matrix = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    x = np.array([5.0, -2.0], dtype=np.float64)
    original_y = np.array([7.0, 11.0], dtype=np.float64)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.dgemv(
        "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    # f2py places its inferred optional leading dimension after the native arrays.
    f2py_result = f2py_blas.dgemv(
        b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    product = np.array([1.0 * 5.0 + 2.0 * (-2.0), 3.0 * 5.0 + 4.0 * (-2.0)])
    expected_y = alpha * product + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert prik_scalars == (2, 2, alpha, 3, 1, beta, 1)
    assert f2py_result is None
    assert_storage_unchanged(prik_a, matrix)
    assert_storage_unchanged(f2py_a, matrix)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
```

### DGEMM

<!-- prik-doc-source: examples/blas/test_level3_general.py::test_dgemm -->
```python
def test_dgemm(prik_blas, f2py_blas):
    alpha, beta = np.float64(2.0), np.float64(-0.5)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    b = np.asfortranarray([[5.0, 6.0], [7.0, 8.0], [93.0, 94.0]], dtype=np.float64)
    original_c = np.asfortranarray([[9.0, 10.0], [11.0, 12.0], [95.0, 96.0]], dtype=np.float64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_scalars = prik_blas.dgemm(
        "N",
        "N",
        np.int32(2),
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(3),
        prik_b,
        np.int32(3),
        beta,
        prik_c,
        np.int32(3),
    )
    # f2py moves its inferred optional leading dimensions to keyword arguments.
    f2py_result = f2py_blas.dgemm(
        b"N",
        b"N",
        np.int32(2),
        np.int32(2),
        np.int32(2),
        alpha,
        f2py_a,
        f2py_b,
        beta,
        f2py_c,
        lda=np.int32(3),
        ldb=np.int32(3),
        ldc=np.int32(3),
    )

    product = np.array(
        [[1.0 * 5.0 + 2.0 * 7.0, 1.0 * 6.0 + 2.0 * 8.0], [3.0 * 5.0 + 4.0 * 7.0, 3.0 * 6.0 + 4.0 * 8.0]],
        dtype=np.float64,
    )
    expected_active = alpha * product + beta * original_c[:2, :]
    assert_allclose_for_dtype(prik_c[:2, :], expected_active, operation_size=2)
    assert_allclose_for_dtype(f2py_c[:2, :], expected_active, operation_size=2)
    assert_allclose_for_dtype(prik_c[:2, :], f2py_c[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_c[2, :], original_c[2, :], strict=True)
    np.testing.assert_array_equal(f2py_c[2, :], original_c[2, :], strict=True)
    assert prik_scalars == (2, 2, 2, alpha, 3, 3, beta, 3)
    assert f2py_result is None
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)
```

### DTRSV

<!-- prik-doc-source: examples/blas/test_level2_triangular.py::test_dtrsv_upper_nonunit -->
```python
def test_dtrsv_upper_nonunit(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0], [91.0, 92.0]], dtype=np.float64)
    expected_solution = np.array([4.0, -2.0], dtype=np.float64)
    logical_a = triangular_from_triangle(original_a, 2, "U", unit_diagonal=False)
    original_b = logical_a.T @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.dtrsv("U", "T", "N", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.dtrsv(b"U", b"T", b"N", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a.T @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a.T @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
```

### CHEMV (complex Hermitian)

<!-- prik-doc-source: examples/blas/test_level2_hermitian.py::test_chemv -->
```python
def test_chemv(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    original_a = np.asfortranarray(
        [[2.0 + 77.0j, 1.0 - 2.0j], [np.nan + 1.0j * np.nan, 3.0 - 88.0j], [91.0j, 92.0j]], dtype=np.complex64
    )
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    original_y = np.array([4.0 - 2.0j, 5.0 + 3.0j], dtype=np.complex64)
    logical_a = hermitian_from_triangle(original_a, 2, "U")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.chemv("U", np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.chemv(b"U", np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3))

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
```

### SGBMV (general band)

<!-- prik-doc-source: examples/blas/test_level2_banded.py::test_sgbmv -->
```python
def test_sgbmv(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    original_a = np.asfortranarray([[91.0, -1.0], [2.0, 3.0], [4.0, 92.0], [93.0, 94.0]], dtype=np.float32)
    x = np.array([2.0, -3.0], dtype=np.float32)
    original_y = np.array([4.0, 5.0], dtype=np.float32)
    logical_a = general_from_band(original_a, 2, 2, 1, 1)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.sgbmv(
        "N",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        prik_a,
        np.int32(4),
        prik_x,
        np.int32(1),
        beta,
        prik_y,
        np.int32(1),
    )
    f2py_blas.sgbmv(
        b"N",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        f2py_a,
        f2py_x,
        np.int32(1),
        beta,
        f2py_y,
        np.int32(1),
        lda=np.int32(4),
    )

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
```

## Coverage and known API differences

`routine_inventory.py` classifies all routines by BLAS level and storage
family. `test_routine_coverage.py` parses the source files and fails on a
missing/extra classification, missing PRIK or f2py export, absent explicitly
named test, duplicate test name, routine-level skip, or unaudited outcome.

Current audited counts:

| Outcome | Count |
| --- | ---: |
| Native source files | 155 |
| Discovered callable routines | 155 |
| PRIK exports and independently validated routines | 155 |
| f2py exports | 155 |
| Full independent plus differential success | 149 |
| Proven f2py scalar-writeback limitations | 6 |
| Unsupported routines | 0 |
| Environmentally skipped routines | 0 |

The six f2py limitations are `srotg`, `drotg`, `crotg`, `zrotg`, `srotmg`, and
`drotmg`. From these unannotated Reference BLAS sources, f2py treats the scalar
writeback arguments as input-only. PRIK's scalar results are independently
validated; f2py's observable return or `PARAM` mutation is still recorded.
These are f2py projection limitations, not skipped PRIK checks.

PRIK uses Python `str` for native character arguments while f2py uses `bytes`.
PRIK returns detached scalar arguments alongside function/subroutine results;
f2py generally returns only a function result and returns `None` for
subroutines. `LSAME` is a Python `bool` through PRIK and an integer truth value
through f2py. Tests keep both calls visible wherever these APIs differ.

## Diagnose a failure

Keep a named temporary directory and display build output:

```bash
python3 -m pytest -vv -s examples/blas -k dgemm --basetemp=/tmp/prik-blas-debug
```

Build failures include the compiler identity, complete command, stdout, and
stderr. For numerical failures, run the single named test and inspect the
visible inputs, wrapper calls, independent expectation, and preservation
assertions in that function. The suite performs no timing collection and makes
no performance claims.
