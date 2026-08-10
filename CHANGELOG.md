# Changelog

This file is the canonical record of user-visible PRIK changes. Add changes to
**Unreleased** as they land, then move them into a versioned section during
release preparation. Versions use [Semantic Versioning](https://semver.org/);
release tags add a leading `v` to the package version.

## Unreleased

### Added

- Added maintained FFTPACK and MINPACK examples built from the upstream
  fortran-lang projects. Their build scripts, user guides, and numerical tests
  cover all 31 FFTPACK and 22 MINPACK public procedures.
- Added Python-owned, read-only NumPy snapshots for supported public Fortran
  parameter arrays, including MINPACK's `dpmpar` constants.
- Added declaration-expression support for richer arithmetic, comparisons,
  conditionals, array inquiries, and local, imported, or standalone
  specification functions, including native-dependent result extents.
- Added exact NumPy Boolean-array conversion for compiler-measured 8-, 16-,
  32-, and 64-bit Fortran logical kinds, with canonical writeback.
- Added `WrapperBuildResult.import_module()` to load a generated extension
  explicitly without changing `sys.path`.

### Changed

- Moved documentation and maintainer-tool tests to `tests/docs/` and
  `tests/tools/`, removed the generic `tests/shared/` bucket, and mirrored
  internal tests by production package with narrower support helpers; removed
  recursive layout-policing tests that froze maintainer organization, retaining
  exceptional release safety under `tests/workflows/`.
- Simplified the documented DGESV validation and the LAPACK test suite to use
  explicit NumPy Fortran-order copies, with documented numerical-test helper
  conventions.
- Aligned the documented MINPACK `hybrd1` callback example with its runnable
  test, made it verify callback invocation, and made its test problems
  self-contained; FFTPACK workspace initializer tests now validate a paired
  transform against NumPy or SciPy.
- Renamed the developer-facing wrapper generation package from
  `prik.wrapper_codegen` to `prik.codegen`; the old import path was removed.
- Expanded public interface resolution so implemented unnamed interfaces and
  public generics can be wrapped without exposing private implementation
  procedures.
- Expanded the Real Libraries CI lane to build and test BLAS, LAPACK, FFTPACK,
  and MINPACK, with cached native BLAS and LAPACK builds where available.
- Made performance comparisons faster and less order-sensitive with balanced
  A/B/B/A runtime measurements, merged samples, smaller worker budgets, and
  four measured clean builds after warm-up.
- Refreshed the README and website around the canonical
  **PRIK — Python Runtime Interop Kit** identity, with a concise FAQ, a fair
  PRIK-versus-f2py guide, clearer array guidance, and searchable real-library
  examples, including a four-library capability and validation summary.
- Hardened preprocessing, compiler-derived type probes, semantic policy
  completion, and multi-source build reporting so unsupported contracts fail
  earlier with clearer diagnostics.

### Fixed

- Preserved authoritative public interface signatures when linked legacy
  implementations use different internal storage declarations, including
  FFTPACK's `zfftf` complex-array interface.
- Corrected SciPy reference inputs for the LAPACK `dstemr` and `dstebz` tests
  and strengthened BLAS and LAPACK routine validation with independent
  mathematical expectations.

## 0.1.1 — 2026-08-03

- Update README and CONTRIBUTING
- Change the Description section and add more tags


## 0.1.0 — 2026-08-03

- First public release under the PRIK name.
- Build importable Python extensions from supported Fortran sources.
- Generate, inspect, edit, and rebuild from semantic `.pyi` contracts.
- Expose the `prik` console command and the equivalent `python -m prik`
  module command.
- Report the installed release through `prik --version` and
  `prik.__version__`.
- Added a complete runnable Reference BLAS correctness example covering all 155
  discovered routines through PRIK, independent mathematical expectations, and
  f2py differential comparisons.
- Moved the repository's authoritative Reference BLAS sources to
  `examples/blas/native/` for shared use by the example, integration tests,
  LAPACK CI build, and build comparison tooling.
- Added a complete Reference LAPACK build and correctness project. It wraps all
  2,062 implementation sources once and explicitly validates the reviewed 127
  SciPy 1.18.0 double-precision real routines against independent mathematical
  invariants and f2py comparisons in the dedicated CI lane.
- Moved the repository's authoritative Reference LAPACK implementation sources
  to `examples/lapack/native/` and updated full-library integration and CI to
  consume that single source owner alongside `examples/blas/native/`.
- Fixed dependency-safe Python argument conversion ordering for wrappers whose
  array extents depend on later native scalar arguments, including padded BLAS
  leading dimensions.
