#!/usr/bin/env bash

set -euo pipefail

benchmark_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$benchmark_dir"

benchmark_first="${PRIK_BENCHMARK_FIRST:-prik}"
case "$benchmark_first" in
    prik)
        binding_tools=(prik f2py)
        ;;
    f2py)
        binding_tools=(f2py prik)
        ;;
    *)
        echo "PRIK_BENCHMARK_FIRST must be 'prik' or 'f2py'." >&2
        exit 2
        ;;
esac

rm -rf *.so __prik__ results

echo
echo "========================================"
echo " Building PRIK wrapper"
echo "========================================"
bash build/prik.sh

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
echo "Check direct/adapted correctness and generated artifacts..."
python3 direct_preflight.py
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
    --runs "${PRIK_BUILD_BENCHMARK_RUNS:-4}" \
    --warmups "${PRIK_BUILD_BENCHMARK_WARMUPS:-1}" \
    --first "$benchmark_first"

echo
echo "========================================"
echo " Benchmarking direct/adapted clean builds"
echo "========================================"
python3 direct_build_time.py \
    --runs "${PRIK_DIRECT_BUILD_BENCHMARK_RUNS:-4}" \
    --warmups "${PRIK_DIRECT_BUILD_BENCHMARK_WARMUPS:-1}" \
    --first "$benchmark_first"

runtime_groups=(
    calls
    vector-latency
    vector-bulk
    matrix-sum-latency
    matrix-sum-bulk
    matrix-update-latency
    matrix-update-bulk
)
runtime_passes=(prik-first f2py-first)
for runtime_group in "${runtime_groups[@]}"; do
    for runtime_pass in "${runtime_passes[@]}"; do
        case "$runtime_pass" in
            prik-first)
                binding_tools=(prik f2py)
                ;;
            f2py-first)
                binding_tools=(f2py prik)
                ;;
        esac
        echo "Runtime benchmark order ($runtime_group, $runtime_pass): ${binding_tools[*]}"
        for binding_tool in "${binding_tools[@]}"; do
            result_file="results/$binding_tool-$runtime_pass.json"
            if [[ -f "$result_file" ]]; then
                result_args=(--append "$result_file")
            else
                result_args=(-o "$result_file")
            fi
            BINDING_TOOL="$binding_tool" \
            PRIK_RUNTIME_BENCHMARK_GROUP="$runtime_group" \
            PRIK_RUNTIME_ORDER_PASS="$runtime_pass" \
            OMP_NUM_THREADS=1 \
            OPENBLAS_NUM_THREADS=1 \
            MKL_NUM_THREADS=1 \
            python3 runtime.py \
                --rigorous \
                --affinity=0 \
                --inherit-environ=BINDING_TOOL,PRIK_RUNTIME_BENCHMARK_GROUP,PRIK_RUNTIME_ORDER_PASS,PRIK_BENCHMARK_CPU_MODEL,OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS \
                "${result_args[@]}"
        done
    done
done

for binding_tool in prik f2py; do
    python3 -m pyperf convert \
        "results/$binding_tool-prik-first.json" \
        --add "results/$binding_tool-f2py-first.json" \
        --output "results/$binding_tool.json"
done

direct_runtime_passes=(forward reverse)
for runtime_pass in "${direct_runtime_passes[@]}"; do
    case "$runtime_pass" in
        forward)
            direct_routes=(prik-direct f2py-direct prik-adapted)
            ;;
        reverse)
            direct_routes=(prik-adapted f2py-direct prik-direct)
            ;;
    esac
    echo "Direct runtime benchmark order ($runtime_pass): ${direct_routes[*]}"
    for direct_route in "${direct_routes[@]}"; do
        PRIK_DIRECT_BENCHMARK_ROUTE="$direct_route" \
        PRIK_DIRECT_ORDER_PASS="$runtime_pass" \
        OMP_NUM_THREADS=1 \
        OPENBLAS_NUM_THREADS=1 \
        MKL_NUM_THREADS=1 \
        python3 direct_runtime.py \
            --rigorous \
            --affinity=0 \
            --inherit-environ=PRIK_DIRECT_BENCHMARK_ROUTE,PRIK_DIRECT_ORDER_PASS,PRIK_DIRECT_PREFLIGHT_REPORT,PRIK_BENCHMARK_CPU_MODEL,OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS \
            -o "results/$direct_route-$runtime_pass.json"
    done
done

for direct_route in prik-direct f2py-direct prik-adapted; do
    python3 -m pyperf convert \
        "results/$direct_route-forward.json" \
        --add "results/$direct_route-reverse.json" \
        --output "results/$direct_route.json"
done

python3 -m pyperf compare_to \
    results/f2py.json \
    results/prik.json \
    --table

python3 -m pyperf compare_to \
    results/f2py-direct.json \
    results/prik-direct.json \
    --table

python3 -m pyperf compare_to \
    results/prik-adapted.json \
    results/prik-direct.json \
    --table

python3 -m pyperf compare_to \
    results/f2py-direct-build.json \
    results/prik-direct-build.json \
    --table

python3 -m pyperf compare_to \
    results/prik-adapted-build.json \
    results/prik-direct-build.json \
    --table

python3 -m pyperf compare_to \
    results/f2py-build.json \
    results/prik-build.json \
    --table
