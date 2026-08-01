#!/usr/bin/env bash

set -euo pipefail

benchmark_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$benchmark_dir"

rm -rf *.so __x2py__ results

echo
echo "========================================"
echo " Building X2PY wrapper"
echo "========================================"
bash build/x2py.sh

echo
echo "========================================"
echo " Building F2PY wrapper"
echo "========================================"
bash build/f2py.sh
echo "========================================"
echo "========================================"
echo "========================================"

echo
echo "Check correctness of all shared libraries..."
python3 correctness.py
echo
echo "========================================"
echo "========================================"
echo "========================================"

mkdir -p results

BINDING_TOOL=x2py \
OMP_NUM_THREADS=1 \
OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
python3 runtime.py \
    --rigorous \
    --affinity=0 \
    --inherit-environ=BINDING_TOOL,OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS \
    -o results/x2py.json

BINDING_TOOL=f2py \
OMP_NUM_THREADS=1 \
OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
python3 runtime.py --rigorous \
    --affinity=0 \
    --inherit-environ=BINDING_TOOL,OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS \
    -o results/f2py.json

python3 -m pyperf compare_to \
    results/f2py.json \
    results/x2py.json \
    --table
