# Wrap the C TA-Lib Library with PRIK

TA-Lib is a **C library** that calculates technical-analysis series from caller-supplied price and
volume arrays. It provides indicators such as moving averages, momentum,
volatility, regressions, price transforms, and candlestick-pattern signals; it
does not fetch market data or execute trades.

This maintained example wraps the complete numerical indicator API from
TA-Lib v0.7.1. It accounts for all 522 functions in the public `ta_libc.h`
umbrella header and builds a checked-in 324-function contract:

- 161 double-input indicator functions;
- 161 float-input variants;
- initialization and shutdown for library lifecycle.

The 198 explicit exclusions are 161 lookbacks, six global settings, and 31
optional abstraction or metadata functions. Lookbacks are unnecessary because
the wrapper returns each calculation's beginning and count. The example uses
TA-Lib's default global settings.

PRIK uses TA-Lib's public C header declarations and links the compiled
`libta-lib` library. TA-Lib's implementation `.c` files are not wrapper inputs.
The native build helper compiles the pinned dependency only so the example has
a reproducible header, library, and regression runner to consume.

## API and contract model

Every wrapped indicator follows the same broad native pattern:

```text
status = TA_NAME(start, end, inputs..., options...,
                 &output_begin, &output_count, output_arrays...)
```

Input arrays hold aligned historical series. `start` and `end` select an
inclusive range. Options are scalar calculation settings. TA-Lib writes into
caller-owned output arrays; `output_begin` identifies the input index for the
first result and `output_count` says how many values were written from
`output[0]`.

The checked-in [`ta_lib_api.pyi`](ta_lib_api.pyi) turns the two scalar output
pointers into Python results while keeping the result arrays visible:

```text
status, begin, count = module.TA_NAME(
    start, end, inputs..., options..., output_arrays...
)
```

In the fixture, the Python function signature defines the NumPy-facing call.
Its ordered `@native_call(...)` mapping inserts hidden writable storage for
`outBegIdx` and `outNBElement` at their original C positions. For example,
`TA_SMA` exposes five Python arguments while this mapping reconstructs all
seven native arguments:

```python
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_SMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
```

`Arg(i)` selects visible Python argument `i`. Each `Return(name, position)`
creates a hidden native output pointer and places the written value in that
Python result position. The first returned `Int` is TA-Lib's native status.
The [user guide](../../../docs/user/examples/c/ta-lib-wrapper.md#the-shape-of-a-ta-lib-indicator)
explains the recurring input, option, and output families with examples.

## Requirements

Install Git, CMake, a C compiler, Python development headers, NumPy, and
pytest. On Ubuntu:

```console
sudo apt-get update
sudo apt-get install --yes build-essential cmake git python3-dev
python3 -m pip install "numpy>=2" pytest
```

The native builder clones tag `v0.7.1`, verifies commit
`2247d599bddf37ed37e3a709371517e46efc66f6`, and caches the installation by
target and compiler. No TA-Lib implementation source is copied into PRIK.

Run the remaining commands from the repository root.

## Quick start

```bash
source examples/c/ta_lib/build_all.sh
python3 -m pytest -q examples/c/ta_lib/tests
```

Use `source` so `PYTHONPATH` and the runtime library search path remain
available to pytest.

Set `PRIK_TALIB_CC` to choose the C compiler. Set
`PRIK_TALIB_CACHE_DIR` to choose the native cache, or
`PRIK_TALIB_PREFIX` to use an existing complete TA-Lib v0.7.1 installation.
`PRIK_TALIB_JOBS` bounds both the native and wrapper builds.

An external `PRIK_TALIB_PREFIX` must be accompanied by
`PRIK_TALIB_REGTEST` and `PRIK_TALIB_REFERENCE_SERVER`, pointing to the
matching v0.7.1 regression runner and reference-protocol server. The default
pinned build prepares all three automatically.

## Calculate an indicator

TA-Lib's C API writes into arrays supplied by the caller. PRIK keeps that
ownership explicit and projects the two scalar output pointers into returned
metadata:

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

`begin` identifies the input index for the first result. `count` says how many
values TA-Lib wrote from the start of `output`. Allocate one output array per
native output for indicators such as `TA_BBANDS`.

## Build path

`build_all.sh` sources [`build_prik.sh`](build_prik.sh), performs the native and
wrapper builds, and makes the generated module importable. `build_prik.sh`
performs three checked operations:

1. [`native_build.py`](native_build.py) fetches, verifies, builds, and caches
   the pinned native release and its reference-test tools.
2. PRIK generates a complete public-header inventory for the pinned compiler
   target. The inventory is for the surface audit; it is not used as the
   wrapper contract.
3. PRIK builds the reviewed [`ta_lib_api.pyi`](ta_lib_api.pyi), where all 322
   indicator signatures hide `outBegIdx` and `outNBElement` and return
   `(status, begin, count)`.

The pytest command shown in Quick start performs the runtime and surface
audits. Keeping the build and test commands separate makes it possible to
inspect or import the generated module before running the complete audit.

There is no Fortran bridge and no ABI-conversion adapter. The opt-in collision
forwarder isolates selected names from declarations in Python's own headers;
it does not convert the TA-Lib ABI.

## How the tests know a result is correct

TA-Lib ships `ta_regtest` for native regression and cross-language validation.
This example uses its `--codegen-only` mode: it checks PRIK's generated
boundary against a direct native reference, without rerunning TA-Lib's separate
C regression suite.

The exhaustive test is not 322 handwritten Python tests and PRIK stores no
table of expected indicator values. TA-Lib's runner enumerates its 161
indicator families and exercises both the double-input function and its
`TA_S_*` float-input variant. It calculates each expected result live through
`ta_ref_serve`, which calls the pinned native library directly.

For every request, the runner uses the same built-in price data, input range,
and options in two paths:

1. `ta_ref_serve` calls the pinned TA-Lib C API directly, without PRIK. Its
   live response is the expected native result.
2. [`reference_adapter.py`](reference_adapter.py) converts the same request to
   NumPy values using the checked-in `.pyi`, calls the PRIK-generated module,
   and returns the result seen through the wrapper.
3. TA-Lib's runner compares the native status, beginning, count, and every
   output value from those two responses.

This is differential wrapper testing: both routes ultimately call TA-Lib
v0.7.1, but only one crosses the PRIK boundary. It verifies that PRIK selected
the right symbol and preserved argument order, dtypes, array writes, projected
metadata, and results. Because both routes execute the same indicator logic,
it does not independently prove TA-Lib's formulas; TA-Lib's native regression
tests own that separate question.

[`api_inventory.py`](api_inventory.py) makes the audit fail closed. The pinned
header must contain exactly 522 public `TA_*` functions. Those names must split
into the 324 reviewed exports and 198 explicit exclusions, and the contract and
built module must both expose the same 324 exports. During numerical testing,
the adapter records every call that reached the generated wrapper; pytest
requires that record to contain exactly all 322 indicators. A skipped function
therefore cannot disappear inside a successful aggregate run.

The runner itself reaches all 322 numerical exports, including `TA_MAVP` and
`TA_S_MAVP`. The suite repeats those two functions with a small explicit
period-series request as an additional readable two-input check. Separate
focused tests demonstrate moving averages, three-output Bollinger Bands, and
integer output arrays, while the session fixture checks `TA_Initialize` and
`TA_Shutdown`.

The runner starts with abstraction-protocol self-checks. The adapter forwards
those setup requests to the direct reference server because the abstraction
API is explicitly excluded. They do not cross the generated wrapper and do
not count toward the required 322-indicator coverage set.

The detailed user guide includes the complete
[test flow and CI target explanation](../../../docs/user/examples/c/ta-lib-wrapper.md#where-the-expected-results-come-from).

## Why the abstraction API is excluded

TA-Lib's abstraction API discovers functions and schemas dynamically through
library-owned records and handles. Its public signatures include struct
pointers, pointer-to-pointer outputs, a callback, and pointer results. Those
forms are outside PRIK's direct-C subset.

The typed batch API is the calculation surface: every official indicator has a
double-input and float-input entrypoint. Covering all 322 makes this a complete
numerical TA-Lib example, not a cherry-picked indicator demo.

## Troubleshooting

- Confirm that `git`, `cmake`, and the compiler selected by `PRIK_TALIB_CC` are
  on `PATH`.
- If a cached tag fails commit verification, remove only the source directory
  named in the diagnostic and retry.
- Use `source examples/c/ta_lib/build_all.sh` so the extension and native shared
  library remain importable.
- Set `PRIK_TALIB_PREFIX` only to a TA-Lib v0.7.1 installation containing
  `include/ta-lib/ta_libc.h` and `lib/libta-lib.*`, and supply the two matching
  reference-tool paths described under Quick start.

The full user guide is
[Build and Validate TA-Lib with PRIK](../../../docs/user/examples/c/ta-lib-wrapper.md).
