---
title: C Symbols, Headers, and Dependencies
description: Present C overloads and build extensions from headers and native libraries
audience: users
prerequisites: C functions and semantic contracts
related: index.md, ../../reference/cli-commands.md, ../../reference/python-api.md, ../../examples/c/libm-wrapper.md, ../../language-support/c-support.md
status: maintained
publication: reviewed
---

# C Symbols, Headers, and Dependencies

## Present several C symbols as one Python name

An authored contract can dispatch supported dtype and rank variants behind one
Python name. Mark the concrete candidates `@private`, then name them with
`@overload(...)`.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C overload workflow">
<button class="prik-example-tab" id="c-overload-source-tab" type="button" role="tab" aria-controls="c-overload-source" aria-selected="true">C source</button>
<button class="prik-example-tab" id="c-overload-contract-tab" type="button" role="tab" aria-controls="c-overload-contract" aria-selected="false" tabindex="-1">Contract and build</button>
<button class="prik-example-tab" id="c-overload-python-tab" type="button" role="tab" aria-controls="c-overload-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-overload-source" role="tabpanel" aria-labelledby="c-overload-source-tab" tabindex="0" markdown="1">

Create `overloads.c`:

```c
int scale_integer(int value) { return value * 2; }

double scale_real(double value) { return value * 2.0; }
```

</div>

<div class="prik-example-panel" id="c-overload-contract" role="tabpanel" aria-labelledby="c-overload-contract-tab" tabindex="0" markdown="1">

Create `overloads.pyi`:

```python
from prik.contracts import Float64, Int32, overload, private

@private
def scale_integer(value: Int32) -> Int32: ...

@private
def scale_real(value: Float64) -> Float64: ...

@overload("scale_integer")
def scale(value: Int32) -> Int32: ...

@overload("scale_real")
def scale(value: Float64) -> Float64: ...
```

```bash
python3 -m prik --language c overloads.pyi \
  --native-c-sources overloads.c \
  --compiler cc \
  --out overloads \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-overload-python" role="tabpanel" aria-labelledby="c-overload-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import overloads

print(overloads.scale(np.int32(21)))
print(overloads.scale(np.float64(1.5)))
print([name for name in dir(overloads) if not name.startswith("_")])
```

```text
42
3.0
['scale']
```

</div>
</div>

Candidates must remain distinguishable by their supported dtype and rank.

## Qualifiers and compiler attributes

Use C qualifiers as constraints when authoring a contract: `const T *` must
not be presented as writable NumPy storage. `const` and `restrict` do not add
a separate Python type or calling convention.

Common non-ABI attributes such as `deprecated` and `warn_unused_result` do not
change a wrapper. An attribute that may change the ABI, symbol identity, or
layout stops the build instead of being ignored.

Compiler-preprocessed system headers may contain unavailable extended floating
types in private declarations. PRIK can use those declarations as parsing
context without adding wrapper support for the extended type. Prototype
parameters may omit names; actual K&R definitions remain unsupported.

## Symbols declared by binding headers

A header included by the generated binding may already declare the same name
for a different API. Select that symbol for an isolated collision forwarder:

```bash
python3 -m prik --language c vendor.pyi \
  --native-library vendor \
  --collision-adapter evaluate \
  --out vendor_api --out-dir build
```

The build writes a separate forwarding translation unit that includes no
Python header. Its signature uses the completed exact native C types:

```c
long long evaluate(double x);

long long prik_collision_adapter_evaluate(double x) {
    return (evaluate)(x);
}
```

The adapter targets a real function symbol; PRIK does not expose macros. The
forwarder has hidden visibility and works with or without `--lto`. Use
`--collision-adapter-all` to adapt every eligible C source function.

This solves a declaration collision inside the generated binding. It does not
choose between two linked libraries that export the same external symbol.
Normal linker and loader resolution must already select the intended library.

A source-free `.pyi` contract must preserve every exact native scalar identity
needed by the declaration. A target-generated contract does this
automatically. See [CLI Commands](../../reference/cli-commands.md#wrapper-builds)
for selection, validation, and LTO options.

## Build and inspect APIs

Use `build_c_extension()` for source builds or `build_pyi_extension()` for
authored contracts from Python. See the [Python
API](../../reference/python-api.md) for those calls and [CLI
Commands](../../reference/cli-commands.md) for build, generation, Makefile,
and inspection options.

### Native dependencies

Pass public C source files as positional inputs. Add implementation-only C
files with `--native-c-sources`, compiler flags with
`--native-c-compile-flags`, existing objects with `--native-objects`, and
libraries with `--native-library` and `--native-library-dir`.

For headers and conditional source, pass the native project's preprocessing
configuration with `-I`, `-D`, `--std`, and, when available,
`--compile-commands build/compile_commands.json`.

To wrap a reviewed subset of a broad or system header, list the public
functions in a file and generate their contract:

```bash
python3 -m prik generate --pyi --language c api_probe.h \
  --include-exposure roots-only \
  --export-symbols reviewed_functions.txt \
  --out contracts/api.pyi
```

The export file selects the semantic API, not linker exports. Selected
functions still need native link inputs and a signature supported by the C
wrapper. See [C include
exposure](../../reference/cli-commands.md#c-include-exposure) for the file
format and validation rules.

The Python API accepts already-resolved names:

```python
build = build_c_extension(
    "api_probe.c",
    export_symbols=("evaluate", "normalize"),
    native_libraries=("vendor",),
)
```

### Inspect a broader C API

The parser and contract generator accept more syntax than the supported
wrapper surface. Use them to inspect declarations:

```bash
python3 -m prik parse --language c include/library.h --json
python3 -m prik semantics --language c include/library.h
python3 -m prik generate --pyi --language c include/library.h --out contracts/library.pyi
```

Pass the native preprocessing configuration when the header needs it:

```bash
python3 -m prik parse --language c include/library.h \
  -I include \
  -D LIBRARY_ENABLE_FAST=1 \
  --std c11 \
  --compile-commands build/compile_commands.json
```

Only declarations in the wrapped translation unit become a source build's
public API; headers provide declarations and preprocessing context.

## Next

See [C Support](../../language-support/c-support.md) for the complete supported
surface, or continue with the [libm](../../examples/c/libm-wrapper.md) and
[TA-Lib](../../examples/c/ta-lib-wrapper.md) examples.
