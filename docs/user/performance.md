---
title: Performance
description: Reproducible x2py and f2py binding-performance results
audience: users
prerequisites: x2py repository checkout
related: getting-started/index.md, guide/index.md
status: maintained
publication: reviewed
---

# Performance

**Low-overhead Python calls for real Fortran workloads.**

<!-- x2py-performance-summary:start -->
On the benchmark system, the normal x2py interface delivered a **1.06× geometric-mean
speedup over NumPy's f2py**. Across 13 workloads, x2py was faster in 8 and f2py in 2; 3
workloads showed no statistically significant difference.

<div class="x2py-performance-summary" role="group" aria-label="Benchmark summary">
  <div class="x2py-performance-metric">
    <strong>1.06×</strong>
    <span>x2py geometric-mean speedup</span>
  </div>
  <div class="x2py-performance-metric">
    <strong>8 of 13</strong>
    <span>workloads faster with x2py</span>
  </div>
  <div class="x2py-performance-metric">
    <strong>1.38×</strong>
    <span>best measured x2py speedup</span>
  </div>
</div>
<!-- x2py-performance-summary:end -->

![Relative performance of x2py and f2py across 13 call, vector, and matrix workloads. Values above 1.0 mean x2py is faster.](assets/performance-comparison.svg)
{ .x2py-performance-chart }

The chart shows `f2py time ÷ x2py time`. Values to the right of `1.0×` favor
x2py; values to the left favor f2py. Results close to `1.0×` are practical
parity and may move slightly between machines or runs.

## Detailed Results

Lower times are better. Every row measures the same Fortran operation through
the normal generated interface of each tool.

<!-- x2py-performance-table:start -->
| Workload | f2py | x2py | Relative result |
| --- | ---: | ---: | ---: |
| Empty function call | 44.5 ns | **41.7 ns** | x2py 1.07× faster |
| Add two scalars | **416 ns** | 434 ns | f2py 1.04× faster |
| Increment vector, 1 element | 129 ns | **93.8 ns** | x2py 1.38× faster |
| Increment vector, 16 elements | 142 ns | **106 ns** | x2py 1.33× faster |
| Increment vector, 1,024 elements | **276 ns** | 297 ns | f2py 1.08× faster |
| Increment vector, 1,000,000 elements | 981 µs | 973 µs | No significant difference |
| Sum 4×4 F-order matrix | 165 ns | **148 ns** | x2py 1.12× faster |
| Sum 32×32 F-order matrix | 1.13 µs | **1.12 µs** | x2py 1.02× faster |
| Sum 256×256 F-order matrix | 63.5 µs | **63.3 µs** | x2py 1.003× faster |
| Sum 1,024×1,024 F-order matrix | 1.10 ms | 1.10 ms | No significant difference |
| Update 4×4 F-order matrix | 342 ns | **331 ns** | x2py 1.03× faster |
| Update 256×256 F-order matrix | 25.7 µs | **25.6 µs** | x2py 1.006× faster |
| Update 1,024×1,024 F-order matrix | 1.14 ms | 1.14 ms | No significant difference |
| **Geometric mean** | reference | — | **x2py 1.06× faster** |
<!-- x2py-performance-table:end -->

The smallest workloads expose wrapper overhead most clearly. As more time is
spent inside Fortran, both tools approach the cost of the native operation and
small differences matter less.

## Clean Build Time

Build latency is measured separately from runtime-call overhead. Each timing
starts with an empty output directory and ends when the normal tool command has
generated its wrapper, compiled all native and generated sources, and linked an
extension. Importability and the expected Python exports are checked immediately
afterward, outside the timed interval.

The small-module workload uses the same one-source, five-procedure module as the
runtime suite. The full-library workload gives both tools the same 155-source
reference BLAS implementation and requires all 155 routines to be exposed.

<!-- x2py-performance-build:start -->
Each value is the mean of 6 clean builds after 1 untimed warm-up.

| Clean build workload | f2py | x2py | Relative result |
| --- | ---: | ---: | ---: |
| Small module (1 source, 5 procedures) | 2.92 sec | **1.19 sec** | x2py 2.45× faster |
| Full reference BLAS (155 sources) | **22.0 sec** | 78.7 sec | f2py 3.57× faster |
<!-- x2py-performance-build:end -->

## Fair, Like-for-Like Setup

The suite wraps one set of Fortran kernels with the default x2py and f2py
interfaces. It checks both extensions for the same results before measuring
them. No benchmark-only wrapper mode is used.

<!-- x2py-performance-environment:start -->
- Native and generated sources use `-O3 -march=native -mtune=native`.
- Both interfaces keep the GIL held.
- OpenMP, OpenBLAS, and MKL are limited to one thread.
- `pyperf --rigorous` pins each benchmark to logical CPU `0`.
- Build timings alternate tool order, use clean output directories, and
  exclude post-build import checks.
- CPU: Intel(R) Core(TM) i7-4712MQ CPU @ 2.30GHz.
- Operating system: Ubuntu 26.04 LTS.
- Kernel/platform: `Linux-7.0.0-28-generic-x86_64-with-glibc2.43`.
- Python: 3.14.4.
- NumPy/f2py: 2.5.1.
- Fortran compiler: GNU Fortran 15.2.0.
- pyperf: 2.10.0.
- x2py revision: `f8d7e8a95724`.

These results were recorded on August 1, 2026. Performance depends on the CPU,
compiler, operating system, and background activity, so comparisons should use
results produced together on the same machine.
<!-- x2py-performance-environment:end -->

## Reproduce the Results

The complete [benchmark suite](../../benchmarks/README.md) is included in the
repository. From the repository root, reproduce the build, correctness checks,
measurements, and comparison with one command:

```bash
bash benchmarks/run.sh
```

The command writes the runtime and clean-build `pyperf` result pairs under
`benchmarks/results/` and prints both comparison tables.
