cd "$EXAMPLE_WORKSPACE"
export BLAS_F2PY_ROOT="$BLAS_BUILD_ROOT/f2py"
mkdir -p "$BLAS_F2PY_ROOT/generated"
cd "$BLAS_F2PY_ROOT"

export FC="$(command -v gfortran)"
export F77="$FC"
export F90="$FC"
export FFLAGS="-O0"
export F90FLAGS="-O0"
export LDFLAGS="${LDFLAGS:+$LDFLAGS }-Wl,-rpath,$(dirname "$BLAS_SHARED_LIBRARY")"

python -m numpy.f2py -c \
  "$EXAMPLE_WORKSPACE/examples/fortran/blas/blas.pyf" \
  "-L$(dirname "$BLAS_SHARED_LIBRARY")" \
  -lprik_full_blas \
  --build-dir "$BLAS_F2PY_ROOT/generated" \
  --f77flags=-O0 \
  --f90flags=-O0 \
  --opt=-O0
