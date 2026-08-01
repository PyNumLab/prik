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
On the benchmark system, the normal x2py interface delivered a **1.09× geometric-mean
speedup over NumPy's f2py**. Across 13 workloads, x2py was faster in 10 and f2py in 3;
all comparisons were statistically significant.

<div class="x2py-performance-summary" role="group" aria-label="Benchmark summary">
  <div class="x2py-performance-metric">
    <strong>1.09×</strong>
    <span>x2py geometric-mean speedup</span>
  </div>
  <div class="x2py-performance-metric">
    <strong>10 of 13</strong>
    <span>workloads faster with x2py</span>
  </div>
  <div class="x2py-performance-metric">
    <strong>1.49×</strong>
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
| Empty function call | 44.6 ns | **41.2 ns** | x2py 1.08× faster |
| Add two scalars | 436 ns | **426 ns** | x2py 1.02× faster |
| Increment vector, 1 element | 140 ns | **93.7 ns** | x2py 1.49× faster |
| Increment vector, 16 elements | 151 ns | **107 ns** | x2py 1.41× faster |
| Increment vector, 1,024 elements | **283 ns** | 301 ns | f2py 1.07× faster |
| Increment vector, 1,000,000 elements | 1.27 ms | **1.16 ms** | x2py 1.10× faster |
| Sum 4×4 F-order matrix | 168 ns | **162 ns** | x2py 1.04× faster |
| Sum 32×32 F-order matrix | **1.14 µs** | 1.15 µs | f2py 1.008× faster |
| Sum 256×256 F-order matrix | **64.1 µs** | 65.9 µs | f2py 1.03× faster |
| Sum 1,024×1,024 F-order matrix | 1.22 ms | **1.19 ms** | x2py 1.02× faster |
| Update 4×4 F-order matrix | 343 ns | **330 ns** | x2py 1.04× faster |
| Update 256×256 F-order matrix | 26.1 µs | **25.8 µs** | x2py 1.009× faster |
| Update 1,024×1,024 F-order matrix | 1.38 ms | **1.15 ms** | x2py 1.21× faster |
| **Geometric mean** | reference | — | **x2py 1.09× faster** |
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
Each workload is built once as a development build with `-O0` and once as an
optimized build with `-O3 -march=native -mtune=native`.

![Clean end-to-end build time for x2py and f2py under development and optimized compiler profiles. Lower times are better.](assets/build-time-comparison.svg)
{ .x2py-performance-chart }

<!-- x2py-performance-build:start -->
Each value is the mean of 6 clean builds after 1 untimed warm-up.

| Clean build workload | f2py | x2py | Relative result |
| --- | ---: | ---: | ---: |
| Development (`-O0`) · small module (1 source, 5 procedures) | 2.36 sec | **895 ms** | x2py 2.64× faster |
| Development (`-O0`) · full reference BLAS (155 sources) | 10.7 sec | 10.7 sec | No significant difference |
| Optimized (`-O3 -march=native -mtune=native`) · small module (1 source, 5 procedures) | 2.89 sec | **1.04 sec** | x2py 2.77× faster |
| Optimized (`-O3 -march=native -mtune=native`) · full reference BLAS (155 sources) | **21.7 sec** | 39.0 sec | f2py 1.80× faster |
<!-- x2py-performance-build:end -->

## Fair, Like-for-Like Setup

The suite wraps one set of Fortran kernels with the default x2py and f2py
interfaces. It checks both extensions for the same results before measuring
them. No benchmark-only wrapper mode is used.

<!-- x2py-performance-environment:start -->
- Runtime native and generated sources use `-O3 -march=native -mtune=native`.
- Clean builds use development (`-O0`) and optimized
  (`-O3 -march=native -mtune=native`) profiles.
- Both interfaces keep the GIL held.
- OpenMP, OpenBLAS, and MKL are limited to one thread.
- `pyperf --rigorous` pins each benchmark to logical CPU `0`.
- x2py build timings use up to 8 concurrent compiler
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
- x2py revision: `working-tree`.

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
