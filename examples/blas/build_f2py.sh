cd "$EXAMPLE_WORKSPACE"
export BLAS_F2PY_ROOT="$BLAS_BUILD_ROOT/f2py"
python -m examples.blas.f2py_build \
  "$BLAS_F2PY_ROOT" \
  "$BLAS_SHARED_LIBRARY" \
  --compiler "$(command -v gfortran)"
