#!/usr/bin/env bash

set -euo pipefail

benchmark_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$benchmark_dir"

rm -rf bench_f2py.*.so build/f2py
mkdir -p build/f2py

CFLAGS="-O3 -march=native -mtune=native" \
FFLAGS="-O3 -march=native -mtune=native" \
F90FLAGS="-O3 -march=native -mtune=native" \
python3 -m numpy.f2py \
    -c \
    -m bench_f2py \
    sources/kernels.f90 \
    --build-dir build/f2py \
    --f90flags="-O3 -march=native -mtune=native" \
    --opt="-O3 -march=native -mtune=native"
