source examples/lapack/build_prik.sh
source "$EXAMPLE_WORKSPACE/examples/lapack/build_f2py.sh"
cd "$EXAMPLE_WORKSPACE"
export PYTHONPATH="$LAPACK_BUILD_ROOT/prik:$LAPACK_F2PY_ROOT${PYTHONPATH:+:$PYTHONPATH}"
