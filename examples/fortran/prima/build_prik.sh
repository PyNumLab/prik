export EXAMPLE_WORKSPACE="$PWD"
export PRIMA_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$PRIMA_BUILD_ROOT/prik/generated"

cmake \
  -S "$EXAMPLE_WORKSPACE/examples/fortran/prima" \
  -B "$PRIMA_BUILD_ROOT/native" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_Fortran_COMPILER="$(command -v gfortran)"
cmake --build "$PRIMA_BUILD_ROOT/native" --target primaf --parallel 2

mapfile -t PRIMA_SOURCE_NAMES < "$EXAMPLE_WORKSPACE/examples/fortran/prima/sources.txt"
PRIMA_SOURCES=()
for source in "${PRIMA_SOURCE_NAMES[@]}"; do
  PRIMA_SOURCES+=("$EXAMPLE_WORKSPACE/examples/fortran/prima/native/$source")
done

python3 -m prik generate --pyi \
  "${PRIMA_SOURCES[@]}" \
  --export-symbols "$EXAMPLE_WORKSPACE/examples/fortran/prima/export_symbols.txt" \
  --out "$PRIMA_BUILD_ROOT/contract" \
  --compiler "$(command -v gfortran)" \
  -I "$EXAMPLE_WORKSPACE/examples/fortran/prima/native/common" \
  -D PRIMA_REAL_PRECISION=64 \
  -D PRIMA_INTEGER_KIND=0

cd "$PRIMA_BUILD_ROOT/prik"
python3 -m prik "$PRIMA_BUILD_ROOT/contract/__init__.pyi" \
  --out prik_prima \
  --out-dir "$PRIMA_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --native-link-item "archive:$PRIMA_BUILD_ROOT/native/libprimaf.a" \
  --native-linker-language fortran \
  -I "$PRIMA_BUILD_ROOT/native/mod" \
  --jobs 2
