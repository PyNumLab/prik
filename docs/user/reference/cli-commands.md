---
title: CLI Commands Reference
audience: users, developers
prerequisites: installation
related: python-api.md, fortran-wrapper.md
status: maintained
publication: draft
---

# CLI Commands Reference

With no subcommand, prik builds a wrapper. Four subcommands expose the earlier
stages without building one.

```bash
python3 -m prik INPUT [INPUT ...] [BUILD OPTIONS]
python3 -m prik {parse,semantics,generate,probe} [OPTIONS] ...
```

| Command | Purpose |
| --- | --- |
| no subcommand | Builds one importable extension from Fortran source or a semantic `.pyi` contract. |
| `parse` | Prints parser facts and diagnostics. |
| `semantics` | Prints language-neutral semantic IR as JSON. |
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

When `rich-argparse` is installed, prik uses its colored help formatter
automatically. Install it with `python3 -m pip install 'prik[pretty]'`, or from
an editable checkout with `python3 -m pip install -e '.[pretty]'`. Plain
`argparse` help is the deterministic fallback; `--no-color` or `NO_COLOR`
selects it explicitly.

## Input selection

The default build accepts either one or more Fortran source `INPUT` values, or
exactly one semantic `.pyi` entry contract — never both. With
`--build-manifest PATH`, omit positional input entirely.

| Option | Purpose |
| --- | --- |
| `paths` | Source files, `.pyi` files, or directories. Omit only with `--build-manifest`. |
| `--version` | Prints the installed PRIK version and exits. |
| `--language fortran` | Selects the frontend explicitly when suffix inference is unavailable. |
| `--build-manifest PATH` | Replays a saved `prik-build.json`. It does not generate one. |
| `--jobs N` | Limits concurrent compiler processes. The default uses available CPUs. |

<!-- PRIK_C_DOCS_START
| `&#45;&#45;language {fortran,c}` | Selects the frontend. Required for C inputs, directories, and unknown suffixes. |
PRIK_C_DOCS_END -->

Compiled wrapper builds are Fortran-only, so the default build advertises
`--language {fortran}`. The `parse`, `semantics`, `generate --pyi`, and `probe`
paths advertise `--language {fortran,c}` because they support both frontends.

Directories are expanded recursively in deterministic path order.

<!-- PRIK_C_DOCS_START
Fortran source files can usually be inferred from their suffix. C files,
directories, and unknown suffixes require `&#45;&#45;language`.
PRIK_C_DOCS_END -->

## Wrapper builds

A positional Fortran source is both a semantic input and a native
implementation source. A `.pyi` is only the semantic contract, so it needs at
least one explicit native input: `--native-fortran-sources`, `--native-objects`,
`--native-library`, or `--native-link-item`.

| Option | Purpose |
| --- | --- |
| `--out NAME` | Python module name, `PyInit_<name>` symbol, and stable `NAME.so` alias. Accepts `NAME` or `NAME.so`, and requires a value. |
| `--out-dir DIR` | Where generated artifacts and the ABI-suffixed extension are built. Default `./__prik__`. |
| `--compiler COMPILER` | The input-language compiler used for the whole build: preprocessing, datatype measurement, native and bridge compilation, and linking. Default `gfortran`. |
| `-I DIR`, `--include-dir DIR` | Build-wide include directory. Repeat to preserve search order. |
| `--strict-wrapper-names` | Rejects Python names that would need escaping or a collision suffix. |
| `--no-compile-input-sources` | Treats positional sources as semantic inputs only. Requires an explicit native input. |
| `--native-fortran-sources PATH ...` | Compiles extra native sources without exposing them as public API. |
| `--native-compile-flags FLAG ...` | Flags for native implementation compilation. |
| `--native-objects PATH ...` | Links object files, static archives, or shared libraries. |
| `--native-library NAME ...` | Links system libraries by name — `--native-library openblas` passes `-lopenblas`. |
| `--native-link-item KIND:VALUE ...` | Ordered link items. `KIND` is `object`, `archive`, `shared-library`, `library`, or `arg`. |
| `--native-library-dir DIR ...` | Library search directories and runtime paths. |
| `--wrapper-compiler-debug` | Uses the compiler debug profile instead of release. |
| `--wrapper-fortran-flags FLAG ...` | Flags for generated Fortran bridge compilation. |
| `--wrapper-c-flags FLAG ...` | Flags for generated binding compilation and extension linking. |

Build rules worth knowing:

- prik selects the generated binding compiler from its own profile;
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
  than silently ignored.

<!-- PRIK_C_DOCS_START
- C source inspection is supported; runtime wrapping of user-supplied C
  libraries is not part of this CLI surface yet.
PRIK_C_DOCS_END -->

## Parse and semantics

```bash
python3 -m prik parse INPUT [INPUT ...] [OPTIONS]
python3 -m prik semantics INPUT [INPUT ...] [OPTIONS]
```

| Option | Purpose |
| --- | --- |
| `--show-vars` | Includes module, submodule, program, and block-data variables in human-readable parse reports. |
| `--print-limit N` | Shows at most `N` items per repeated section in human-readable parse reports. |

`semantics` always emits JSON. With no `--out` it prints the combined report;
`--out PATH` writes that report to `PATH`; bare `--out` writes one `.json`
beside each input source.

Target datatype measurement happens automatically inside semantic conversion.
Use `probe` only when you want to inspect those facts yourself.

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

`--sources` and `--makefile` still run preprocessing and semantic policy to
produce a valid wrapper plan; they skip object compilation and linking, and
use `--out-dir`. `--pyi` uses `--out` for its contract package, and there
`--compiler` and `-I` affect only preprocessing and datatype measurement.

In `.pyi` Makefile mode, prik writes `<out-dir>/prik-build.json` first, then
generates `<out-dir>/Makefile.prik` from that manifest.

## Probe

JSON is the default; `--format markdown` prints the target datatype mapping
table.

```bash
python3 -m prik probe --language {fortran,c} --compiler COMPILER [OPTIONS]

python3 -m prik probe --language fortran --compiler gfortran-13
```

<!-- PRIK_C_DOCS_START
```bash
python3 -m prik probe &#45;&#45;language c &#45;&#45;compiler gcc-13 &#45;&#45;format markdown
```
PRIK_C_DOCS_END -->

| Option | Purpose |
| --- | --- |
| `--language {fortran,c}` | Selects the target probe. |
| `--compiler COMPILER` | The exact native or cross compiler. |
| `--format {json,markdown}` | Machine-readable report, or the mapping table. |
| `--expr EXPR` | Adds a Fortran integer expression to the JSON probe. Repeat for more. |
| `--runner ARG` | Adds one cross-target runner command item. Repeat for more. |
| `--cache-dir PATH` | Reusable probe storage. |
| `--refresh` | Ignores reusable results and probes again. |
| `--out PATH` | Writes the report instead of printing it. |

Pass each raw compiler flag separately, for example
`--compiler-arg=-fdefault-real-8 --compiler-arg=-fdefault-integer-8`. Markdown
mappings accept compiler, runner, cache, and refresh options because they
measure the standard table rather than one preprocessed expression.

## Compiler preprocessing

These options control preprocessing before parsing.

| Option | Purpose |
| --- | --- |
| `--preprocessor-adapter {auto,gnu-fortran,command-template}` | Selects the compiler adapter or a custom command template. |
| `--compiler COMPILER` | An exact compiler or preprocessor executable. Defaults to `gfortran` for Fortran. |
| `--preprocess-template TEMPLATE` | Runs a custom command-template preprocessor. |
| `-I DIR`, `--include-dir DIR` | Adds an include directory. |
| `-D NAME[=VALUE]`, `--define NAME[=VALUE]` | Defines a preprocessing macro. |
| `-U NAME`, `--undef NAME` | Undefines a preprocessing macro. |
| `--std STANDARD` | Passes a language standard such as `f2008` or `f2018`. |
| `--compiler-arg ARG` | Passes one raw compiler argument. Repeat for more. |

Use the equals form when a value starts with `-`, for example
`--compiler-arg=-target`.

<!-- PRIK_C_DOCS_START
The C frontend defaults to `cc` when `&#45;&#45;compiler` is omitted.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| `&#45;&#45;compile-commands PATH` | Reads project flags from a `compile_commands.json` database. |
| `&#45;&#45;std STANDARD` | Passes a language standard such as `c11`, `c23`, `f2008`, or `f2018`. |
| `&#45;&#45;preprocessor-adapter {auto,gcc-compatible-c,gnu-fortran,command-template}` | Selects the compiler adapter family. |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
## C include exposure
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
These options affect wrapper exposure for reachable included C files.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Option | Purpose |
| &#45;&#45;- | &#45;&#45;- |
| `&#45;&#45;include-exposure {reachable-project,roots-only}` | Selects whether reachable project includes are public by default or only root inputs are public. |
| `&#45;&#45;public-include PATH_OR_PATTERN` | Forces matched included files to be public in wrapper output. |
| `&#45;&#45;private-include PATH_OR_PATTERN` | Forces matched included files to be private in wrapper output. |
PRIK_C_DOCS_END -->

## Output and diagnostics

| Option | Purpose |
| --- | --- |
| `--json` | Selects JSON where both formats exist. Semantic reports are always JSON and do not expose this flag. |
| `--out [PATH]` | Command output, generated `.pyi` package directory, or the wrapper module and final `.so`. |
| `--out-dir DIR` | Wrapper build output directory. Default `./__prik__`. |
| `--verbose` | Announces each generation, artifact, and compile step with its exact compiler or linker command, times each operation, and reports total build time last. |
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
| Build with native compiler and link flags | `python3 -m prik path/to/file.f90 --native-compile-flags="-O3 -fopenmp" --wrapper-c-flags=-fopenmp` |
| Build from a semantic contract and native object | `python3 -m prik contracts/module.pyi --native-objects build/module.o -I build` |
| Build with an explicit module and `.so` name | `python3 -m prik path/to/file.f90 --out my_extension` |
| Generate wrapper sources only | `python3 -m prik generate --sources dependency.f90 api.f90 --out-dir build` |
| Generate an editable Makefile | `python3 -m prik generate --makefile dependency.f90 api.f90 --out-dir build` |
| Generate a `.pyi` replay manifest and Makefile | `python3 -m prik generate --makefile contracts/module.pyi --native-fortran-sources native/module.f90 --out-dir build --json` |
| Replay a `.pyi` manifest | `python3 -m prik --build-manifest build/prik-build.json` |

<!-- PRIK_C_DOCS_START
| Parse a C API | `python3 -m prik path/to/api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;json` |
| Parse with compiler preprocessing | `python3 -m prik path/to/api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;compiler clang-18 -I include -D API_EXPORT= &#45;&#45;std c11` |
PRIK_C_DOCS_END -->

The `points.f90` examples reuse the source from the
[derived-type guide](../guide/wrapping-derived-types.md#complete-example),
which has a complete source, build, import, and result flow.

## Related pages

- [Python API Reference](python-api.md) — the same workflows from Python.
- [Fortran Wrapper Reference](fortran-wrapper.md) — build workflows in depth.
- [Semantic .pyi Format](semantic-pyi-format.md) — editing wrapper contracts.
