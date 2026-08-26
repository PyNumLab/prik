---
title: Build and Validate the C TA-Lib Library with PRIK
audience: users, advanced users
prerequisites: C support, semantic .pyi contracts
related: ../../language-support/c-support.md, ../../reference/cli-commands.md, libm-wrapper.md
status: maintained
publication: reviewed
---

# Build and Validate the C TA-Lib Library with PRIK

TA-Lib is a **C library** for technical-analysis calculations. You give it aligned
arrays of historical prices or volume—one array element per time step—and it
calculates derived series such as moving averages, momentum, volatility,
regression values, price transforms, and candlestick-pattern signals. It does
not download market data, choose a trading strategy, or place trades.

This maintained example wraps TA-Lib v0.7.1's complete numerical indicator
API with NumPy arrays: all 161 double-input and all 161 float-input functions.

The checked-in contract contains those 322 numerical functions plus
initialization and shutdown. The 198 excluded public functions are 161
lookbacks, six global settings, and 31 optional abstraction or metadata
functions. The returned beginning and count replace the need for public
lookbacks; calculations use TA-Lib's default global settings.

## C integration boundary

PRIK does not wrap TA-Lib by reading or modifying its implementation `.c`
files. This example has two native inputs:

| Input | Role |
| --- | --- |
| public C header `ta_libc.h` | Supplies the declarations used to audit TA-Lib's complete public function inventory |
| compiled `libta-lib` library | Supplies the native function implementations that the generated Python extension calls |

The checked-in semantic `.pyi` is the reviewed contract between those C
declarations and Python. The example's native helper downloads and compiles
the pinned TA-Lib release only to create a reproducible installed header and
library for the test environment. TA-Lib's C implementation files are never
passed to PRIK as wrapper inputs.

## The shape of a TA-Lib indicator

The 322 numerical functions are not 322 unrelated APIs. They combine the same
small set of parts:

```text
TA_<indicator>(
    start index, end index,
    one or more input arrays,
    zero or more scalar options,
    output beginning, output count,
    one or more caller-owned output arrays,
) -> status
```

`startIdx` and `endIdx` select an inclusive range of the input arrays. Options
control the calculation—for example, the moving-average period. TA-Lib returns
a status code and writes the calculated values into storage supplied by the
caller.

Every successful indicator also writes two pieces of alignment metadata:

- `outBegIdx` is the input index represented by the first calculated value;
- `outNBElement` is the number of values written into each output array.

TA-Lib writes the first result at `output[0]`, not at `output[outBegIdx]`.
Therefore `output[:outNBElement]` corresponds to the input range
`outBegIdx:outBegIdx + outNBElement`. Early input values may have no result
because an indicator needs earlier observations. A three-period moving average,
for example, cannot produce its first value until input index 2.

### Recurring parameters and results

| Contract name | Meaning in the indicator API |
| --- | --- |
| `startIdx`, `endIdx` | Inclusive input range to calculate |
| `inReal`, `inReal0`, `inReal1` | One or more generic numerical series |
| `inOpen`, `inHigh`, `inLow`, `inClose`, `inVolume` | Aligned market-data series required by price and volume indicators |
| `inPeriods` | A period value for each input element, used by variable-period moving averages |
| `optIn...` | Explicit scalar calculation options such as a period, deviation, or moving-average kind |
| `outReal...` | Caller-owned floating-point result arrays |
| `outInteger...` | Caller-owned integer results, such as indexes or candlestick signals |
| `outBegIdx`, `outNBElement` | Native scalar outputs projected by this contract into `begin` and `count` |
| native return value | TA-Lib status: zero on success and a nonzero error code otherwise |

“Optional input” is TA-Lib's C naming convention for a parameter with a
documented default. This direct wrapper still makes every selected `optIn...`
value explicit in the Python call.

Different indicators vary only in how many of those pieces they use:

| Example | Inputs | Options | Output arrays |
| --- | --- | --- | --- |
| `TA_SMA` | one value series | period | one floating-point average |
| `TA_ADD` | two value series | none | one floating-point series |
| `TA_AVGPRICE` | open, high, low, close | none | one floating-point price series |
| `TA_BBANDS` | one value series | period, two deviations, average kind | upper, middle, and lower floating-point bands |
| `TA_STOCH` | high, low, close | five period/kind options | two floating-point oscillator series |
| `TA_MINMAXINDEX` | one value series | period | two integer index arrays |
| `TA_CDLENGULFING` | open, high, low, close | none | one integer pattern-signal array |
| `TA_MAVP` | value and per-element period series | minimum period, maximum period, average kind | one floating-point average |

For every `TA_NAME` function accepting `Float64[:]` inputs, this release also
provides a `TA_S_NAME` variant accepting `Float32[:]` inputs. The reviewed
contract keeps floating-point output arrays as `Float64[:]` for both variants.
The two lifecycle functions, `TA_Initialize()` and `TA_Shutdown()`, sit outside
this indicator pattern.

## How the checked-in `.pyi` describes that shape

The semantic `.pyi` is the reviewed source of truth for the wrapper. Its
function signature describes what Python supplies and receives; its
`@native_call` decorator describes the complete native argument order.

This is the complete `TA_SMA` declaration from the fixture:

<!-- prik-doc-source: examples/c/ta_lib/ta_lib_api.pyi::TA_SMA -->
```python
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_SMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
```

Read the declaration in two layers:

- `startIdx`, `endIdx`, `inReal`, `optInTimePeriod`, and `outReal` are the five
  Python-visible arguments. `Float64[:]` means a one-dimensional,
  C-contiguous NumPy array using the target's compatible double storage.
- Python receives `(status, begin, count)`. The plain first `Int` is the native
  function result. The two named `Returns[...]` entries expose native output
  parameters as Python results.
- `Arg(0)` through `Arg(3)` place the first four visible arguments into native
  positions 0 through 3.
- `Return("outBegIdx", 1)` and `Return("outNBElement", 2)` ask PRIK to create
  two hidden writable integer slots, pass their addresses to TA-Lib, then put
  their values into Python result positions 1 and 2.
- `Arg(4)` places the caller's visible output array after those two hidden
  native pointers, matching TA-Lib's real argument order.

Conceptually, the native and Python views are:

```text
native: status = TA_SMA(start, end, input, period, &begin, &count, output)
Python: status, begin, count = talib.TA_SMA(start, end, input, period, output)
```

The output array remains visible because TA-Lib writes potentially many values
into caller-owned storage. Only the two scalar bookkeeping outputs are hidden
and returned. The same pattern is repeated across the other 321 indicators,
with additional input, option, and output arrays as required.

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
| Native language | C |
| PRIK declaration input | public `ta_libc.h` through `ta_lib_probe.h`, plus the reviewed semantic `.pyi` |
| Link input | compiled `libta-lib` |
| Native build | CMake with TA-Lib's regression tools enabled |
| Python | 3.12 in Real Libraries Portability CI |

Install Git, CMake, a C compiler, Python development headers, NumPy, and
pytest. The build helper clones the pinned TA-Lib tag into the user cache,
verifies the exact commit, and installs it into a target-and-compiler-specific
cache directory. No TA-Lib source is vendored in PRIK.

## Build and test

Run from the repository root:

```bash
source examples/c/ta_lib/build_all.sh
python3 -m pytest -q examples/c/ta_lib/tests
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
   [324-function semantic contract](../../../../examples/c/ta_lib/ta_lib_api.pyi).
   That contract contains 322 indicators plus initialization and shutdown. For
   every indicator it projects the two scalar output pointers into
   `(status, begin, count)` and keeps the native output arrays visible.

The separate pytest command then audits the inventory and exercises the built
extension.

## Where the expected results come from

TA-Lib supplies a program named `ta_regtest` with two relevant kinds of
validation:

- its native C regression mode checks the indicator implementation using
  TA-Lib's own C test cases;
- its code-generation mode checks another implementation or language boundary
  against a direct native TA-Lib reference.

This example deliberately reuses the second mode because its question is
whether PRIK preserves the C API correctly. The test invokes
`ta_regtest --codegen-only`, so it does **not** rerun TA-Lib's separate native C
regression suite. It asks TA-Lib's runner to validate the generated PRIK
boundary instead.

There is no file in PRIK containing 322 arrays of expected numbers. The
expected values are calculated during the test:

```text
                 TA-Lib metadata and built-in input data
                                  |
                         one identical request
                    +-------------+-------------+
                    |                           |
                    v                           v
          direct native reference        PRIK test adapter
             `ta_ref_serve`                     |
                    |                    checked-in `.pyi`
                    |                           |
                    |                       NumPy values
                    |                           |
                    |                  PRIK-generated module
                    |                           |
                    +----------+   +------------+
                               |   |
                               v   v
                 compare status, begin, count,
                       and every output value
```

The build creates two routes from the same pinned TA-Lib v0.7.1 source. The
reference server is linked directly with the native library and does not use
PRIK. The generated Python extension links the shared native library and can be
reached only through the semantic `.pyi` and PRIK's generated boundary. The
reference route produces the expected result; the wrapper route produces the
actual result being tested.

That arrangement is a **differential wrapper test**. It does not require 322
handwritten sets of expected numbers. TA-Lib's runner creates a request once
and sends that same request through both paths:

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
   [`reference_adapter.py`](../../../../examples/c/ta_lib/reference_adapter.py).
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

Both paths ultimately execute the same TA-Lib v0.7.1 indicator logic. If
TA-Lib itself calculated an indicator incorrectly in both paths, this
comparison would not detect that shared error. What it establishes is that
crossing the Python/NumPy/PRIK boundary does not change the result produced by
the pinned native library. TA-Lib's own C regression suite is the upstream
evidence for the indicator implementation; the PRIK suite is evidence for the
wrapper.

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

## Tested platforms

The Real Libraries Portability workflow builds and runs the complete surface
audit and 322-indicator numerical comparison with Python 3.12 on:

| Operating system | Architectures | C compiler |
| --- | --- | --- |
| Linux | x86-64, ARM64 | GCC 13 |
| macOS | Intel, ARM64 | Apple Clang |

Each lane exercises the compiler-specific native cache, generated inventory,
semantic lowering, extension build, and runtime comparison. TA-Lib therefore
covers both GCC and Clang families across the matrix, but unlike libm it does
not run both compiler families on every target. Native Windows/MSVC remains
outside PRIK's current POSIX C build lane. See the [complete portability
matrix](../index.md#tested-platforms).

## Support boundary

The excluded abstraction API is useful to programs that discover indicators
and parameter schemas dynamically. It requires aggregate records, callbacks,
multi-level pointers, and library-owned pointer results, which are outside the
current direct-C subset. The maintained example therefore uses TA-Lib's
ordinary typed batch functions, which are the numerical API Python callers
need.

See the copyable [example README](../../../../examples/c/ta_lib/README.md) for cache,
toolchain, and troubleshooting details.
