export EXAMPLE_WORKSPACE="$PWD"
export LIBM_BUILD_ROOT="$(mktemp -d)"

LIBM_COMPILER="${PRIK_LIBM_CC:-cc}"
if ! LIBM_COMPILER_PATH="$(command -v "$LIBM_COMPILER")"; then
  echo "libm example: C compiler not found: $LIBM_COMPILER" >&2
  return 1 2>/dev/null || exit 1
fi
export LIBM_COMPILER_PATH

mkdir -p "$LIBM_BUILD_ROOT/prik/contract" "$LIBM_BUILD_ROOT/prik/generated"
cd "$LIBM_BUILD_ROOT/prik"

if ! python3 -m prik generate --pyi --language c \
  "$EXAMPLE_WORKSPACE/examples/libm/libm_probe.h" \
  --compiler "$LIBM_COMPILER_PATH" \
  --std c99 \
  --include-exposure roots-only \
  --export-symbols "$EXAMPLE_WORKSPACE/examples/libm/iso_c99_routines.txt" \
  --out "$LIBM_BUILD_ROOT/prik/contract/libm_api.pyi"; then
  return 1 2>/dev/null || exit 1
fi

if ! python3 -m prik --language c "$LIBM_BUILD_ROOT/prik/contract/libm_api.pyi" \
  --out prik_reference_libm \
  --out-dir "$LIBM_BUILD_ROOT/prik/generated" \
  --compiler "$LIBM_COMPILER_PATH" \
  --native-library m \
  --positional-only \
  --collision-adapter-all; then
  return 1 2>/dev/null || exit 1
fi
