---
title: CLI Commands Reference
audience: users, developers
prerequisites: installation
related: python-api.md, configuration-files.md
status: maintained
publication: draft
---

# CLI Commands Reference

This page documents the checked command surface exposed by:

```bash
prik --version
python3 -m prik --help
python3 -m prik --help-build
```

`prik --version` and `python3 -m prik --version` print the installed
distribution version and exit successfully. The value comes from the same
package metadata as `prik.__version__`.

With no subcommand, prik builds a wrapper from Fortran source or a semantic
`.pyi` contract. Four focused subcommands expose parsing, semantic inspection,
artifact generation, and target probing. The default `--help` output is a
concise overview of common inputs, build controls, and commands. Use
`--help-build` for every default-build option.

Every help page places a clear one-line purpose directly below its usage. Its
examples are grouped by task rather than presented as an unlabeled command
list, so users can scan directly to a basic invocation, a different frontend
or output form, or a cross-target workflow. The examples remain illustrative;
the option groups above them are the exhaustive command contract.

<!-- PRIK_C_DOCS_START
The command accepts source paths and then either builds a wrapper or runs an
inspection stage. Fortran source files can usually be inferred from their
suffix. C files, directories, and unknown suffixes require `&#45;&#45;language`.
PRIK_C_DOCS_END -->

## Command shapes

```bash
python3 -m prik INPUT [INPUT ...] [BUILD OPTIONS]
python3 -m prik {parse,semantics,generate,probe} [OPTIONS] ...
```

The default compiled build accepts one or more Fortran source `INPUT` values,
or exactly one semantic `.pyi` entry contract. Do not mix those two input
forms. When `--build-manifest PATH` is supplied, omit positional input
entirely. In the second form, select one of the four command names shown in
braces; `COMMAND` is not a literal command or input. Inspection and
contract-generation commands advertise their own supported frontend languages
in their focused help; compiled wrapper generation is currently Fortran-only.
The concise top-level help lists `INPUT` under `positional arguments:` and the
common flags under `build options:`. All help section headings use lowercase
for the same presentation in plain and colored output. Full build help and
every source-taking subcommand use the same concise section style. Positional
`INPUT` values appear under `positional arguments:`. Full build help puts
`--language` and manifest selection under `input selection:`, while
source-taking subcommands use `input options:` for their corresponding
controls. Output and diagnostic controls always have separate groups. Each
subcommand describes shared compiler and include flags in terms of that
subcommand's actual stage rather than copying the default-build wording.
Accordingly, full default-build help advertises `--language {fortran}` only;
`parse`, `semantics`, `generate --pyi`, and `probe` advertise
`--language {fortran,c}` because those paths currently support both frontends.

<!-- PRIK_C_DOCS_START
```bash
python3 -m prik [PATH ...] [&#45;&#45;language fortran|c] [stage-or-build] [options]
```
PRIK_C_DOCS_END -->

The top-level help intentionally lists only common build options. Run
`python3 -m prik --help-build` for the complete build surface. Each subcommand
has its own options; use `parse --help`, `semantics --help`, `generate --help`,
or `probe --help` after `python3 -m prik` to see only the options relevant to
that command. The concise build list covers output naming and location, build
compiler and include-directory selection, native compile flags such as `-O3`,
native libraries, compiler job limits, and verbose build output.
Command-specific help describes the stage-specific role of shared flags; for
example, `parse --help` explains
that `--compiler` and `-I` configure preprocessing. The concise build help does
not mislabel them as preprocessing-only options. It also keeps short examples
for a basic source build, an explicitly named extension, and semantic contract
generation; `--help-build` labels its basic build, semantic-contract build,
and manifest-replay examples separately. Both help levels reuse the canonical
`points.f90` and `geometry` naming from the
[derived-type guide](../guide/wrapping-derived-types.md#complete-example),
which contains a complete source, build, import flow, and expected result.

The full build help uses the following two forms:

```text
usage: python3 -m prik INPUT [INPUT ...]
       [OUTPUT OPTIONS] [COMPILER OPTIONS] [WRAPPER OPTIONS]
       [NATIVE OPTIONS] [DIAGNOSTIC OPTIONS]
       python3 -m prik --build-manifest PATH [MANIFEST OVERRIDES]
```

Its groups are exhaustive rather than curated: `input selection` contains the
frontend and manifest selectors; `output options` contains the module name,
build directory, and structured-result selection; `compiler options` contains
every compiler and preprocessing control; `wrapper options` contains generated
wrapper naming and compiler behavior; `native options` contains native sources,
flags, objects, libraries, directories, and ordered link items; and
`diagnostic options` contains verbose, color, and traceback controls. The
default output directory shown there is `./__prik__`.

`--build-manifest PATH` reads an existing `prik-build.json` and replays the
saved build; it does not generate a manifest. Manifest replay accepts only
overrides that the replay implementation consumes:
`--out`, `--compiler`, `-I`/`--include-dir`, `--jobs`, `--json`, `--verbose`,
`--no-color`, and `--debug`. The manifest owns its output
directory, input language, preprocessing recipe, wrapper behavior, native
inputs, and link plan, so replay rejects flags from those areas instead of
silently ignoring them.

| Command | Purpose |
| --- | --- |
| no subcommand | Builds and imports one extension path from Fortran source or a semantic `.pyi` contract. |
| `parse` | Prints parser facts and diagnostics. |
| `semantics` | Prints language-neutral semantic IR. |
| `generate` | Generates `.pyi` contracts, wrapper sources, or a Makefile build without compiling an extension. |
| `probe` | Probes compiler-target datatype facts as JSON or a Markdown mapping table. |

## Input selection

| Option | Purpose |
| --- | --- |
| `paths` | Source files, `.pyi` files, or directories. Omit only when using `--build-manifest`. |
| `--version` | Prints the installed PRIK version and exits. |
| `--language fortran` | Selects the Fortran frontend explicitly when suffix inference is unavailable. |
| `--jobs N` | Limits concurrent compiler processes to `N`; the default uses the CPUs available to prik. |

<!-- PRIK_C_DOCS_START
| `&#45;&#45;language {fortran,c}` | Selects the frontend. Required for C inputs, directories, and unknown suffixes. |
PRIK_C_DOCS_END -->

## Parse and semantics

Inspection is selected by a subcommand rather than a stage flag. Compact usage
lines leave the complete command-specific option inventory to the groups below
them:

```bash
python3 -m prik parse INPUT [INPUT ...] [OPTIONS]
python3 -m prik semantics INPUT [INPUT ...] [OPTIONS]

python3 -m prik parse points.f90
python3 -m prik semantics points.f90
```

Parse-report controls such as `--show-vars` and `--print-limit` appear only in
`prik parse --help`. Target datatype measurement is internal to semantic
conversion and wrapping. Use the separate `prik probe` command only when you
want to inspect or save the measured target facts yourself.

The parse examples distinguish basic inspection, a detailed report, and an
alternate frontend. The semantics examples distinguish basic conversion, an
alternate frontend, and writing the combined semantic IR to a named JSON file.

`semantics` always writes its language-neutral report as JSON. With no `--out`,
it prints the combined report to standard output. `--out PATH` writes that
combined report to `PATH`; `--out` without a path writes one `.json` file beside
each input source.

## Generate

`generate` requires exactly one output mode:

```bash
python3 -m prik generate (--pyi | --sources | --makefile)
                                INPUT [INPUT ...] [OPTIONS]
python3 -m prik generate (--sources | --makefile)
                                --build-manifest PATH [OVERRIDES]
```

| Mode | Purpose |
| --- | --- |
| `--pyi` | Writes the editable semantic `.pyi` contract. |
| `--sources` | Writes wrapper source files without compiling native objects or an extension. |
| `--makefile` | Writes wrapper sources, the replay manifest when applicable, and `Makefile.prik` without compiling. |

```bash
python3 -m prik generate --pyi points.f90 --out contracts
python3 -m prik generate --sources points.f90 --out-dir build
python3 -m prik generate --makefile points.f90 --out-dir build
```

These examples reuse `points.f90` from the
[derived-type guide](../guide/wrapping-derived-types.md#complete-example).

These modes are mutually exclusive. Source and Makefile generation still run
the preprocessing and semantic-policy stages needed to produce a valid wrapper
plan; they skip native object compilation and extension linking. Their
generated commands use the build-wide `--compiler` and `-I` contract. In
`--pyi` mode those same options apply only to source preprocessing and datatype
measurement because no native build is generated.

The help page presents `generation modes` immediately after the standard
`options` group, then `positional arguments`, `input options`, compiler and
frontend-specific include controls, wrapper and native controls, output,
diagnostics, and examples. `native options` keeps native sources, compiler
flags, objects, libraries, library directories, and ordered link items
together, matching `--help-build`. `--build-manifest` reads an existing
manifest and regenerates wrapper artifacts; it is not a contract-generation
input.

## Probe

`probe` uses `--language fortran` and compiler-oriented flags instead of nested
language commands. JSON is the default; `--format markdown` prints the target
datatype mapping table. Its help examples distinguish basic native probes, a
human-readable mapping table, ABI-affecting compiler flags that change default
kinds, and a cross-target probe run through a target runner. Pass each raw
compiler flag separately, for example
`--compiler-arg=-fdefault-real-8 --compiler-arg=-fdefault-integer-8`.

```bash
python3 -m prik probe --language {fortran,c} --compiler COMPILER [OPTIONS]
```

<!-- PRIK_C_DOCS_START
The same command accepts `&#45;&#45;language c`; no language-specific nested command
is needed.
PRIK_C_DOCS_END -->

```bash
python3 -m prik probe --language fortran --compiler gfortran-13
```

<!-- PRIK_C_DOCS_START
```bash
python3 -m prik probe &#45;&#45;language c &#45;&#45;compiler gcc-13 &#45;&#45;format markdown
```
PRIK_C_DOCS_END -->

| Option | Purpose |
| --- | --- |
| `--language fortran` | Selects the Fortran target probe. |
<!-- PRIK_C_DOCS_START
| `&#45;&#45;language c` | Selects the C target probe. |
PRIK_C_DOCS_END -->
| `--compiler COMPILER` | Selects the exact native or cross compiler. |
| `--format {json,markdown}` | Chooses the machine-readable report or mapping table. |
| `--expr EXPR` | Adds a Fortran integer expression to the JSON probe; repeat for more expressions. |
| `--runner ARG` | Adds one cross-target runner command item; repeat for multiple arguments. |
| `--cache-dir PATH` | Selects reusable probe storage. |
| `--refresh` | Ignores reusable results and probes the target again. |
| `--out PATH` | Writes the probe report instead of printing it. |

Compiler preprocessing flags are accepted for JSON probes. Markdown mappings
accept compiler arguments, runner, cache, and refresh options because they
measure the standard mapping table rather than an individual preprocessed
source expression.

## Compiler preprocessing

These options control compiler preprocessing before Fortran parsing.

<!-- PRIK_C_DOCS_START
These options control preprocessing before parsing. They are most useful for C
headers, C source files, and preprocessed Fortran sources.
PRIK_C_DOCS_END -->

| Option | Purpose |
| --- | --- |
| `--preprocessor-adapter {auto,gnu-fortran,command-template}` | Selects the Fortran compiler adapter or a custom command template. |
| `--compiler COMPILER` | Uses an exact compiler or preprocessor executable. Defaults to `gfortran` for Fortran. |
| `--preprocess-template TEMPLATE` | Runs a custom command-template preprocessor. |
| `-I DIR`, `--include-dir DIR` | Adds an include directory during compiler preprocessing. |
| `-D NAME[=VALUE]`, `--define NAME[=VALUE]` | Defines a preprocessing macro. |
| `-U NAME`, `--undef NAME` | Undefines a preprocessing macro. |
| `--std STANDARD` | Passes a Fortran language standard such as `f2008` or `f2018`. |
| `--compiler-arg ARG` | Passes one raw compiler preprocessing argument. Repeat for multiple arguments. |

<!-- PRIK_C_DOCS_START
The C frontend defaults to `cc` when `&#45;&#45;compiler` is omitted.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| `&#45;&#45;compile-commands PATH` | Reads project flags from a `compile_commands.json` database. |
| `&#45;&#45;std STANDARD` | Passes a language standard such as `c11`, `c23`, `f2008`, or `f2018`. |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| `&#45;&#45;preprocessor-adapter {auto,gcc-compatible-c,gnu-fortran,command-template}` | Selects the compiler adapter family. |
PRIK_C_DOCS_END -->

Use `--compiler-arg=-target` style spelling when the value itself starts with
`-`.

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

## Parse report controls

| Option | Purpose |
| --- | --- |
| `--show-vars` | Includes module, submodule, program, and block-data variables in human-readable Fortran parse reports. |
| `--print-limit N` | Shows at most `N` items per repeated section in human-readable parse reports. |

## Wrapper builds

With no subcommand, recognizable Fortran source, semantic `.pyi` input, or a
saved manifest builds a wrapper. A positional Fortran source is both a semantic
input and a native implementation source. A `.pyi` is only the semantic
contract, so it requires at least one explicit native implementation input.
Generation without compilation belongs to the `generate` subcommand.

| Option | Purpose |
| --- | --- |
| `--compiler COMPILER` | Selects the input-language compiler used throughout a wrapper build: preprocessing, datatype measurement, native and generated-bridge compilation, and extension linking. The default is `gfortran`; the generated binding continues to use prik's binding-compiler profile. |
| `-I DIR`, `--include-dir DIR` | Adds a build-wide compiler include directory. Source builds use it during preprocessing; source and `.pyi` builds use it for native and generated wrapper compilation. Repeat to preserve search order. |
| `--strict-wrapper-names` | Rejects Python wrapper names that require escaping or collision suffixes. |
| `--build-manifest PATH` | Reads an existing semantic `.pyi` wrapper build manifest and replays its saved build. It does not generate the manifest. |
| `--no-compile-input-sources` | Treats positional Fortran sources as semantic inputs only. Requires an explicit native input; `--native-fortran-sources` remain compiled hidden implementation sources. |
| `--native-fortran-sources PATH [PATH ...]` | Compiles additional native Fortran implementation sources without using them as semantic inputs. |
| `--native-compile-flags FLAG [FLAG ...]` | Adds compiler flags to native implementation source compilation. Native source compilation is currently Fortran-only. |
| `--native-objects PATH [PATH ...]` | Links one or more native object, static archive, or shared library paths into the extension. |
| `--native-library NAME [NAME ...]` | Links system libraries by name. For example, `--native-library openblas` passes `-lopenblas` to the linker. |
| `--native-link-item KIND:VALUE [KIND:VALUE ...]` | Adds ordered extension link items. `KIND` is `object`, `archive`, `shared-library`, `library`, or `arg`. |
| `--native-library-dir DIR [DIR ...]` | Adds native library search directories and runtime paths for extension linking. |

Important boundaries:

- `parse`, `semantics`, `generate`, and `probe` are the only subcommands.
- For compiled wrapper builds, `--out NAME` selects the Python module name,
  `PyInit_<name>` symbol, JSON `module_name`, and stable `NAME.so` alias in the
  current directory. Use `--out-dir DIR` to choose where generated artifacts
  and the ABI-suffixed extension are built. Give `--out` an explicit path to
  place the stable alias elsewhere.
- Wrapper `--out` requires a value and accepts `NAME` or `NAME.so`.
- `generate --sources` and `generate --makefile` use `--out-dir`; `generate
  --pyi` uses `--out` for its contract package.
- `.pyi` wrapper builds require at least one native implementation input such
  as `--native-fortran-sources`, `--native-objects`, `--native-library`, or
  `--native-link-item`.
- Source-driven builds accept individual Fortran files or directories.
  Directories are expanded recursively in deterministic path order.
- `--no-compile-input-sources` keeps positional Fortran sources as semantic inputs
  but removes them from native compilation. It requires an explicit native
  implementation through `--native-fortran-sources`, `--native-objects`,
  `--native-library`, or `--native-link-item`. Sources passed through
  `--native-fortran-sources` are still compiled without becoming public API.
- Source-driven builds may use the same native source, object, library,
  include-directory, library-directory, and ordered-link options to complete
  the extension build. These inputs augment the positional implementation
  sources; they do not become semantic wrapper inputs.
- In a wrapper build, `--compiler` is a build input rather than a
  preprocessing-only setting. It selects the input-language compiler command
  used for preprocessing and datatype measurement, then for native source and
  generated bridge compilation, and finally for extension linking. prik still
  selects the generated binding compiler from its compiler profile.
- `-I DIR` is build-wide: prik preserves the supplied order in preprocessing
  and in native, bridge, and binding compilation. Use it for source includes,
  compiler-produced module files, and native interface directories.
- `--native-compile-flags` compiles the native implementation. The public name
  identifies the native compilation phase rather than the current source
  language; native source compilation is currently Fortran-only.
  `--wrapper-fortran-flags` compiles the generated Fortran bridge, and
  `--wrapper-c-flags` compiles the generated binding and supplies additional
  extension-link flags.
- For source-driven builds, prik also applies `--native-compile-flags` to its
  internal datatype measurement. Target-changing flags such as
  `-fdefault-integer-8` or `-fdefault-real-8` therefore affect both native
  compilation and the semantic wrapper types without separate probe options.
- Native input options accept one or more values per occurrence and may also be
  repeated. prik preserves the supplied source, artifact, and link-item order.
  For compiler flags or prefixed library names that start with `-`, group them
  with the equals form, for example `--native-compile-flags="-O3 -fopenmp"` or
  `--native-library="-lblas -llapack"`.
- In `.pyi` Makefile mode, prik writes `<out-dir>/prik-build.json` first and
  generates `<out-dir>/Makefile.prik` from that manifest.
- `--build-manifest PATH` reads a saved manifest and rebuilds from it; it does
  not generate the manifest. `generate --makefile
  --build-manifest PATH` regenerates `Makefile.prik` without positional
  contracts or repeated native flags. Replay may override only `--out`,
  `--compiler`, `-I`/`--include-dir`, `--json`, `--verbose`, `--no-color`, and
  `--debug`; all other build settings come from the
  manifest.

<!-- PRIK_C_DOCS_START
- C source inspection is supported; runtime wrapping of user-supplied C
  libraries is not part of this CLI surface yet.
PRIK_C_DOCS_END -->

## Output and diagnostics

| Option | Purpose |
| --- | --- |
| `--json` | Selects JSON instead of the default human-readable output for commands that support both formats. Semantic reports are always JSON and therefore do not expose this flag. |
| `--out [PATH]` | Writes command output, selects a generated `.pyi` package directory, or names the wrapper Python module and final `.so`. |
| `--out-dir DIR` | Selects the wrapper build output directory. The default is `./__prik__`. |
| `--verbose` | Announces and completes binding, bridge, and header source-text generation in order, then each written artifact, source/object compilation pair, and final extension path before printing the exact compiler or linker command; it times each non-writing operation and reports total build time last. |
| `--wrapper-compiler-debug` | Uses the compiler debug profile for direct wrapper builds instead of the default release profile. |
| `--wrapper-fortran-flags FLAG...` | Appends flags to generated Fortran bridge compilation commands. |
| `--wrapper-c-flags FLAG...` | Appends flags to generated binding compilation and extension-link commands. |
| `--no-color` | Disables ANSI color in parse diagnostics. |
| `--debug` | Re-raises command failures so Python prints a traceback. |

When `rich-argparse` is installed, prik uses its colored help formatter
automatically. Install the optional UI dependencies for a published package
with `python3 -m pip install 'prik[pretty]'`, or from an editable source
checkout with `python3 -m pip install -e '.[pretty]'`. Plain `argparse` help
remains the deterministic fallback, and `--no-color` or `NO_COLOR` selects it
explicitly.

Use `--out` for command output, generated `.pyi` contract packages, or
the wrapper Python module and final `.so`. Use `--out-dir` for wrapper build artifacts.
Wrapper build JSON includes generated artifact paths,
`native_build_plan`, the structured native compile/link plan for the extension,
and for semantic `.pyi` builds the normalized replay `manifest`.

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
| Build a Fortran wrapper with native compiler and link flags | `python3 -m prik path/to/file.f90 --native-compile-flags="-O3 -fopenmp" --wrapper-c-flags=-fopenmp` |
| Build from a semantic contract and native object | `python3 -m prik contracts/module.pyi --native-objects build/module.o -I build` |
| Build a Fortran wrapper with an explicit module and `.so` name | `python3 -m prik path/to/file.f90 --out my_extension` |
| Generate wrapper sources only | `python3 -m prik generate --sources dependency.f90 api.f90 --out-dir build` |
| Generate an editable Makefile | `python3 -m prik generate --makefile dependency.f90 api.f90 --out-dir build` |
| Generate a `.pyi` replay manifest and Makefile | `python3 -m prik generate --makefile contracts/module.pyi --native-fortran-sources native/module.f90 --out-dir build --json` |
| Replay a `.pyi` manifest | `python3 -m prik --build-manifest build/prik-build.json` |

<!-- PRIK_C_DOCS_START
| Parse a C API | `python3 -m prik path/to/api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;json` |
| Parse with compiler preprocessing | `python3 -m prik path/to/api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;compiler clang-18 -I include -D API_EXPORT= &#45;&#45;std c11` |
PRIK_C_DOCS_END -->

## Related pages

- Use [Python API Reference](python-api.md) when calling prik from Python.
- Use [Fortran Wrapper Reference](fortran-wrapper.md) for wrapper
  build workflows.
- Use [Semantic .pyi Format](semantic-pyi-format.md) when editing wrapper
  contracts.
