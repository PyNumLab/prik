---
title: Performance
description: Reproducible PRIK and f2py binding-performance results
audience: users
prerequisites: PRIK repository checkout
related: getting-started/index.md, guide/index.md
status: maintained
publication: reviewed
---

# Performance

**Low-overhead Python calls for real Fortran workloads.**

<!-- prik-performance-summary:start -->
On the benchmark system, the normal PRIK interface delivered a **1.05× geometric-mean
speedup over NumPy's f2py**. Across 13 workloads, PRIK was faster in 7 and f2py in 5; 1
workload showed no statistically significant difference.

<div class="prik-performance-summary" role="group" aria-label="Benchmark summary">
  <div class="prik-performance-metric">
    <strong>1.05×</strong>
    <span>PRIK geometric-mean speedup</span>
  </div>
  <div class="prik-performance-metric">
    <strong>7 of 13</strong>
    <span>workloads faster with PRIK</span>
  </div>
  <div class="prik-performance-metric">
    <strong>1.49×</strong>
    <span>best measured PRIK speedup</span>
  </div>
</div>
<!-- prik-performance-summary:end -->

![Relative performance of PRIK and f2py across 13 call, vector, and matrix workloads. Values above 1.0 mean PRIK is faster.](assets/performance-comparison.svg)
{ .prik-performance-chart }

The chart shows `f2py time ÷ PRIK time`. Values to the right of `1.0×` favor
PRIK; values to the left favor f2py. Results close to `1.0×` are practical
parity and may move slightly between machines or runs.

## Detailed Results

Lower times are better. Every row measures the same Fortran operation through
the normal generated interface of each tool.

<!-- prik-performance-table:start -->
| Workload | f2py | PRIK | Relative result |
| --- | ---: | ---: | ---: |
| Empty function call | 46.2 ns | **42.9 ns** | PRIK 1.08× faster |
| Add two scalars | **426 ns** | 440 ns | f2py 1.03× faster |
| Increment vector, 1 element | 134 ns | **89.9 ns** | PRIK 1.49× faster |
| Increment vector, 16 elements | 145 ns | **101 ns** | PRIK 1.43× faster |
| Increment vector, 1,024 elements | **283 ns** | 299 ns | f2py 1.06× faster |
| Increment vector, 1,000,000 elements | 1.19 ms | 1.21 ms | No significant difference |
| Sum 4×4 F-order matrix | 166 ns | **148 ns** | PRIK 1.13× faster |
| Sum 32×32 F-order matrix | 1.15 µs | **1.13 µs** | PRIK 1.02× faster |
| Sum 256×256 F-order matrix | **63.5 µs** | 64.1 µs | f2py 1.009× faster |
| Sum 1,024×1,024 F-order matrix | **1.09 ms** | 1.22 ms | f2py 1.12× faster |
| Update 4×4 F-order matrix | 346 ns | **324 ns** | PRIK 1.07× faster |
| Update 256×256 F-order matrix | 26.0 µs | **25.7 µs** | PRIK 1.01× faster |
| Update 1,024×1,024 F-order matrix | **1.13 ms** | 1.42 ms | f2py 1.25× faster |
| **Geometric mean** | reference | — | **PRIK 1.05× faster** |
<!-- prik-performance-table:end -->

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
Each workload is built once as a development build with `-O0` and once as an
optimized build with `-O3 -march=native -mtune=native`.

![Clean end-to-end build time for PRIK and f2py under development and optimized compiler profiles. Lower times are better.](assets/build-time-comparison.svg)
{ .prik-performance-chart }

<!-- prik-performance-build:start -->
Each value is the mean of 6 clean builds after 1 untimed warm-up.

| Clean build workload | f2py | PRIK | Relative result |
| --- | ---: | ---: | ---: |
| Development (`-O0`) · small module (1 source, 5 procedures) | 2.37 sec | **867 ms** | PRIK 2.73× faster |
| Development (`-O0`) · full reference BLAS (155 sources) | 10.8 sec | **9.29 sec** | PRIK 1.16× faster |
| Optimized (`-O3 -march=native -mtune=native`) · small module (1 source, 5 procedures) | 2.88 sec | **1.03 sec** | PRIK 2.80× faster |
| Optimized (`-O3 -march=native -mtune=native`) · full reference BLAS (155 sources) | **22.3 sec** | 33.1 sec | f2py 1.48× faster |
<!-- prik-performance-build:end -->

## Fair, Like-for-Like Setup

The suite wraps one set of Fortran kernels with the default PRIK and f2py
interfaces. It checks both extensions for the same results before measuring
them. No benchmark-only wrapper mode is used.

<!-- prik-performance-environment:start -->
- Runtime native and generated sources use `-O3 -march=native -mtune=native`.
- Clean builds use development (`-O0`) and optimized
  (`-O3 -march=native -mtune=native`) profiles.
- Both interfaces keep the GIL held.
- OpenMP, OpenBLAS, and MKL are limited to one thread.
- `pyperf --rigorous` pins each benchmark to logical CPU `0`.
- PRIK build timings use up to 8 concurrent compiler
  processes; f2py uses its normal Meson/Ninja scheduler.
- Build timings alternate tool order, use clean output directories, and exclude
  post-build import checks.
- CPU: Intel(R) Core(TM) i7-4712MQ CPU @ 2.30GHz.
- Operating system: Ubuntu 26.04 LTS.
- Kernel/platform: `Linux-7.0.0-28-generic-x86_64-with-glibc2.43`.
- Python: 3.14.4.
- NumPy/f2py: 2.5.1.
- Fortran compiler: GNU Fortran 15.2.0.
- pyperf: 2.10.0.
- PRIK revision: `0bcaafdf162d`.

These results were recorded on August 1, 2026. Performance depends on the CPU,
compiler, operating system, and background activity, so comparisons should use
results produced together on the same machine.
<!-- prik-performance-environment:end -->

## Reproduce the Results

The complete [benchmark suite](../../benchmarks/README.md) is included in the
repository. From the repository root, reproduce the build, correctness checks,
measurements, and comparison with one command:

```bash
bash benchmarks/run.sh
```

The command writes the runtime and clean-build `pyperf` result pairs under
`benchmarks/results/` and prints both comparison tables.
