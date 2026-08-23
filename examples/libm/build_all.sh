if ! source examples/libm/build_prik.sh; then
  return 1 2>/dev/null || exit 1
fi
cd "$EXAMPLE_WORKSPACE"
export PYTHONPATH="$LIBM_BUILD_ROOT/prik${PYTHONPATH:+:$PYTHONPATH}"
