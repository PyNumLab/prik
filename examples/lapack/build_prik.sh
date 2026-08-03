export EXAMPLE_WORKSPACE="$PWD"
export LAPACK_BUILD_ROOT="$(mktemp -d)"
export LAPACK_SHARED_LIBRARY="$(
  python -m examples.native_library lapack \
    --compiler "$(command -v gfortran)" \
    --jobs 8
)"
export LAPACK_MODULE_DIR="$(dirname "$LAPACK_SHARED_LIBRARY")/modules"

mkdir -p "$LAPACK_BUILD_ROOT/prik/generated"
cd "$LAPACK_BUILD_ROOT/prik"
python -m prik "$EXAMPLE_WORKSPACE/examples/lapack/native" \
  --out prik_reference_lapack_example \
  --out-dir "$LAPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --no-compile-input-sources \
  --native-objects "$LAPACK_SHARED_LIBRARY" \
  -I "$LAPACK_MODULE_DIR" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
