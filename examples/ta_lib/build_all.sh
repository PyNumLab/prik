if ! source examples/ta_lib/build_prik.sh; then
  return 1 2>/dev/null || exit 1
fi
cd "$EXAMPLE_WORKSPACE"
export PYTHONPATH="$TA_LIB_BUILD_ROOT/prik/generated${PYTHONPATH:+:$PYTHONPATH}"
