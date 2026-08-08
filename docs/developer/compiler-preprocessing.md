---
title: Compiler Preprocessing Reference
audience: developers, contributors
prerequisites: repository structure, native project compiler flags
related: source-map.md, c-parser-reference.md, fortran-parser-reference.md, ../user/examples/recipes/compiler-preprocessing.md
status: maintained
publication: draft
---

# Compiler-Backed Preprocessing Reference

`prik/pipeline/preprocessing.py` owns compiler-backed preprocessing for the wrapper
pipeline. The parsers consume one expanded source stream; they do not evaluate
CPP branches or emulate macro expansion.

## Pipeline

```text
source path
  -> build preprocessing invocation
  -> run compiler adapter
  -> collect expanded stdout, linemarkers, macros, include files, diagnostics
  -> expand remaining native Fortran INCLUDE statements
  -> parse expanded source once
```

The compiler is authoritative for `#include`, `#define`, `#if`/`#ifdef`,
predefined macros, `-D`, `-U`, include paths, target flags, and sysroot
behavior. GNU Fortran does not preprocess files referenced by native Fortran
`include "file.inc"`, so prik expands those textually after compiler CPP
output.

## Main Models

- `PreprocessingConfig`: user/compiler configuration, adapter selection,
  include exposure controls, and passthrough compiler arguments.
- `Invocation`: exact argv/cwd sent to the compiler adapter.
- `PreprocessResult`: expanded source plus recipe, included files, source
  mappings, macro metadata, and preprocessing diagnostics.
- `IncludedFile`: include graph edge with mechanism, system/project
  classification, and public/private exposure.
- `SourceMapping`: generated line to original file/line and include stack.
- `MacroDefinition`: active macro metadata when the adapter output exposes it.

## Adapters

Built-in adapters cover GCC-compatible C/Clang (`-E -x c`), GNU Fortran
(`-E -cpp`), compile database ingestion, and custom command templates for other
compiler families. A custom template must write expanded source to stdout:

```bash
python -m prik parse include/api.h --language c --preprocess compiler \
  --preprocessor-adapter command-template \
  --preprocess-template 'vendor-cc --preprocess {include_dirs} {defines} {source}'
```

## Diagnostics

Preprocessing errors use explicit categories and are printed by the CLI without
a traceback unless `--debug` is used:

- `PREPROCESSOR_NOT_FOUND`
- `PREPROCESSOR_FAILED`
- `INVALID_COMPILER_ARGUMENTS`
- `UNSUPPORTED_COMPILER_CAPABILITY`
- `PROVENANCE_UNAVAILABLE`
- `INCLUDE_NOT_FOUND`
- `INCLUDE_CYCLE`

## Include Exposure

Root files and reachable project includes are public by default; system headers
are private. Use `--include-exposure roots-only`, `--public-include`, and
`--private-include` to control wrapper export. Private declarations remain
available to resolve public signatures, and private C handle types can be
emitted as opaque classes.
