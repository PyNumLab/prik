export EXAMPLE_WORKSPACE="$PWD"
export FFTPACK_BUILD_ROOT="$(mktemp -d)"
export FFTPACK_NATIVE_DIR="$EXAMPLE_WORKSPACE/examples/fftpack/native"

FFTPACK_PUBLIC_SOURCES=(
  "$FFTPACK_NATIVE_DIR/rk.f90"
  "$FFTPACK_NATIVE_DIR/fftpack.f90"
  "$FFTPACK_NATIVE_DIR"/fftpack_*.f90
)
FFTPACK_LINK_ONLY_SOURCES=()
for source in "$FFTPACK_NATIVE_DIR"/*.f90; do
  case "${source##*/}" in
    rk.f90|fftpack.f90|fftpack_*.f90) continue ;;
  esac
  FFTPACK_LINK_ONLY_SOURCES+=("$source")
done

mkdir -p "$FFTPACK_BUILD_ROOT/prik/generated"
cd "$FFTPACK_BUILD_ROOT/prik"

python3 -m prik "${FFTPACK_PUBLIC_SOURCES[@]}" \
  --native-fortran-sources "${FFTPACK_LINK_ONLY_SOURCES[@]}" \
  --out prik_reference_fftpack \
  --out-dir "$FFTPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
