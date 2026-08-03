cd "$EXAMPLE_WORKSPACE"
export LAPACK_F2PY_ROOT="$LAPACK_BUILD_ROOT/f2py"
mkdir -p "$LAPACK_F2PY_ROOT/generated"
cd "$LAPACK_F2PY_ROOT"

export FC="$(command -v gfortran)"
export F77="$FC"
export F90="$FC"
export FFLAGS="-O0"
export F90FLAGS="-O0"
export LDFLAGS="${LDFLAGS:+$LDFLAGS }-Wl,-rpath,$(dirname "$LAPACK_SHARED_LIBRARY")"

python -m numpy.f2py -c \
  "$EXAMPLE_WORKSPACE/examples/lapack/lapack.pyf" \
  "-L$(dirname "$LAPACK_SHARED_LIBRARY")" \
  -lprik_full_lapack \
  --f2cmap "$EXAMPLE_WORKSPACE/examples/lapack/lapack.f2cmap" \
  --build-dir "$LAPACK_F2PY_ROOT/generated" \
  --f77flags=-O0 \
  --f90flags="-O0 -I$LAPACK_MODULE_DIR" \
  --opt=-O0
