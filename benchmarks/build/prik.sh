#!/usr/bin/env bash

set -euo pipefail

benchmark_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$benchmark_dir"

rm -rf bench_prik.*.so __prik__
python3 -m prik \
    sources/kernels.f90 \
    --out bench_prik \
    --native-compile-flags="-O3 -march=native -mtune=native" \
    --wrapper-fortran-flags="-O3 -march=native -mtune=native" \
    --wrapper-c-flags="-O3 -march=native -mtune=native" \
    --verbose
