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

On the benchmark system, the normal x2py interface delivered a **1.13×
geometric-mean speedup over NumPy's f2py**. x2py was faster in 11 of the 13
measured workloads, with its largest advantage reaching **1.65×** for a
1,024-element vector.

<div class="x2py-performance-summary" role="group" aria-label="Benchmark summary">
  <div class="x2py-performance-metric">
    <strong>1.13×</strong>
    <span>geometric-mean speedup</span>
  </div>
  <div class="x2py-performance-metric">
    <strong>11 of 13</strong>
    <span>workloads faster</span>
  </div>
  <div class="x2py-performance-metric">
    <strong>1.65×</strong>
    <span>best measured speedup</span>
  </div>
</div>

![Relative performance of x2py and f2py across 13 call, vector, and matrix workloads. Values above 1.0 mean x2py is faster.](assets/performance-comparison.svg)
{ .x2py-performance-chart }

The chart shows `f2py time ÷ x2py time`. Values to the right of `1.0×` favor
x2py; values to the left favor f2py. Results close to `1.0×` are practical
parity and may move slightly between machines or runs.

## Detailed Results

Lower times are better. Every row measures the same Fortran operation through
the normal generated interface of each tool.

| Workload | f2py | x2py | Relative result |
| --- | ---: | ---: | ---: |
| Empty function call | 45.2 ns | **44.2 ns** | x2py 1.02× faster |
| Add two scalars | **443 ns** | 457 ns | f2py 1.03× faster |
| Increment vector, 1 element | 139 ns | **99.1 ns** | x2py 1.40× faster |
| Increment vector, 16 elements | 151 ns | **110 ns** | x2py 1.37× faster |
| Increment vector, 1,024 elements | 341 ns | **207 ns** | x2py 1.65× faster |
| Increment vector, 1,000,000 elements | **1.35 ms** | 1.44 ms | f2py 1.06× faster |
| Sum 4×4 F-order matrix | 171 ns | **149 ns** | x2py 1.14× faster |
| Sum 32×32 F-order matrix | 1.17 µs | **1.13 µs** | x2py 1.04× faster |
| Sum 256×256 F-order matrix | 65.7 µs | **64.5 µs** | x2py 1.02× faster |
| Sum 1,024×1,024 F-order matrix | 1.26 ms | **1.11 ms** | x2py 1.14× faster |
| Update 4×4 F-order matrix | 354 ns | **322 ns** | x2py 1.10× faster |
| Update 256×256 F-order matrix | 26.0 µs | **25.4 µs** | x2py 1.02× faster |
| Update 1,024×1,024 F-order matrix | 1.16 ms | **1.04 ms** | x2py 1.12× faster |
| **Geometric mean** | reference | — | **x2py 1.13× faster** |

The smallest workloads expose wrapper overhead most clearly. As more time is
spent inside Fortran, both tools approach the cost of the native operation and
small differences matter less.

## Fair, Like-for-Like Setup

The suite wraps one set of Fortran kernels with the default x2py and f2py
interfaces. It checks both extensions for the same results before measuring
them. No benchmark-only wrapper mode is used.

- Native and generated sources use `-O3 -march=native -mtune=native`.
- Both interfaces keep the GIL held.
- OpenMP, OpenBLAS, and MKL are limited to one thread.
- `pyperf --rigorous` runs each benchmark on logical CPU 0.
- The benchmark system runs Python 3.14.4, NumPy/f2py 2.5.1, GNU Fortran
  15.2.0, and pyperf 2.10.0 on Linux.
- The CPU is an Intel Core i7-4712MQ at 2.30 GHz.

These results were recorded on August 1, 2026. Performance depends on the CPU,
compiler, operating system, and background activity, so comparisons should use
results produced together on the same machine.

## Reproduce the Results

The complete [benchmark suite](../../benchmarks/README.md) is included in the
repository. From the repository root, reproduce the build, correctness checks,
measurements, and comparison with one command:

```bash
bash benchmarks/run.sh
```

The command writes both `pyperf` result files under `benchmarks/results/` and
prints the full comparison table.
