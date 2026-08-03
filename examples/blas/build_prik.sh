export EXAMPLE_WORKSPACE="$PWD"
export BLAS_BUILD_ROOT="$(mktemp -d)"
export BLAS_SHARED_LIBRARY="$(
  python -m examples.native_library blas \
    --compiler "$(command -v gfortran)" \
    --jobs 8
)"

mkdir -p "$BLAS_BUILD_ROOT/prik/generated"
cd "$BLAS_BUILD_ROOT/prik"

python -m prik "$EXAMPLE_WORKSPACE/examples/blas/native" \
  --out prik_reference_blas \
  --out-dir "$BLAS_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --no-compile-input-sources \
  --native-objects "$BLAS_SHARED_LIBRARY" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
