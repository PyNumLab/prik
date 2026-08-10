source examples/fftpack/build_prik.sh
cd "$EXAMPLE_WORKSPACE"
export PYTHONPATH="$FFTPACK_BUILD_ROOT/prik${PYTHONPATH:+:$PYTHONPATH}"
