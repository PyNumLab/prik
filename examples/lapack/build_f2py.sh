cd "$EXAMPLE_WORKSPACE"
export LAPACK_F2PY_ROOT="$LAPACK_BUILD_ROOT/f2py"
python -m examples.lapack.f2py_build \
  "$LAPACK_F2PY_ROOT" \
  "$LAPACK_SHARED_LIBRARY" \
  --compiler "$(command -v gfortran)"
