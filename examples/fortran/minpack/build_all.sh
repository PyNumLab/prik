source examples/fortran/minpack/build_prik.sh
cd "$EXAMPLE_WORKSPACE"
export PYTHONPATH="$MINPACK_BUILD_ROOT/prik${PYTHONPATH:+:$PYTHONPATH}"
