export EXAMPLE_WORKSPACE="$PWD"
export LINALG_BUILD_ROOT="$(mktemp -d)"
export LINALG_EXAMPLE_ROOT="$EXAMPLE_WORKSPACE/examples/fortran/pythonic_blas"
export BLAS_NATIVE_ROOT="$EXAMPLE_WORKSPACE/examples/fortran/blas/native"

mkdir -p "$LINALG_BUILD_ROOT/generated"
cd "$LINALG_BUILD_ROOT"

python3 -m prik "$LINALG_EXAMPLE_ROOT/_prik_linalg_native.pyi" \
  --out _prik_linalg_native \
  --out-dir "$LINALG_BUILD_ROOT/generated" \
  --compiler "$(command -v gfortran)" \
  --native-fortran-sources \
    "$BLAS_NATIVE_ROOT/ddot.f" \
    "$BLAS_NATIVE_ROOT/dnrm2.f90" \
    "$BLAS_NATIVE_ROOT/dgemv.f" \
    "$BLAS_NATIVE_ROOT/dgemm.f" \
    "$BLAS_NATIVE_ROOT/lsame.f" \
    "$BLAS_NATIVE_ROOT/xerbla.f" \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"

cd "$EXAMPLE_WORKSPACE"
export PYTHONPATH="$LINALG_BUILD_ROOT:$LINALG_EXAMPLE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
