#!/usr/bin/env bash

set -euo pipefail

benchmark_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$benchmark_dir"

benchmark_first="${X2PY_BENCHMARK_FIRST:-x2py}"
case "$benchmark_first" in
    x2py)
        binding_tools=(x2py f2py)
        ;;
    f2py)
        binding_tools=(f2py x2py)
        ;;
    *)
        echo "X2PY_BENCHMARK_FIRST must be 'x2py' or 'f2py'." >&2
        exit 2
        ;;
esac

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

echo
echo "========================================"
echo " Benchmarking clean end-to-end builds"
echo "========================================"
python3 build_time.py \
    --runs "${X2PY_BUILD_BENCHMARK_RUNS:-6}" \
    --warmups "${X2PY_BUILD_BENCHMARK_WARMUPS:-1}" \
    --first "$benchmark_first"

echo "Benchmark order: ${binding_tools[*]}"
runtime_groups=(
    calls
    vector-latency
    vector-bulk
    matrix-sum-latency
    matrix-sum-bulk
    matrix-update-latency
    matrix-update-bulk
)
for binding_tool in "${binding_tools[@]}"; do
    result_args=(-o "results/$binding_tool.json")
    for runtime_group in "${runtime_groups[@]}"; do
        BINDING_TOOL="$binding_tool" \
        X2PY_RUNTIME_BENCHMARK_GROUP="$runtime_group" \
        OMP_NUM_THREADS=1 \
        OPENBLAS_NUM_THREADS=1 \
        MKL_NUM_THREADS=1 \
        python3 runtime.py \
            --rigorous \
            --affinity=0 \
            --inherit-environ=BINDING_TOOL,X2PY_RUNTIME_BENCHMARK_GROUP,X2PY_BENCHMARK_CPU_MODEL,OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS \
            "${result_args[@]}"
        result_args=(--append "results/$binding_tool.json")
    done
done

python3 -m pyperf compare_to \
    results/f2py.json \
    results/x2py.json \
    --table

python3 -m pyperf compare_to \
    results/f2py-build.json \
    results/x2py-build.json \
    --table
