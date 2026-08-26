---
title: CLI Commands Reference
audience: users
prerequisites: installation
related: python-api.md, ../language-support/c-support.md, ../guide/building-shared-library.md
status: maintained
publication: reviewed
---

# CLI Commands Reference

With no subcommand, PRIK builds a wrapper. Four subcommands expose the earlier
stages without building one.

```bash
python3 -m prik INPUT [INPUT ...] [BUILD OPTIONS]
python3 -m prik {parse,semantics,generate,probe} [OPTIONS] ...
```

| Command | Purpose |
| --- | --- |
| no subcommand | Builds one importable extension from Fortran source, a supported direct C source, or a semantic `.pyi` contract. |
| `parse` | Prints parser facts and diagnostics. |
| `semantics` | Prints a human-readable semantic-IR report; `--json` selects the complete JSON record. |
| `generate` | Writes `.pyi` contracts, wrapper sources, or a Makefile without compiling. |
| `probe` | Prints compiler-target datatype and ABI facts. |

## Getting help

```bash
prik --version          # installed distribution version
python3 -m prik --help        # common inputs, build controls, and commands
python3 -m prik --help-build  # every default-build option
```

`--help` is a curated overview; `--help-build` is the exhaustive build surface.
Each subcommand has its own help — `parse --help`, `semantics --help`,
`generate --help`, `probe --help` — describing that stage's role for shared
flags such as `--compiler` and `-I`.

`prik --version` and `python3 -m prik --version` print the same value as
`prik.__version__`.

When `rich-argparse` is installed, PRIK uses its colored help formatter
automatically. Install it with `python3 -m pip install 'prik[pretty]'`, or from
an editable checkout with `python3 -m pip install -e '.[pretty]'`. Plain
`argparse` help is the deterministic fallback; `--no-color` or `NO_COLOR`
selects it explicitly.

## Input selection

The default build accepts either one or more Fortran or supported C source
`INPUT` values, or exactly one semantic `.pyi` entry contract — never both. With
`--build-manifest PATH`, omit positional input entirely.

| Option | Purpose |
| --- | --- |
| `paths` | Source files, `.pyi` files, or directories. Omit only with `--build-manifest`. |
| `--version` | Prints the installed PRIK version and exits. |
| `--language {fortran,c}` | Selects the source or source-free contract language explicitly. C source and C-native contracts require `c`. |
| `--build-manifest PATH` | Replays a saved `prik-build.json`. It does not generate one. |
| `--jobs N` | Limits concurrent compiler processes. The default uses available CPUs. |

Compiled wrapper builds support Fortran and the documented direct-C subset —
scalars, one-level primitive pointers, arrays, rank-zero strings, hidden
outputs, and status projection. C paths require `--language c`; the parser
accepts more C forms than that runtime subset, and those fail before wrapper
planning. [C Support](../language-support/c-support.md#what-is-supported)
records the exact boundary.

Directories are expanded recursively in deterministic path order. Fortran
source files can usually be inferred from their suffix;
[Fortran Support](../language-support/fortran-support.md#source-forms) lists the
accepted ones. C files, directories, and unknown suffixes require
`--language c`.

## Wrapper builds

A positional Fortran or C source is both a semantic input and a native
implementation source. A `.pyi` is only the semantic contract, so it needs at
least one explicit native input: `--native-fortran-sources`, `--native-c-sources`, `--native-objects`,
`--native-library`, or `--native-link-item`.

| Option | Purpose |
| --- | --- |
| `--out NAME` | Python module name, `PyInit_<name>` symbol, and stable `NAME.so` alias. Accepts `NAME` or `NAME.so`, and requires a value. |
| `--out-dir DIR` | Where generated artifacts and the ABI-suffixed extension are built. Default `./__prik__`. |
| `--compiler COMPILER` | The input-language compiler used for preprocessing, datatype measurement, native compilation, and linking. Defaults to `gfortran` for Fortran and `cc` for C. |
| `-I DIR`, `--include-dir DIR` | Build-wide include directory. Repeat to preserve search order. |
| `--strict-wrapper-names` | Rejects Python names that would need escaping or a collision suffix. |
| `--assume-intent-in-scalars` | Treats a primitive or non-descriptor character scalar dummy that declares no `intent` as `intent(in)`, so its value is not returned. A declared `intent` always wins; arrays, derived-type objects, and descriptor character scalars are unaffected. Also accepted by `generate --pyi`, where it removes the same results from the generated contract, and by `semantics`. |
| `--no-compile-input-sources` | Treats positional sources as semantic inputs only. Requires an explicit native input. |
| `--native-fortran-sources PATH ...` | Compiles extra native sources without exposing them as public API. |
| `--native-c-sources PATH ...` | Compiles extra C sources without exposing them as public API. |
| `--native-compile-flags FLAG ...` | Flags for native implementation compilation. |
| `--native-c-compile-flags FLAG ...` | C implementation compiler flags. |
| `--native-objects PATH ...` | Links object files, static archives, or shared libraries. |
| `--native-library NAME ...` | Links system libraries by name — `--native-library openblas` passes `-lopenblas`. |
| `--native-link-item KIND:VALUE ...` | Ordered link items. `KIND` is `object`, `archive`, `shared-library`, `library`, or `arg`. |
| `--native-library-dir DIR ...` | Library search directories and runtime paths. |
| `--lto` | Enables link-time optimization for Fortran and C builds by adding `-flto` to generated and native compilation and to the extension link. |
| `--collision-adapter NAME ...` | Calls native symbol `NAME` through a forwarder defined in a separate translation unit, so the binding never declares an identifier its own headers already declare. |
| `--collision-adapter-all` | Applies `--collision-adapter` to every direct C symbol in the build. |
| `--positional-only` | For Fortran and C, exposes every wrapper whose arguments are all required as positional-only, renaming them `arg0`..`argN`. |
| `--wrapper-compiler-debug` | Uses the compiler debug profile instead of release. |
| `--wrapper-fortran-flags FLAG ...` | Flags for generated Fortran bridge compilation. |
| `--wrapper-c-flags FLAG ...` | Flags for generated binding compilation and extension linking. |

Build rules worth knowing:

- PRIK selects the generated binding compiler from its own profile;
  `--compiler` controls the input-language side.
- `--native-compile-flags` also applies to internal datatype measurement for
  source builds, so target-changing flags such as `-fdefault-integer-8` affect
  both native compilation and the semantic wrapper types.
- Native input options accept multiple values and may be repeated; supplied
  source, artifact, and link-item order is preserved. For values starting with
  `-`, use the equals form: `--native-compile-flags="-O3 -fopenmp"`.
- Source-driven builds may add native sources, objects, and libraries to
  complete the link. These augment the positional sources without becoming
  semantic inputs.
- Manifest replay accepts only `--out`, `--compiler`, `-I`/`--include-dir`,
  `--jobs`, `--json`, `--verbose`, `--no-color`, and `--debug`. The manifest
  owns output directory, input language, preprocessing recipe, wrapper
  behavior, native inputs, and link plan, so other flags are rejected rather
  than silently ignored. Replay validates the recorded semantic-contract graph
  before it generates files or starts a compiler.

- A source-free C `.pyi` contract is C-native only when `--language c` is
  supplied. PRIK does not infer that identity from the contract filename,
  compiler, native source list, or `@native_abi("c")`.

- `--lto` is an optional build optimization for both Fortran and C. It applies
  to native sources, generated bridge and binding compilation, and the final
  extension link. Collision adapters remain correct without it.

- `--positional-only` applies equally to Fortran and C. It removes argument
  names from the Python API of any function whose arguments are all required,
  so a native declaration's parameter names stop being part of the contract.
  Use it when source parameter names should not become public keywords; a
  system header may spell them `__x`, or omit them entirely. A function with an
  optional argument keeps its keywords because skipping one still requires
  naming the rest, and a module containing overload sets is rejected because
  overload dispatch selects a candidate by keyword.

- `--collision-adapter` is for a genuine identifier collision with a header
  included by the generated binding. The adapter unit includes no Python
  header and reconstructs the exact native declaration from completed
  `@native_call` types. Width-normalized `long` and `long long` distinctions do
  not by themselves require an adapter. Only a C-source function is eligible;
  a Fortran `bind(C)` procedure and a generated bridge symbol are not.
  The adapter isolates the binding's declaration; it does not disambiguate two
  linked libraries that export the same symbol.

## Parse and semantics

```bash
python3 -m prik parse INPUT [INPUT ...] [OPTIONS]
python3 -m prik semantics INPUT [INPUT ...] [OPTIONS]
```

| Option | Purpose |
| --- | --- |
| `--show-vars` | Includes module, submodule, program, and block-data variables in human-readable parse reports. |
| `--print-limit N` | Shows at most `N` items per repeated section in human-readable reports. |
| `--json` | Emits the complete JSON record instead of the human-readable report. |

Both commands follow the same rule: **`--json` selects the format and `--out`
selects the destination, and neither changes the other.** With no `--json` the
command prints a human-readable report; with `--json` it prints the complete
record. With no `--out` that goes to standard output; `--out PATH` writes it to
`PATH`, and bare `--out` writes one file beside each input source, using
`.json` for the record and `.txt` for the report.

`semantics` reports each module's functions with their semantic signatures, and
every argument's semantic dtype, rank, ownership, and mutability — the policy
decisions a parse report cannot show. It accepts source inputs only; use a
source file rather than a generated `.pyi` contract.

Target datatype measurement happens automatically inside semantic conversion.
Use `probe` only when you want to inspect those facts yourself.

For C input, select the language on each command:

```bash
python3 -m prik parse path/to/api.h --language c --json
python3 -m prik semantics path/to/api.c --language c
```

Parsing reports source declarations and diagnostics; it does not promise that
the declaration fits the direct C wrapper contract. Read [C
Support](../language-support/c-support.md) before building a C API.

## Generate

`generate` requires exactly one output mode:

```bash
python3 -m prik generate (--pyi | --sources | --makefile) INPUT [INPUT ...] [OPTIONS]
python3 -m prik generate (--sources | --makefile) --build-manifest PATH [OVERRIDES]
```

| Mode | Purpose |
| --- | --- |
| `--pyi` | Writes the editable semantic `.pyi` contract. |
| `--sources` | Writes wrapper sources without compiling. |
| `--makefile` | Writes wrapper sources, the replay manifest when applicable, and `Makefile.prik`. |

```bash
python3 -m prik generate --pyi points.f90 --out contracts
python3 -m prik generate --sources points.f90 --out-dir build
python3 -m prik generate --makefile points.f90 --out-dir build
```

For a C source contract, `--language c` is valid with `--pyi`:

```bash
python3 -m prik generate --pyi --language c path/to/api.c --out contracts
```

`--sources` and `--makefile` still run preprocessing and semantic policy to
produce a valid wrapper plan; they skip object compilation and linking, and
use `--out-dir`. With no `--out`, `generate --pyi` prints every generated
contract. `--pyi` uses `--out` to write its contract package, and there
`--compiler` and `-I` affect only preprocessing and datatype measurement.

In `.pyi` Makefile mode, PRIK writes `<out-dir>/prik-build.json` first, then
generates `<out-dir>/Makefile.prik` from that manifest.

## Probe

`probe` measures one of two reports. Without `--expr` it measures the standard
datatype mapping table; with `--expr` it measures exactly the Fortran integer
expressions you name. `--json` then selects how that measurement is
rendered: the JSON record is complete and the default Markdown table is
converted from it, so both formats always describe the same measurement.

```bash
python3 -m prik probe --language {fortran,c} --compiler COMPILER [OPTIONS]

python3 -m prik probe --language fortran --compiler gfortran-13
python3 -m prik probe --language c --compiler cc --json
python3 -m prik probe --language fortran --compiler gfortran-13 \
    --expr "selected_real_kind(15,307)"
```

| Option | Purpose |
| --- | --- |
| `--language {fortran,c}` | Selects the target probe. |
| `--compiler COMPILER` | The exact native or cross compiler. |
| `--json` | Emits the complete JSON record instead of the Markdown table. |
| `--expr EXPR` | Measures one Fortran integer expression instead of the mapping table. Repeat for more. |
| `--runner ARG` | Adds one cross-target runner command item. Repeat for more. |
| `--cache-dir PATH` | Reusable probe storage. |
| `--refresh` | Ignores reusable results and probes again. |
| `--out PATH` | Writes the selected format instead of printing it. |

Pass each raw compiler flag separately, for example
`--compiler-arg=-fdefault-real-8 --compiler-arg=-fdefault-integer-8`. The
mapping report accepts compiler, compiler arguments, runner, cache, and refresh
options only, because its inventory is fixed and preprocessing cannot change
it; `-I`, `-D`, `-U`, and `--std` apply to `--expr` measurements, which are
compiled from generated source.

## Compiler preprocessing

These options control preprocessing before parsing.

| Option | Purpose |
| --- | --- |
| `--preprocessor-adapter {auto,gcc-compatible-c,gnu-fortran,command-template}` | Selects the compiler adapter or a custom command template. |
| `--compiler COMPILER` | An exact compiler or preprocessor executable. Defaults to `gfortran` for Fortran and `cc` for C. |
| `--preprocess-template TEMPLATE` | Runs a custom command-template preprocessor. |
| `-I DIR`, `--include-dir DIR` | Adds an include directory. |
| `-D NAME[=VALUE]`, `--define NAME[=VALUE]` | Defines a preprocessing macro. |
| `-U NAME`, `--undef NAME` | Undefines a preprocessing macro. |
| `--std STANDARD` | Passes a language standard such as `c11`, `c23`, `f2008`, or `f2018`. |
| `--compiler-arg ARG` | Passes one raw compiler argument. Repeat for more. |

Use the equals form when a value starts with `-`, for example
`--compiler-arg=-target`.

### Command templates

`--preprocessor-adapter command-template` with `--preprocess-template` runs an
arbitrary preprocessing command, for a compiler family PRIK has no adapter for.
The template must expand to a command that writes preprocessed source to
standard output. PRIK substitutes these placeholders:

| Placeholder | Expands to |
| --- | --- |
| `{source}` | The source file being preprocessed. |
| `{compiler}` | The `--compiler` value, or an empty string. |
| `{language}` | `c` or `fortran`. |
| `{include_dirs}` | Each `-I` directory, in order, as `-Idir`. |
| `{defines}` | Each `-D` macro, in order, as `-Dname[=value]`. |
| `{undefs}` | Each `-U` macro, in order, as `-Uname`. |
| `{standard}` | `-std=<value>` when `--std` is given; nothing otherwise. |
| `{compiler_args}` | Each `--compiler-arg` value, in order. |

```bash
python3 -m prik parse include/api.h --language c \
  --preprocessor-adapter command-template \
  --preprocess-template \
  'cc -E {include_dirs} {defines} {undefs} {standard} {compiler_args} {source}'
```

A collection placeholder must be its own template token; it expands to zero or
more arguments. The scalar placeholders may also appear inside a larger token.
This adapter reports no dependencies, macro dumps, or line markers, so source
locations come from the template's own output.

`--compile-commands PATH` reads per-file C preprocessing commands from a
`compile_commands.json` database. It is available only for C input.

## C include exposure

These C-only options decide which reachable project headers become public
wrapper declarations. They affect parsing, semantic inspection, and generated
C contracts—not whether the native compiler can find an include file.

| Option | Purpose |
| --- | --- |
| `--include-exposure {reachable-project,roots-only}` | Exposes reachable project headers by default, or only the root inputs. |
| `--public-include PATH_OR_PATTERN` | Exposes declarations from matching included files. Repeat as needed. |
| `--private-include PATH_OR_PATTERN` | Hides declarations from matching included files. Repeat as needed. |
| `--export-symbols FILE` | Selects the exact reachable C functions named by FILE and makes those declarations public, including declarations from otherwise-private system headers. |

`--export-symbols` is a function-only allowlist for commands that produce
semantic IR: source builds, `semantics`, and `generate --pyi`. The UTF-8 file
contains one ASCII C identifier per line; blank lines and text after `#` are ignored.
Every listed name must resolve to exactly one reachable function. Empty files,
invalid or repeated names, unknown names, names of non-function declarations,
and ambiguous declarations fail the command. All declarations not selected by
the file are removed from that semantic surface. This makes the allowlist the
explicit exception to `roots-only`, system-header privacy, and matching
`--private-include` rules; it does not change native linking or make an
unsupported selected signature buildable.

## Output and diagnostics

| Option | Purpose |
| --- | --- |
| `--json` | Selects the complete JSON record instead of the human-readable report. Available on `parse`, `semantics`, `probe`, and wrapper builds. |
| `--out [PATH]` | Destination for the selected format, generated `.pyi` package directory, or the wrapper module and final `.so`. It never changes which format is produced. |
| `--out-dir DIR` | Wrapper build output directory. Default `./__prik__`. |
| `--verbose` | Announces each generation, artifact, and compile step. It prints every compiler or linker command before starting it, times each operation, and reports total build time last. |
| `--no-color` | Disables ANSI color in parse diagnostics. |
| `--debug` | Re-raises failures so Python prints a traceback. |

Wrapper build JSON includes generated artifact paths, `native_build_plan`, and
for semantic `.pyi` builds the normalized replay `manifest`.

## Checked workflows

| Workflow | Command |
| --- | --- |
| Parse a compact Fortran tree | `python3 -m prik parse path/to/file.f90` |
| Parse with scope variables | `python3 -m prik parse path/to/file.f90 --show-vars` |
| Cap repeated parse sections | `python3 -m prik parse path/to/file.f90 --print-limit 50` |
| Write parser JSON | `python3 -m prik parse path/to/file.f90 --json --out report.json` |
| Print semantic IR | `python3 -m prik semantics path/to/file.f90` |
| Emit a semantic `.pyi` contract directory | `python3 -m prik generate --pyi path/to/file.f90 --out contracts` |
| Build a Fortran wrapper | `python3 -m prik path/to/file.f` |
| Build a supported C wrapper | `python3 -m prik --language c path/to/file.c --compiler cc` |
| Parse a C header as JSON | `python3 -m prik parse path/to/api.h --language c --json` |
| Parse C with the native project's preprocessing flags | `python3 -m prik parse path/to/api.h --language c --compiler clang -I include -D API_EXPORT= --std c11` |
| Build with native compiler and link flags | `python3 -m prik path/to/file.f90 --native-compile-flags="-O3 -fopenmp" --wrapper-c-flags=-fopenmp` |
| Build from a semantic contract and native object | `python3 -m prik contracts/module.pyi --native-objects build/module.o -I build` |
| Build a C-native semantic contract | `python3 -m prik --language c contracts/module.pyi --native-c-sources native/module.c --compiler cc` |
| Build with an explicit module and `.so` name | `python3 -m prik path/to/file.f90 --out my_extension` |
| Generate wrapper sources only | `python3 -m prik generate --sources dependency.f90 api.f90 --out-dir build` |
| Generate an editable Makefile | `python3 -m prik generate --makefile dependency.f90 api.f90 --out-dir build` |
| Generate a `.pyi` replay manifest and Makefile | `python3 -m prik generate --makefile contracts/module.pyi --native-fortran-sources native/module.f90 --out-dir build --json` |
| Replay a `.pyi` manifest | `python3 -m prik --build-manifest build/prik-build.json` |

The `points.f90` examples reuse the source from the
[derived-type guide](../guide/wrapping-derived-types.md#complete-example),
which has a complete source, build, import, and result flow.

## Related pages

- [Python API Reference](python-api.md) — the same workflows from Python.
- [C Support](../language-support/c-support.md) — the direct C lane's complete
  source, contract, build, and Python workflows.
- [Editing `.pyi` Contracts](pyi-contracts/index.md) — supported contract edits.
