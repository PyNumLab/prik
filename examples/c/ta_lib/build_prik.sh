export EXAMPLE_WORKSPACE="$PWD"
export TA_LIB_BUILD_ROOT="$(mktemp -d)"

TA_LIB_COMPILER="${PRIK_TALIB_CC:-cc}"
if ! TA_LIB_COMPILER_PATH="$(command -v "$TA_LIB_COMPILER")"; then
  echo "TA-Lib example: C compiler not found: $TA_LIB_COMPILER" >&2
  return 1 2>/dev/null || exit 1
fi
export TA_LIB_COMPILER_PATH

if ! TA_LIB_PREFIX="$(python3 "$EXAMPLE_WORKSPACE/examples/c/ta_lib/native_build.py" \
  --compiler "$TA_LIB_COMPILER_PATH")"; then
  return 1 2>/dev/null || exit 1
fi
export TA_LIB_PREFIX
if ! TA_LIB_REGTEST_CACHE="$(python3 "$EXAMPLE_WORKSPACE/examples/c/ta_lib/native_build.py" \
  --compiler "$TA_LIB_COMPILER_PATH" --artifact regtest)"; then
  return 1 2>/dev/null || exit 1
fi
if ! TA_LIB_REFERENCE_CACHE="$(python3 "$EXAMPLE_WORKSPACE/examples/c/ta_lib/native_build.py" \
  --compiler "$TA_LIB_COMPILER_PATH" --artifact reference)"; then
  return 1 2>/dev/null || exit 1
fi
if ! TA_LIB_SHARED_LIBRARY="$(python3 "$EXAMPLE_WORKSPACE/examples/c/ta_lib/native_build.py" \
  --compiler "$TA_LIB_COMPILER_PATH" --artifact library)"; then
  return 1 2>/dev/null || exit 1
fi
export TA_LIB_SHARED_LIBRARY
export LIBRARY_PATH="$TA_LIB_PREFIX/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
if [[ "$(uname -s)" == "Darwin" ]]; then
  export DYLD_LIBRARY_PATH="$TA_LIB_PREFIX/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
else
  export LD_LIBRARY_PATH="$TA_LIB_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

mkdir -p \
  "$TA_LIB_BUILD_ROOT/prik/contract" \
  "$TA_LIB_BUILD_ROOT/prik/generated" \
  "$TA_LIB_BUILD_ROOT/reference"
cd "$TA_LIB_BUILD_ROOT/prik"

if ! python3 -m prik generate --pyi --language c \
  "$EXAMPLE_WORKSPACE/examples/c/ta_lib/ta_lib_probe.h" \
  --compiler "$TA_LIB_COMPILER_PATH" \
  --std c99 \
  -I "$TA_LIB_PREFIX/include" \
  --out "$TA_LIB_BUILD_ROOT/prik/contract/ta_lib_public_api.pyi"; then
  return 1 2>/dev/null || exit 1
fi

if ! python3 -m prik --language c "$EXAMPLE_WORKSPACE/examples/c/ta_lib/ta_lib_api.pyi" \
  --out prik_reference_talib \
  --out-dir "$TA_LIB_BUILD_ROOT/prik/generated" \
  --compiler "$TA_LIB_COMPILER_PATH" \
  --native-library ta-lib \
  --collision-adapter-all \
  --jobs "${PRIK_TALIB_JOBS:-${PRIK_REAL_LIBRARY_NATIVE_JOBS:-4}}"; then
  return 1 2>/dev/null || exit 1
fi

cp "$TA_LIB_REGTEST_CACHE" "$TA_LIB_BUILD_ROOT/reference/ta_regtest"
cp "$TA_LIB_REFERENCE_CACHE" "$TA_LIB_BUILD_ROOT/reference/ta_ref_serve"
cp "$EXAMPLE_WORKSPACE/examples/c/ta_lib/reference_adapter.py" "$TA_LIB_BUILD_ROOT/reference/ta_codegen_serve_c"
chmod +x \
  "$TA_LIB_BUILD_ROOT/reference/ta_regtest" \
  "$TA_LIB_BUILD_ROOT/reference/ta_ref_serve" \
  "$TA_LIB_BUILD_ROOT/reference/ta_codegen_serve_c"
export PRIK_TALIB_REGTEST="$TA_LIB_BUILD_ROOT/reference/ta_regtest"
export PRIK_TALIB_REFERENCE_SERVER="$TA_LIB_BUILD_ROOT/reference/ta_ref_serve"
export PRIK_TALIB_LIBRARY="$TA_LIB_SHARED_LIBRARY"
export PRIK_TALIB_CONTRACT="$EXAMPLE_WORKSPACE/examples/c/ta_lib/ta_lib_api.pyi"
export PRIK_TALIB_COVERAGE="$TA_LIB_BUILD_ROOT/reference/prik_coverage.txt"
