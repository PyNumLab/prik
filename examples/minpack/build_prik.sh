export EXAMPLE_WORKSPACE="$PWD"
export MINPACK_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$MINPACK_BUILD_ROOT/prik/generated"
cd "$MINPACK_BUILD_ROOT/prik"

python3 -m prik "$EXAMPLE_WORKSPACE/examples/minpack/native/minpack.f90" \
  --out prik_reference_minpack \
  --out-dir "$MINPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
