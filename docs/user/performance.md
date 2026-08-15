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
On the benchmark system, the normal PRIK interface delivered a **1.10× geometric-mean
speedup over NumPy's f2py**. Across 13 workloads, PRIK was faster in 11 and f2py in 2;
all comparisons were statistically significant.

<div class="prik-performance-summary" role="group" aria-label="Benchmark summary">
  <div class="prik-performance-metric">
    <strong>1.10×</strong>
    <span>PRIK geometric-mean speedup</span>
  </div>
  <div class="prik-performance-metric">
    <strong>11 of 13</strong>
    <span>workloads faster with PRIK</span>
  </div>
  <div class="prik-performance-metric">
    <strong>1.28×</strong>
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
| Empty function call | 34.6 ns | **29.9 ns** | PRIK 1.16× faster |
| Add two scalars | 341 ns | **316 ns** | PRIK 1.08× faster |
| Increment vector, 1 element | 103 ns | **80.6 ns** | PRIK 1.27× faster |
| Increment vector, 16 elements | 106 ns | **82.8 ns** | PRIK 1.28× faster |
| Increment vector, 1,024 elements | 262 ns | **211 ns** | PRIK 1.24× faster |
| Increment vector, 1,000,000 elements | 186 µs | **183 µs** | PRIK 1.02× faster |
| Sum 4×4 F-order matrix | 127 ns | **121 ns** | PRIK 1.05× faster |
| Sum 32×32 F-order matrix | 718 ns | **711 ns** | PRIK 1.01× faster |
| Sum 256×256 F-order matrix | **38.9 µs** | 39.0 µs | f2py 1.002× faster |
| Sum 1,024×1,024 F-order matrix | **621 µs** | 622 µs | f2py 1.002× faster |
| Update 4×4 F-order matrix | 249 ns | **215 ns** | PRIK 1.16× faster |
| Update 256×256 F-order matrix | 13.0 µs | **12.7 µs** | PRIK 1.02× faster |
| Update 1,024×1,024 F-order matrix | 199 µs | **193 µs** | PRIK 1.03× faster |
| **Geometric mean** | reference | — | **PRIK 1.10× faster** |
<!-- prik-performance-table:end -->

The smallest workloads expose wrapper overhead most clearly. As more time is
spent inside Fortran, both tools approach the cost of the native operation and
small differences matter less.

## Direct `bind(C)` Entrypoints

This separate cohort isolates three scalar call boundaries: an empty
subroutine, a scalar function, and a scalar subroutine with an output. PRIK and
f2py compile the same Fortran source and call the same `bind(C)` labels. The
normal-interface geometric mean above remains unchanged.

Before timing, artifact inspection verifies that neither direct route contains
a generated Fortran procedure adapter. Each Python binding object refers to
the three user labels, while its native object and linked extension define
them. f2py keeps its Python C/API binding and uses `--no-wrap-functions` plus
`--skip-empty-wrappers`; these options remove unnecessary generated Fortran
wrappers, not the Python binding. The PRIK adapter control measures equivalent
ordinary-Fortran procedures separately.

<!-- prik-performance-direct:start -->
### Direct PRIK and f2py

| Workload | f2py direct | PRIK direct | Relative result |
| --- | ---: | ---: | ---: |
| Empty call | 36.5 ns | **29.7 ns** | PRIK direct 1.23× faster |
| Scalar function | 121 ns | **103 ns** | PRIK direct 1.17× faster |
| Scalar subroutine | 122 ns | **103 ns** | PRIK direct 1.18× faster |
| **Geometric mean** | reference | — | **PRIK direct 1.19× faster** |

### PRIK adapter control

| Workload | PRIK adapted | PRIK direct | Relative result |
| --- | ---: | ---: | ---: |
| Empty call | 29.9 ns | **29.7 ns** | PRIK direct 1.008× faster |
| Scalar function | 104 ns | **103 ns** | PRIK direct 1.01× faster |
| Scalar subroutine | 105 ns | **103 ns** | PRIK direct 1.01× faster |
| **Geometric mean** | reference | — | **PRIK direct 1.01× faster** |
<!-- prik-performance-direct:end -->

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
Each value is the mean of 4 clean builds after 1 untimed warm-up.

| Clean build workload | f2py | PRIK | Relative result |
| --- | ---: | ---: | ---: |
| Development (`-O0`) · small module (1 source, 5 procedures) | 1.50 sec | **550 ms** | PRIK 2.73× faster |
| Development (`-O0`) · full reference BLAS (155 sources) | 7.00 sec | **5.05 sec** | PRIK 1.39× faster |
| Optimized (`-O3 -march=native -mtune=native`) · small module (1 source, 5 procedures) | 1.72 sec | **644 ms** | PRIK 2.68× faster |
| Optimized (`-O3 -march=native -mtune=native`) · full reference BLAS (155 sources) | **11.0 sec** | 13.3 sec | f2py 1.22× faster |
<!-- prik-performance-build:end -->

## Direct-Entrypoint Clean Build Time

The direct build workload compiles the same one-source, three-procedure module
used by the direct runtime cohort with the optimized profile. It includes
contract or signature processing, Python binding generation, compilation, and
linking. The separate PRIK adapter control shows whether omitting one generated
Fortran adapter materially changes this small end-to-end build.

<!-- prik-performance-direct-build:start -->
Each value is the mean of 4 clean builds after 1 untimed warm-up.

### Direct PRIK and f2py

| Clean build workload | f2py direct | PRIK direct | Relative result |
| --- | ---: | ---: | ---: |
| Optimized (`-O3 -march=native -mtune=native`) · small direct module (1 source, 3 procedures) | 1.70 sec | **545 ms** | PRIK direct 3.12× faster |

### PRIK adapter control

| Clean build workload | PRIK adapted | PRIK direct | Relative result |
| --- | ---: | ---: | ---: |
| Optimized (`-O3 -march=native -mtune=native`) · small direct module (1 source, 3 procedures) | 547 ms | 545 ms | No significant difference |
<!-- prik-performance-direct-build:end -->

## Should I use PRIK or f2py?

These benchmarks answer two narrow questions: runtime-call overhead and clean
build time for the same Fortran sources on the same machine. They do not rank
feature coverage, API design, ecosystem maturity, or suitability for every
project.

Use [NumPy's f2py](https://numpy.org/doc/stable/f2py/) when its established
generated API—or an editable
[`.pyf` signature](https://numpy.org/doc/stable/f2py/signature-file.html)—is
enough for your project.

Choose PRIK when you want to design the Python API, not just generate a wrapper.
Its editable [semantic `.pyi` contract](reference/pyi-contracts/index.md) is a
simpler, more Pythonic place to rename or hide exports, flatten modules, reorder
or hide native arguments, and return native outputs as Python results.

PRIK treats [NumPy arrays](guide/arrays.md) as complete API contracts: dtype,
rank, shape, memory layout, contiguity, strides, mutation, and copy behavior are
all explicit. This includes
[supported positive-stride views](guide/arrays.md#strided-views) without copying.

PRIK also covers important Fortran features: supported
[derived types](guide/wrapping-derived-types.md) as Python classes,
[allocatables](guide/allocatables.md), documented
[pointer forms](guide/pointers.md), native errors as
[Python exceptions](guide/error-handling.md), and
[overloaded procedures](guide/generic-interfaces.md). PRIK is currently alpha,
so check the linked guides for exact limitations.

## Fair, Like-for-Like Setup

The normal-interface suite wraps one set of Fortran kernels with the default
PRIK and f2py interfaces. It checks both extensions for the same results before
measuring them. The direct-entrypoint cohort is kept separate and uses only the
documented direct-call modes described above.

Each runtime group uses an A/B/B/A sequence with equal PRIK-first and f2py-first
process budgets. The two passes are merged before significance, winner counts
and geometric means are calculated, preventing either tool from consistently
benefiting from being measured second. Clean-build rounds alternate tool order
independently.

<!-- prik-performance-environment:start -->
- Runtime native and generated sources use `-O3 -march=native -mtune=native`.
- Clean builds use development (`-O0`) and optimized
  (`-O3 -march=native -mtune=native`) profiles.
- Both interfaces keep the GIL held.
- OpenMP, OpenBLAS, and MKL are limited to one thread.
- `pyperf --rigorous` pins each benchmark to logical CPU `0`.
- Normal runtime samples combine equal PRIK-first and f2py-first process budgets.
- Direct runtime samples use balanced forward and reverse PRIK-direct,
  f2py-direct, and PRIK-adapted process order.
- PRIK build timings use up to 4 concurrent compiler
  processes; f2py uses its normal Meson/Ninja scheduler.
- Normal and three-route direct build timings alternate tool order, use clean
  output directories, and exclude post-build import checks.
- CPU: Arm Neoverse N2.
- Operating system: Ubuntu 24.04.4 LTS.
- Kernel/platform: `Linux-6.17.0-1022-azure-aarch64-with-glibc2.39`.
- Python: 3.12.13.
- NumPy/f2py: 2.5.1.
- Fortran compiler: GNU Fortran 13.3.0.
- pyperf: 2.10.0.
- PRIK revision: `8ff253070c44`.

These results were recorded on August 15, 2026. Performance depends on the CPU,
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

The command writes the normal, direct, and adapter-control runtime and
clean-build `pyperf` result pairs under `benchmarks/results/` and prints their
comparison tables.
