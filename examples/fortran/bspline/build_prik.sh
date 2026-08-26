export EXAMPLE_WORKSPACE="$PWD"
export BSPLINE_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$BSPLINE_BUILD_ROOT/prik/generated"
cd "$BSPLINE_BUILD_ROOT/prik"

python3 -m prik \
  "$EXAMPLE_WORKSPACE/examples/fortran/bspline/native/bspline_kinds_module.F90" \
  "$EXAMPLE_WORKSPACE/examples/fortran/bspline/native/bspline_sub_module.f90" \
  "$EXAMPLE_WORKSPACE/examples/fortran/bspline/native/bspline_oo_module.f90" \
  --out prik_bspline \
  --out-dir "$BSPLINE_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
