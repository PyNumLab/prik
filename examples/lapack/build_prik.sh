export EXAMPLE_WORKSPACE="$PWD"
export LAPACK_BUILD_ROOT="$(mktemp -d)"
export LAPACK_SHARED_LIBRARY="$(
  python -m examples.native_library lapack \
    --compiler "$(command -v gfortran)" \
    --jobs 8
)"

python -m prik generate \
  --pyi examples/lapack/native \
  --language fortran \
  --out "$LAPACK_BUILD_ROOT/contracts/lapack"

# Remove the LA_CONSTANTS and LA_XISNAN imports from the generated root contract.
python -c 'import sys; from pathlib import Path; p=Path(sys.argv[1]); s=p.read_text(encoding="utf-8")
p.write_text(s.replace("from . import LA_CONSTANTS\n", "").replace("from . import LA_XISNAN\n", ""), encoding="utf-8")' \
  "$LAPACK_BUILD_ROOT/contracts/lapack/__init__.pyi"

mkdir -p "$LAPACK_BUILD_ROOT/prik/generated"
cd "$LAPACK_BUILD_ROOT/prik"
python -m prik "$LAPACK_BUILD_ROOT/contracts/lapack/__init__.pyi" \
  --out prik_reference_lapack_example \
  --out-dir "$LAPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --native-objects "$LAPACK_SHARED_LIBRARY" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
