source examples/blas/build_prik.sh
source "$EXAMPLE_WORKSPACE/examples/blas/build_f2py.sh"
cd "$EXAMPLE_WORKSPACE"
export PYTHONPATH="$BLAS_BUILD_ROOT/prik:$BLAS_F2PY_ROOT${PYTHONPATH:+:$PYTHONPATH}"
