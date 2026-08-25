---
title: Build and Validate TA-Lib with PRIK
audience: users, advanced users
prerequisites: C support, semantic .pyi contracts
related: ../language-support/c-support.md, ../reference/cli-commands.md, libm-wrapper.md
status: maintained
publication: reviewed
---

# Build and Validate TA-Lib with PRIK

TA-Lib is a C library for technical-analysis indicators over price and volume
series. This maintained example wraps its complete numerical indicator API
with NumPy arrays: all 161 double-input and all 161 float-input functions from
TA-Lib v0.7.1.

The checked-in contract contains those 322 numerical functions plus
initialization and shutdown. The 198 excluded public functions are 161
lookbacks, six global settings, and 31 optional abstraction or metadata
functions. The returned beginning and count replace the need for public
lookbacks; calculations use TA-Lib's default global settings.

## What this example proves

- PRIK can build a large, array-centered C API without a Fortran bridge or an
  ABI-conversion adapter.
- Generated C `int[]`, `float[]`, and `double[]` contracts use the compiler-
  probed NumPy storage for the active target.
- TA-Lib's caller-owned output buffers remain caller-owned NumPy arrays.
- The edited contract hides `outBegIdx` and `outNBElement` as returned metadata,
  while retaining TA-Lib's status code as the first result.
- A fail-closed inventory accounts for every public function in the pinned
  header and reference-checks every numerical entrypoint.

## Versions and requirements

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| TA-Lib | v0.7.1, commit `2247d599bddf37ed37e3a709371517e46efc66f6` |
| Native build | CMake with TA-Lib's regression tools enabled |
| Python | 3.12 in Real Libraries Portability CI |

Install Git, CMake, a C compiler, Python development headers, NumPy, and
pytest. The build helper clones the pinned TA-Lib tag into the user cache,
verifies the exact commit, and installs it into a target-and-compiler-specific
cache directory. No TA-Lib source is vendored in PRIK.

## Build and test

Run from the repository root:

```bash
source examples/ta_lib/build_all.sh
python3 -m pytest -q examples/ta_lib/tests
```

`build_all.sh` leaves the generated extension on `PYTHONPATH` and the
TA-Lib shared library on the platform runtime-library path for the current
shell.

Set `PRIK_TALIB_CC` to select a compiler. Set
`PRIK_TALIB_CACHE_DIR` to choose the native source and build cache.

## Calculate a moving average

TA-Lib writes results into storage supplied by the caller. Allocate an output
array with enough capacity, then use the returned count to select the values
that were written:

```python
import numpy as np

import prik_reference_talib as talib

prices = np.arange(1.0, 11.0, dtype=np.float64)
output = np.empty_like(prices)

status, begin, count = talib.TA_SMA(
    np.intc(0),
    np.intc(prices.size - 1),
    prices,
    np.intc(3),
    output,
)

if status != 0:
    raise RuntimeError(f"TA_SMA failed with status {status}")

print(begin)
print(output[:count])
```

```text
2
[2. 3. 4. 5. 6. 7. 8. 9.]
```

`begin` is the input index corresponding to the first output value.
`count` is the number of values written from the start of `output`.
Multi-output indicators use one caller-owned array per output.

## What the build creates

`build_all.sh` prepares the test environment; it does not run pytest itself.
It performs three checked operations:

1. Fetch, verify, and compile the pinned TA-Lib release, including TA-Lib's
   regression runner and a direct native reference server.
2. Ask PRIK to generate a target-specific inventory from the complete public
   `ta_libc.h` umbrella header. This inventory is used to detect a missing,
   added, or unreviewed public function; it is not the wrapper contract.
3. Build the reviewed
   [324-function semantic contract](../../../examples/ta_lib/ta_lib_api.pyi).
   That contract contains 322 indicators plus initialization and shutdown. For
   every indicator it projects the two scalar output pointers into
   `(status, begin, count)` and keeps the native output arrays visible.

The separate pytest command then audits the inventory and exercises the built
extension.

## How the numerical comparison works

The exhaustive check is a **differential wrapper test**. It does not contain
322 handwritten sets of expected numbers. Instead, TA-Lib's own regression
runner creates a request once and sends that same request through two paths:

| Path | What it calls | Purpose |
| --- | --- | --- |
| Direct reference | TA-Lib's reference server calls the pinned C API directly, without PRIK | Produce the expected native result |
| PRIK wrapper | The Python adapter calls the PRIK-generated module, which calls the same pinned C API | Produce the result a Python user receives |

Use the moving-average call above as the mental model. The reference path calls
native `TA_SMA` directly with the price data, period, and output buffer. The
wrapper path calls `talib.TA_SMA` with equivalent NumPy values. If the direct
path returns `begin=2`, `count=8`, and the eight displayed averages, the
wrapper path must return the same metadata and write the same eight values.
The runner automates that pattern for the entire indicator surface.

For each indicator, the sequence is:

1. TA-Lib's runner selects its built-in price and volume data, input range,
   and option values. No market data is downloaded.
2. The runner serializes those inputs into one request. It sends the identical
   request first to the direct reference server and then to
   [`reference_adapter.py`](../../../examples/ta_lib/reference_adapter.py).
3. The direct server calls TA-Lib natively and returns the native status,
   `outBegIdx`, `outNBElement`, and output arrays.
4. The adapter reads the checked-in semantic `.pyi` as its call schema,
   converts the same inputs to the required NumPy dtypes, allocates the
   caller-owned output arrays, and invokes the generated PRIK function.
5. The runner compares the two statuses, beginning indexes, result counts, and
   every output value using TA-Lib's comparison tolerances. This comparison is
   designed to expose a wrong symbol, argument order, scalar conversion, array
   dtype, output projection, or written value.
6. The adapter records every indicator that actually crossed the generated
   wrapper. After the run, pytest requires that record to equal the exact set
   of 322 reviewed indicator names. A silently skipped function fails even if
   every function that did run produced correct values.

Both paths ultimately execute TA-Lib v0.7.1. The comparison therefore proves
that the PRIK boundary preserves the pinned library's native behavior; it is
not an independent proof that TA-Lib's financial formulas are mathematically
correct.

## What the complete pytest suite checks

The suite has four complementary layers:

- **Public-surface accounting:** the 522 public header functions must equal the
  324 reviewed exports plus the 198 named exclusions. The edited contract and
  built Python module must expose exactly the same 324 names.
- **Entrypoint reachability:** every one of the 322 indicator functions is
  called through the generated Python module with a deliberately invalid start
  index and must return TA-Lib's expected error status. This catches a missing
  or uncallable binding independently of numerical comparison.
- **Numerical parity:** TA-Lib's runner covers all 161 double-input functions
  and all 161 `TA_S_*` float-input functions through the two-path comparison
  above. The suite also repeats `TA_MAVP` and `TA_S_MAVP` with an explicit
  period-series request as a focused, readable check of that two-array input.
- **Lifecycle and readable examples:** initialization and shutdown must both
  succeed. Focused tests for moving averages, Bollinger Bands, and integer
  index outputs make the expected Python calling pattern easy to inspect.

TA-Lib's runner performs abstraction-protocol self-checks before the indicator
comparisons. That API is outside this example, so those setup requests are
forwarded directly to the native reference server. They are not counted as
PRIK calls and cannot satisfy the required 322-name coverage set.

## CI targets

The Real Libraries Portability workflow repeats the build, surface audit, and
numerical comparison with Python 3.12 on Linux x86-64, Linux Arm64, macOS
Intel, and macOS Arm64. TA-Lib uses GCC 13 on Linux and Apple Clang on macOS.
The compiler-specific native cache, generated inventory, semantic lowering,
extension build, and runtime comparison are all target-specific and exercised
by each job.

## Support boundary

The excluded abstraction API is useful to programs that discover indicators
and parameter schemas dynamically. It requires aggregate records, callbacks,
multi-level pointers, and library-owned pointer results, which are outside the
current direct-C subset. The maintained example therefore uses TA-Lib's
ordinary typed batch functions, which are the numerical API Python callers
need.

See the copyable [example README](../../../examples/ta_lib/README.md) for cache,
toolchain, and troubleshooting details.
