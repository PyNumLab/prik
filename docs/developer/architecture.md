---
title: Contributor Architecture Guide
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: source-map.md, feature-to-code-map.md, repository-structure.md, testing-strategy.md
status: maintained
publication: draft
---

# Contributor Architecture Guide

This is the first internal document to read before changing prik. It is the
single architectural map for developers, maintainers, and future
contributors: one description of the package tree, the data passed between
stages, the decisions owned by each stage, the files to open, the directly
runnable examples, and the tests that prove each boundary.

The existing [Source Map](source-map.md) remains the detailed file index, and
the [Feature To Code Map](feature-to-code-map.md) remains the route from a
user-visible behavior to its implementation and evidence. Their architectural
explanations are summarized here without duplicating their detailed indexes.
This page is the canonical orientation document; the other maps are supporting
references rather than alternative starting points.

## Documentation Decision

Prik will keep one contributor documentation area: `docs/developer/`. A
maintainer is a developer with additional release, CI, roadmap, and stewardship
responsibilities, not a separate reader who should receive a different account
of the architecture.

The former maintainer material now lives in the contributor tree by topic:

```text
docs/developer/
  architecture.md
  design/
  internal-architecture/
  roadmap/
  contributing/
  ci-cd.md
  release-process.md
  documentation-architecture.md
```

The separate `docs/maintainer/` lane has been removed together with its old
index and navigation entry. Design proposals and roadmaps remain clearly
labelled as proposals or plans; sharing one documentation area does not turn
planned architecture into implemented behavior.

## System In One View

The implemented source-driven Fortran path is:

```text
CLI or Python build request
  -> compiler-backed preprocessing and target probing
  -> language parser facts
  -> language-neutral semantic IR
  -> complete post-IR interoperability policy
  -> backend-neutral wrapper plan
  -> C and Fortran syntax-node generation
  -> language printers
  -> one GeneratedWrapper
  -> compiler and linker services
  -> importable extension and runtime objects
```

Semantic `.pyi` input joins at semantic IR construction.

<!-- PRIK_C_DOCS_START
C input currently supports preprocessing, parsing, target probing, semantic
conversion, and semantic `.pyi` inspection; it does not yet provide the
complete runtime wrapper path.
PRIK_C_DOCS_END -->

The most important dependency rule is one-way authority. Parsers describe
source. Semantic IR preserves contract facts. Policy completion decides
ownership, transfer, destruction, storage, projection, setter exposure, and
support. Planning projects those completed decisions. Code generation and
printers implement the selected plan without inventing semantic behavior.

## Direct-Execution Examples

Every selected architectural entry file ends with a small, real example
guarded by:

```python
if __name__ == "__main__":
    ...
```

Run an example from the repository root with its filename, for example:

```bash
python3 prik/parsers/fortran/parser.py
```

These examples are executable architecture notes. Each one must:

- exercise the module's actual API or data model rather than a test fixture;
- show the module's input and output at its owning stage;
- remain deterministic and write only below a temporary directory when files
  are needed;
- state or fail clearly when a compiler or optional target capability is
  required;
- avoid importing policy into a parser, semantic inference into codegen, or any
  other shortcut across the documented ownership boundaries; and
- be covered by a focused direct-execution test or by an existing CLI test.

The result of every selected file example is asserted in one inventory:

```text
tests/fortran/infrastructure/execution_examples/test_execution_examples.py
```

It contains one explicit test per production file, named in the form
`test_fortran_<folder>_<file>_execution_example`. This central owner verifies
that the commands and outputs shown throughout this guide remain executable;
feature-local tests separately prove the underlying parser, policy, codegen,
runtime, or build behavior. The `pipeline/build.py` case retains its
`fortran_end_to_end` marker because that example really compiles, imports, and
calls an extension.

Not every helper, model, or export file needs an artificial example. Each
folder section selects the files that best expose that folder's responsibility
and explains why those are its entry files. Secondary files are described when
they clarify the design and are exercised indirectly by the selected example.
Package-export `__init__.py` files normally declare namespaces and remain
side-effect free. Package `__main__.py` files are CLI launchers rather than
teaching examples, but they still use an explicit guard. The architecture
section for each package lists its useful filename-based examples and explains
what each demonstrates.

## Folder-By-Folder Coverage

The guide and examples follow dependency order. Each group was completed as a
reviewable checkpoint: first document the package contract, then add or repair
its direct examples, then run its focused tests before moving downstream.

| Order | Folder or files | What the architecture section explains | Direct-execution coverage | Focused verification |
| --- | --- | --- | --- | --- |
| 1 | `prik/`, `prik/contracts/`, `prik/stage_values.py` | Public entrypoints, CLI dispatch, public semantic-contract vocabulary, and shared stage-record behavior | Guard the CLI launchers; demonstrate a public stage record and representative runtime contract scalars; keep export-only `__init__.py` files inert | public-entrypoint, CLI, contract-runtime, and stage-record tests |
| 2 | `prik/compiler/` | Reusable compiler profiles, object inputs, command execution, native support installation, and linking; no preprocessing or semantic policy | Demonstrate profile selection, an `ObjectFile`, a dry command boundary, and temporary native-support installation without creating a wrapper plan | compiler command, verbose output, profile, and shared-library build tests |
| 3 | `prik/preprocessing/` and `prik/preprocessing/probes/` | Compiler source expansion, provenance, native Fortran includes, and compiler-measured Fortran target facts | Preserve the source and Fortran-probe examples; add a native Fortran include example; make compiler requirements explicit | Fortran preprocessing and target-probe tests |
| 4 | `prik/parsers/fortran/` and `prik/parsers/pyi/` | The Fortran and semantic `.pyi` frontend boundaries, diagnostics, source locations, and project assembly | Keep parser/type-resolver examples; add lexer, report, and semantic `.pyi` parser examples; explain passive models and utilities without contrived demos; guard all CLI launchers | parser fixtures, diagnostics, public parser APIs, and parser CLI tests |
| 5 | `prik/semantics/` | Language-neutral IR models, scalar vocabulary, Fortran and semantic `.pyi` conversion, native-contract validation, and raw metadata that survives into policy | Keep the Fortran and semantic `.pyi` converter examples; add small model, scalar, metadata, native-handle, and native-contract flows | semantic conversion, semantic `.pyi`, datatype, and native-contract tests |
<!-- PRIK_C_DOCS_START
| 3C | `prik/preprocessing/c.py` and `prik/preprocessing/probes/c_types.py` | Raw C directives and compiler-measured C target facts | Preserve the C preprocessing and probe examples | C preprocessing and target-probe tests |
| 4C | `prik/parsers/c/` | The C lexer/model/parser boundary, diagnostics, source locations, and project assembly | Keep C lexer, parser, type-resolver, and report examples | C parser fixtures, diagnostics, APIs, and CLI tests |
| 5C | `prik/semantics/c2ir.py` | C parser facts to language-neutral semantic IR | Keep the C converter example | C semantic-conversion tests |
PRIK_C_DOCS_END -->
| 6 | `prik/policy/` | Immutable completed-policy vocabulary, ownership resolution, export policy, feature-policy construction, descriptor-handle policy, and ordered completion | Keep ownership/construction/completion examples; add focused model, export, and native-array-policy examples using semantic input | infrastructure semantics, ownership, and feature-local policy tests |
| 7 | `prik/planning/` | Mechanical projection from completed semantic policy into the editable backend-neutral wrapper plan | Keep model and planner examples; ensure they show policy completion before planning and no rendering | planner and feature-local codegen-plan tests |
| 8 | `prik/codegen/` | Backend syntax nodes, datatype catalogues, docstrings, overload queries, Python facade generation, and C/Fortran lowering | Keep bridge/binding/docstring examples; add nodes, datatype registry, overload, naming, check, visitor, and Python-surface examples that consume completed plans | codegen infrastructure, golden output, complexity-policy, and feature-local codegen tests |
| 9 | `prik/printers/` | Pure serialization of already-formed C nodes, Fortran nodes, and semantic IR; no orchestration or semantic decisions | Keep Fortran and `.pyi` examples; add the matching C-node printing example | printer and generated-source golden tests |
| 10 | `prik/pipeline/` | Cross-stage `.pyi` loading, datatype reports, plan-to-rendered-wrapper orchestration, build orchestration, and returned artifacts | Keep wrapper/report/build examples; add a `.pyi` loading and reconciliation example; keep compiler-writing examples temporary | pipeline, build-mode, generated-wrapper, and semantic `.pyi` tests |
| 11 | `prik/runtime/` | Runtime handle responsibilities, generated-operation adapters, descriptor validation, and the bundled native support boundary | Add a Python runtime-handle example driven by explicit generated operations; document that `runtime/native_support` is a native payload with no substantive Python module to demonstrate | runtime handle, descriptor, ownership, and compiled runtime tests |
| 12 | `prik/naming/` and `prik/utilities/` | Cross-cutting public/native naming and genuinely domain-neutral parsing/string/visitor mechanisms | Keep the declaration-expression example; add public-name, native-symbol, string, and visitor examples | naming, utility, declaration-expression, and downstream consumer tests |
| 13 | Contributor documentation consolidation | Merge implemented architecture, design rationale, internal maps, governance workflows, and roadmaps into one developer tree; remove contradictory placeholders and duplicate audience lanes | Add a checked inventory tying every selected architectural entry file to a reproducible direct-execution route | complete documentation suite, link/navigation checks, direct-example suite, and whitespace checks |

## Acceptance Criteria For Each Package Section

A folder is complete in this guide only when its section contains all of the
following:

1. Its purpose in one paragraph.
2. What it owns and what it must not own.
3. Its important files and the role of each file.
4. The input and output values crossing its boundary.
5. Its upstream and downstream dependencies.
6. At least one runnable `python3 <filename>.py` example, or an explicit reason
   the folder contains only package manifests or non-Python payloads.
7. The focused tests that prove the contract.
8. A short change route telling a future contributor where to begin.

The completed inventory compares every `prik/` folder and every entry file
selected by this guide against this checklist. It also checks that
each folder consciously identifies its main files, so omitting a helper does
not imply that every file is equally important. A folder is not complete
merely because it appears in a package table.

## Package Root And Public Contracts

The package root is the boundary between users and the internal pipeline. It
contains only public entrypoints and one shared stage-value mechanism; domain
implementations belong in named subpackages.

| File or folder | Responsibility |
| --- | --- |
| `prik/__init__.py` | Flattens the supported Python API and lazily exposes heavyweight CLI, probe, and build functions. It must not become a second implementation home for those functions. |
| `prik/__main__.py` | Delegates `python3 -m prik` to `prik.cli.main`. Importing this launcher does not execute the CLI. |
| `prik/cli.py` | Parses user commands, validates cross-option combinations, selects inspection or build workflows, formats diagnostics, and delegates work to the owning parser or pipeline module. It coordinates stages but does not own their semantic rules. |
| `prik/stage_values.py` | Provides `StageRecord`, the mutable-producer/immutable-consumer handoff used for editable wrapper plans and generated artifacts. Recursive freezing converts mutable containers and rejects later mutation. |
| `prik/contracts/` | Defines the public names used in semantic `.pyi` files. Contract symbols are both parser-recognized syntax and, for supported primitive scalars or native descriptor handles, small runtime constructors. They are not semantic IR classes. |

The root API depends on parsers, semantic conversion, contract loading, and
runtime handles. Those packages must not import the flattened root API back;
internal code imports canonical owners to avoid cycles and hidden dependency
direction.

### `prik/__init__.py`: supported public API

The package initializer is the public import surface. Its example deliberately
uses `prik.parse_fortran_file`, rather than reaching into an implementation
package, to show what a caller receives from the stable API:

```bash
python3 prik/__init__.py
```

```text
PRIK 0.2.1
Public parser result: subroutine ping from ping.f90
```

The output demonstrates that the root exposes both package metadata and the
source-to-parser-model entrypoint. The result is still a parser fact; no
semantic conversion, policy completion, or wrapper generation has occurred.

### `prik/cli.py`: command dispatch

This file owns the top-level command vocabulary and routes a validated request
to its real stage owner. Running the file with an ordinary CLI option reaches
the same `main()` function as the installed `prik` command:

```bash
python3 prik/cli.py --version
```

```text
prik 0.2.1
```

This small output proves filename execution is a real CLI path, not a separate
tutorial implementation. Parse and build subcommands exercise the downstream
packages described later in this guide.

### `prik/stage_values.py`: mutable-to-frozen handoff

`StageRecord` lets a producing stage assemble a dataclass and then lets its
consumer freeze that value recursively:

```bash
python3 prik/stage_values.py
```

```text
Editable parser output: geometry -> ['scale', 'norm']
Frozen consumer input: geometry -> ('scale', 'norm')
Mutation rejected: ParserOutput is frozen by its consuming stage
```

The list becoming a tuple and the rejected assignment are the important
boundary: consumers can trust a completed plan or artifact not to change under
them.

### `prik/contracts/__init__.py`: public contract vocabulary

The contracts package contains names written by users in semantic `.pyi`
files. Some primitive names are also useful NumPy scalar constructors:

```bash
python3 prik/contracts/__init__.py
```

```text
Float64() -> np.float64(0.0) (float64)
Float64[:, :] -> element=Float64, rank=2, shape=(slice(None, None, None), slice(None, None, None))
```

The first line is a runtime NumPy scalar. The second is declarative contract
syntax describing element type, rank, and shape; it is interpreted later by
the semantic `.pyi` frontend rather than being a semantic IR object itself.

Package `__init__.py` files normally remain export-only manifests. The root and
`contracts` initializers are exceptions because each contains substantive
public behavior worth demonstrating. `runtime/native_support/__init__.py`
remains empty: its folder owns a native header payload, not a Python API.

Primary evidence:

- `tests/fortran/source_parsing/parsing/test_public_entrypoints.py`
- `tests/fortran/command_line_interface/pipeline/test_stage_dispatch.py`
- `tests/fortran/infrastructure/pipeline/test_stage_values.py`
- `tests/fortran/data_types/runtime/test_contract_scalar_constructors.py`

Start a root-level change in the narrow owner above. Public export changes also
update `docs/user/reference/python-api.md`; CLI changes update the CLI reference
and argument/output contract tests. A new cross-stage value should be placed at
the stage that produces it unless its freeze behavior is genuinely shared.

## Compiler Services

`prik/compiler/` is the reusable native-process layer. It receives explicit
source, object, include, library, flag, and link inputs from the build pipeline;
it constructs and optionally executes commands. It does not preprocess source,
measure datatype semantics, discover a wrapper API, complete ownership policy,
or decide build order.

| Important file | Responsibility |
| --- | --- |
| `compiler_profiles.py` | Defines coherent GNU, Intel, LLVM, NVIDIA, and PGI language profiles, attaches the active Python/NumPy build settings, and maps a selected Fortran driver family to its matching C driver family. |
| `objects.py` | Defines the immutable `ObjectFile` input for one source-to-object invocation. The pipeline—not this value—owns dependency order and concurrency. |
| `compilers.py` | Selects configured executables, builds compile/link argv, records commands, runs subprocesses when enabled, and reports concise native failures. Its record-only mode exposes commands without compiling. |
| `native_support.py` | Installs the bundled header-only binding support and a NumPy API-version header into a generated-wrapper directory when the rendered wrapper requests it. |

The upstream owner is `prik/pipeline/build.py`, which creates `ObjectFile`
records and decides dependency-ready batches. The downstream boundary is the
host compiler and linker process. `prik/preprocessing/` and its probes reuse
the same selected compiler identity and flags at earlier stages, but they own
their own source-expansion and measurement operations.

### `compiler_profiles.py`: coherent compiler families

The profile resolver normalizes a selected executable and supplies matching
language drivers and family-specific switches:

```bash
python3 prik/compiler/compiler_profiles.py
```

```text
Selected family: gfortran
Compiler profile: GNU
Matching C executable: gcc
Fortran module-output flag: -J
```

This demonstrates why the pipeline selects a profile rather than independently
guessing C and Fortran flags: one family decision yields coherent drivers and
switches.

### `objects.py`: one explicit compile input

`ObjectFile` is the immutable request passed to a compiler invocation:

```bash
python3 prik/compiler/objects.py
```

```text
Compile input: generated/bridge.f90 -> build/bridge.o
Language: fortran
Flags: ('-O2',)
Include directories: build/modules
```

The record contains everything needed for one source-to-object command. It
does not decide when that command is dependency-ready; ordering belongs to the
build pipeline.

### `compilers.py`: command construction and execution

The direct example uses record-only mode, so it exercises the real command
builder without compiling a file:

```bash
python3 prik/compiler/compilers.py
```

```text
Compiler profile: GNU
Compile input: demo.c -> demo.o
Recorded without execution: True
Contains compile switch: True
Contains requested flag: True
Commands recorded: 1
```

The output distinguishes compiler mechanics from orchestration: the caller
provided the source, object, and flag; this module converted them into one
recorded native command.

### `native_support.py`: bundled support installation

Generated C sources include bundled headers. This example installs the real
payload into a temporary wrapper directory:

```bash
python3 prik/compiler/native_support.py
```

```text
Installed directory: binding_support
Binding header present: True
NumPy version header present: True
```

It shows the precise responsibility of this file: materialize requested native
support. Whether a wrapper requests that support was already decided by
generation.

Primary evidence:

- `tests/fortran/building_shared_library/compiling/test_compiler_verbose.py`
- `tests/fortran/error_handling/compiling/test_verbose_commands.py`
- `tests/fortran/building_shared_library/pipeline/test_parallel_compilation.py`
- `tests/fortran/building_shared_library/pipeline/test_generated_wrapper_build.py`
- `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`

Start compiler-profile or argv changes in this package. Start ordering,
parallelism, artifact naming, or build-manifest changes in the pipeline. If a
requested change depends on ownership, dtype, projection, or Python API shape,
it belongs upstream of both packages rather than in a compiler flag branch.

## Preprocessing And Target Probes

`prik/preprocessing/` owns everything required to turn original Fortran source
into authoritative parser input and compiler-dependent target facts. It runs
before declaration parsing, but it is not one generic text cleanup pass:
compiler expansion, native Fortran includes, and executable datatype probes
deliberately remain separate mechanisms with separate results.

<!-- PRIK_C_DOCS_START
The same package also prepares C parser input through raw-directive inspection
and compiler-derived C target probes.
PRIK_C_DOCS_END -->

| Important file | Responsibility |
| --- | --- |
| `source.py` | Configures and invokes compiler preprocessing, collects expanded source, line-marker provenance, dependency edges, macro metadata, diagnostics, and replayable recipes. It coordinates the Fortran include pass after compiler CPP. |
<!-- PRIK_C_DOCS_START
| `c.py` | Collects safe metadata from raw C preprocessing directives and include statements before the C grammar parser runs. It does not evaluate conditional compilation or macros. |
PRIK_C_DOCS_END -->
| `fortran.py` | Recursively expands native Fortran `INCLUDE` statements left after compiler preprocessing while preserving dependency edges and generated-to-original source mappings. |
<!-- PRIK_C_DOCS_START
| `probes/c_types.py` | Compiles and runs a target probe for modeled C ABI facts such as integer widths, signedness, precision, availability, and standard opaque types. |
PRIK_C_DOCS_END -->
| `probes/fortran_types.py` | Compiles and runs target programs for Fortran kind expressions, storage widths, logical representations, and compile-time values required by semantic conversion. |

The source preprocessors output text and provenance consumed by the Fortran
parser. The probes output immutable reports consumed by Fortran semantic
conversion. Compiler identity, target flags, include paths, macros, working
directory, and optional cross-target runner are part of the probe recipe/cache
identity; measured facts must not silently cross targets. This package never
decides semantic scalar names, NumPy dtypes, ownership, or wrapper support.

<!-- PRIK_C_DOCS_START
C preprocessing results and C probe reports feed the C parser and C semantic
converter through the same stage boundary.
PRIK_C_DOCS_END -->

### `source.py`: compiler preprocessing with provenance

This is the coordinating preprocessing entrypoint. Its example expands a
native Fortran include while retaining source provenance:

```bash
python3 prik/preprocessing/source.py
```

```text
Before Fortran include expansion:
module greeting
include 'constants.inc'
...
After Fortran include expansion:
module greeting
integer, parameter :: answer = 42
...
Native includes: 1; diagnostics: 0
```

<!-- PRIK_C_DOCS_START
The same direct example then invokes the host C preprocessor:

```text
Before C compiler preprocessing:
#include "state.h"
int state_id = STATE_ID;

After C compiler preprocessing:
int state_id = 42;
```
PRIK_C_DOCS_END -->

The changed source and the dependency/diagnostic counts show that the result is
parser input plus provenance, not just cleaned text.

<!-- PRIK_C_DOCS_START
### `c.py`: raw C directive inspection

The C-specific pass records directives and includes that compiler expansion
would otherwise erase:

```bash
python3 prik/preprocessing/c.py
```

```text
Raw directive: #pragma once
Includes: local state.h, system stddef.h
Diagnostic: C_UNRESOLVED_INCLUDE
Resolved include: state.h (diagnostics: 0)
```

This output exposes the deliberate boundary: the pass records and resolves
include metadata, but it does not evaluate the C grammar or build semantic IR.
PRIK_C_DOCS_END -->

### `fortran.py`: native `INCLUDE` expansion

Fortran `INCLUDE` remains distinct from compiler macro preprocessing:

```bash
python3 prik/preprocessing/fortran.py
```

```text
Expanded parser input:
module geometry
integer, parameter :: dimensions = 3
end module geometry
Native include dependencies: 1
Generated source mappings: 5
Diagnostics: 0
```

The expanded declaration is accompanied by dependency and line-mapping facts,
which lets later parser diagnostics still identify original sources.

<!-- PRIK_C_DOCS_START
### `probes/c_types.py`: measured C target facts

```bash
python3 prik/preprocessing/probes/c_types.py
```

```text
int: 32-bit signed
```

The value is compiled and measured for the active target rather than inferred
from a host-side Python table. This example requires `cc`.
PRIK_C_DOCS_END -->

### `probes/fortran_types.py`: measured Fortran target facts

The Fortran probe resolves compiler-dependent kind expressions and storage
facts:

```bash
python3 prik/preprocessing/probes/fortran_types.py
```

```text
selected_int_kind(9) = 4
```

The result is a native kind value consumed by semantic datatype resolution.
It is not yet the stable semantic scalar name or NumPy dtype. The example
requires `gfortran` or `f95`.

Primary evidence:

<!-- PRIK_C_DOCS_START
- `tests/c/preprocessing/`
- `tests/c/probes/test_c_types.py`
PRIK_C_DOCS_END -->
- `tests/fortran/source_preprocessing/preprocessing/`
- `tests/fortran/data_types/probes/test_fortran_type_probes.py`
- `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`

Start source-expansion and provenance changes in `source.py`, native include
behavior in `fortran.py`, and target measurement or cache changes in the
Fortran probe. Parser grammar changes start downstream, while stable semantic
datatype vocabulary and NumPy lowering start in `semantics/scalar_types.py`
and `codegen/primitive_scalar_types.py`.

<!-- PRIK_C_DOCS_START
C-only directive behavior starts in `c.py`; C target measurement starts in
`probes/c_types.py`.
PRIK_C_DOCS_END -->

## Parser Frontends

`prik/parsers/` contains the active Fortran source frontend and the semantic
`.pyi` syntax frontend. Fortran owns its lexical rules, source models,
diagnostics, and project assembly; semantic `.pyi` deliberately reuses
Python's AST. A parser reports what source says. It must not choose ownership,
wrapper support, NumPy lowering, or generated API behavior.

<!-- PRIK_C_DOCS_START
The package also contains a C source frontend with its own lexical rules,
source models, diagnostics, and project assembly.
PRIK_C_DOCS_END -->

| Folder | Responsibility |
| --- | --- |
<!-- PRIK_C_DOCS_START
| `parsers/c/` | Turns prepared C translation units into C parser models and resolves supported project-level typedef/tag identities. |
PRIK_C_DOCS_END -->
| `parsers/fortran/` | Turns prepared fixed- or free-form Fortran into file/project models while preserving source locations, declarations, visibility, and unit structure. |
| `parsers/pyi/` | Reads semantic `.pyi` syntax into a standard Python `ast.Module`; interpretation belongs to `semantics/pyi2ir.py`. |

In the Fortran package, `models.py` owns passive parser dataclasses and
diagnostic types. That file has no direct example because constructing an
isolated dataclass would hide the parser boundary; the parser examples below
produce the real models. `utils.py` contains subordinate source-form and
delimiter-aware helpers exercised by the lexer, type resolver, and parser.
Package initializers are export manifests, while `__main__.py` files are guarded
`python3 -m ...` launchers.

<!-- PRIK_C_DOCS_START
### `parsers/c/lexer.py`: C lexical and top-level boundaries

The lexer preserves token locations and separates top-level declarations while
ignoring braces and semicolons nested inside a construct:

```bash
python3 prik/parsers/c/lexer.py
```

```text
Identifier tokens: struct point double x double y double norm struct point value
Segment at line 2: struct point { double x; double y; } [;]
Segment at line 3: double norm(struct point value) [;]
```

The output shows both views consumed by the parser: lexical tokens and
source-located declaration segments. It does not claim to interpret either
declaration.

### `parsers/c/parser.py`: C source models

This is the main C frontend. Its example parses one header through the public
convenience function:

```bash
python3 prik/parsers/c/parser.py
```

```text
Parsed: state_api.h
Typedef: api_size -> unsigned long
Struct: state (id)
Function: count() -> api_size
Function: step(value) -> pointer to struct state
```

The result retains C structure—typedef identity, tag fields, functions, and a
pointer declarator—for later semantic conversion. No wrapper or Python API has
been selected.

### `parsers/c/type_resolver.py`: cross-unit C identity

After project assembly, the resolver links supported typedef chains and tag
references to canonical parser objects:

```bash
python3 prik/parsers/c/type_resolver.py
```

```text
Tag reference:
state_handle -> struct state
Typedef chain:
state_alias -> raw_state -> struct state
```

This is still parser-level resolution. It answers which declaration a C name
refers to, not which semantic scalar or ownership policy it should receive.

### `parsers/c/cli.py`: C parser reports

With no arguments, filename execution parses an in-memory header and feeds the
normal human report formatter:

```bash
python3 prik/parsers/c/cli.py
```

```text
File: geometry.h
  Language: c
  Functions: 1
    - norm
  Structs: 1
    - point
  ...
  Diagnostics: 0
```

This demonstrates the inspection boundary exposed to users. Supplying paths or
options invokes the ordinary CLI instead of the teaching input.
PRIK_C_DOCS_END -->

### `parsers/fortran/lexer.py`: logical Fortran lines

The Fortran lexer detects source form, strips comments, folds continuations,
and retains the original starting line for diagnostics:

```bash
python3 prik/parsers/fortran/lexer.py
```

```text
Detected source form: free
line 1: subroutine shift(value,offset)
line 3:   real, intent(inout) :: value
line 4:   real, intent(in) :: offset
line 5: end subroutine shift
```

The first two physical lines become one logical parser record attributed to
line 1. That location contract is the lexer's output to the grammar parser.

### `parsers/fortran/parser.py`: Fortran source models

This is the main Fortran frontend and project assembler:

```bash
python3 prik/parsers/fortran/parser.py
```

```text
Module: metrics
Parameter: n = 4
Procedure: scale(values: real[1])
```

The example shows three parser facts used downstream: source-unit ownership, a
compile-time parameter expression, and an argument's intrinsic spelling and
rank. It does not map `real` to a target kind or NumPy dtype by itself.

### `parsers/fortran/type_resolver.py`: type-spec syntax

The type resolver extracts kind and character metadata without evaluating
compiler-dependent expressions:

```bash
python3 prik/parsers/fortran/type_resolver.py
```

```text
integer(4) -> 4
real(kind=selected_real_kind(15, 307)) -> selected_real_kind(15, 307)
character(len=16, kind=c_char) -> len=16, kind=c_char
```

Preserving `selected_real_kind(...)` as syntax is intentional: target-probe
facts and semantic conversion decide its meaning later.

### `parsers/fortran/cli.py`: Fortran parser reports

The no-argument example renders a real in-memory parse through the stable
report formatter:

```bash
python3 prik/parsers/fortran/cli.py
```

```text
File: geometry.f90
  Modules: 1
    - module geometry (vars=0, uses=0)
      Procedures: 1
        - function norm(value:real[0]) -> real[0]
```

The report exposes parser structure and parser datatypes. Command-line paths
and options reuse the same formatter and may request JSON or downstream
semantic reports.

### `parsers/pyi/parser.py`: syntax-only contract parsing

This frontend intentionally stops at Python AST:

```bash
python3 prik/parsers/pyi/parser.py
```

```text
Parsed AST: Module
Function node: scale
Argument annotation: Float64
Semantic conversion performed: False
```

The last line makes the ownership boundary explicit. Recognizing `Float64` as
a PRIK semantic type belongs to `semantics/pyi2ir.py`, not this parser.

Primary evidence:

<!-- PRIK_C_DOCS_START
- `tests/c/parsing/` and `tests/c/cli/`
PRIK_C_DOCS_END -->
- `tests/fortran/source_parsing/parsing/`
- `tests/fortran/command_line_interface/pipeline/`
- `tests/fortran/semantic_pyi_format/parsing/`

Start lexical/source-coordinate changes in the Fortran `lexer.py`; grammar and
source-model construction in `parser.py`; cross-file identity in the Fortran
project parser; report output in `cli.py`; and semantic meaning downstream in
the corresponding converter. Parser support never by itself establishes
wrapper support.

<!-- PRIK_C_DOCS_START
C lexical/source-coordinate changes start in `parsers/c/lexer.py`; grammar and
model construction in `parsers/c/parser.py`; and cross-file identity in the C
resolver.
PRIK_C_DOCS_END -->

## Semantic IR

`prik/semantics/` is the language-neutral contract layer. It receives Fortran
parser models or a parsed semantic `.pyi` AST and produces the same
`SemanticModule` graph. The graph preserves public names, native names, source
provenance, storage shape, projections, and raw contract metadata. It must not
complete ownership, select lowering actions, or render backend text; those
responsibilities belong to policy, planning, and codegen respectively.

<!-- PRIK_C_DOCS_START
C parser models enter the same semantic graph through the C-to-IR converter.
PRIK_C_DOCS_END -->

| Important file | Responsibility |
| --- | --- |
| `models.py` | Defines semantic modules, functions, classes, variables, types, storage/array contracts, projections, origins, and structural equality. |
| `scalar_types.py` | Defines stable scalar identities and intrinsic family/storage facts without NumPy or generated-language spellings. |
<!-- PRIK_C_DOCS_START
| `c2ir.py` | Converts C parser models and target-probe facts into semantic modules. |
PRIK_C_DOCS_END -->
| `fortran2ir.py` | Converts Fortran parser models and measured kind/compile-time facts into semantic modules. |
| `pyi2ir.py` | Interprets parsed Python AST as an editable semantic contract and reconciles imported semantic references. |
| `ownership_metadata.py` | Normalizes raw ownership and pointer requests recorded during IR construction; it does not resolve them. |
| `native_array_handles.py` | Marks allocatable/pointer descriptor handles and derives their ordinary array and element facets. |
| `native_contract.py` | Prepares and validates source-free `.pyi` native placement, projections, concrete types, and callback reconstruction. |

`metadata.py` and `pyi_metadata.py` are intentionally passive registries for
shared keys. They have no direct example because their values become meaningful
only on the models demonstrated below. `semantics/__init__.py` is an export
manifest. Combined file loading and cross-file `.pyi` reconciliation are
pipeline orchestration and are documented with `pipeline/pyi.py` later.

### `semantics/models.py`: the language-neutral graph

The model example constructs the same values a frontend converter returns:

```bash
python3 prik/semantics/models.py
```

```text
Semantic module: geometry
Function: scale -> native SCALE
Argument: values: Float64, rank=1, shape=('n',), order=F
Source provenance: fortran real
```

The public/native name distinction, shape/order contract, and source
provenance survive together. None of these values says how the generated
binding transfers or owns the argument.

### `semantics/scalar_types.py`: stable scalar vocabulary

This catalogue separates intrinsic semantic facts from target- or
backend-dependent representations:

```bash
python3 prik/semantics/scalar_types.py
```

```text
Float64: family=real, storage=64 bits
Int: family=signed_integer, storage=target-dependent
Backend spelling stored here: False
```

`Float64` fixes a semantic width, while `Int` needs target-probe information.
Neither entry owns a NumPy dtype, C spelling, or Fortran bridge spelling; those
maps live at their respective runtime and code-generation boundaries.

<!-- PRIK_C_DOCS_START
### `semantics/c2ir.py`: C facts to semantic IR

The C converter consumes parser objects rather than reparsing source:

```bash
python3 prik/semantics/c2ir.py
```

```text
math.scale(value): Int <- Int
```

The arrow summarizes conversion of the C argument and result into stable `Int`
semantic identities. It does not imply that C input can yet follow the complete
wrapper-runtime pipeline.
PRIK_C_DOCS_END -->

### `semantics/fortran2ir.py`: Fortran facts to semantic IR

The Fortran converter normalizes measured kind and source storage information:

```bash
python3 prik/semantics/fortran2ir.py
```

```text
math.scale(value): Float64 via reference storage
```

Here the source `real` declaration has become stable `Float64`, while reference
storage remains an explicit semantic fact. Ownership and Python/native barrier
actions are still undecided.

### `semantics/pyi2ir.py`: editable contract to semantic IR

This converter gives semantic meaning to the AST produced by
`parsers/pyi/parser.py`:

```bash
python3 prik/semantics/pyi2ir.py
```

```text
math.scale(value): Float64 -> Float64
```

Unlike the syntax-only parser example, this result contains a semantic module,
function, argument type, and result type. Contract validation happens here;
post-IR policy completion remains downstream.

### `semantics/ownership_metadata.py`: unresolved ownership requests

Frontends use these setters to normalize user/source claims before complete
signatures and relationships are available:

```bash
python3 prik/semantics/ownership_metadata.py
```

```text
Raw ownership request: owner=caller, transfer=in_place, destruction=caller
Pointer contract: nullable=True, lifetime=owner, reassociation=forbidden
Completed lowering action present: False
```

The final line is the boundary: normalized metadata is input to policy
completion, not permission for a generator to infer a transfer or codegen
action.

### `semantics/native_array_handles.py`: descriptor and data facets

A native descriptor handle is semantically different from the array data it
currently addresses:

```bash
python3 prik/semantics/native_array_handles.py
```

```text
Descriptor kind: allocatable
Data facet: Float64, rank=2, shape=('rows', 'columns')
Element facet: Float64, rank=0
Handle marker retained by data facet: False
```

The derived data facet deliberately drops handle-only ownership and descriptor
metadata. Policy can therefore reason separately about the native container,
the exposed array view, and one element type.

### `semantics/native_contract.py`: source-free native validation

Semantic `.pyi` can describe a native artifact without available source, but
the contract must still reconstruct placement and ABI-relevant type facts:

```bash
python3 prik/semantics/native_contract.py
```

```text
Prepared origin: fortran module math
Valid contract issues: 0
Invalid contract issue: pyi_native_type_missing at math.broken.value
```

The validator prepares native origin information and reports a stable issue at
the exact semantic owner when a concrete dtype is missing. It validates the
contract; it does not compile or load the artifact.

Primary evidence:

- `tests/fortran/semantic_ir/semantics/`
<!-- PRIK_C_DOCS_START
- `tests/c/semantics/conversion/`
PRIK_C_DOCS_END -->
- `tests/fortran/semantic_pyi_format/`
- `tests/fortran/data_types/semantics/`
- `tests/fortran/native_array_handles/semantics/`
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`

Start model-shape changes in `models.py`, stable primitive vocabulary in
`scalar_types.py`, Fortran or semantic `.pyi` conversion in its corresponding
`*2ir.py` file, and raw contract normalization in its focused helper. If the
question is which transfer, lifetime, setter, projection, or lowering action is
valid, the change starts in `prik/policy/`, not here.

<!-- PRIK_C_DOCS_START
C semantic conversion changes start in `c2ir.py`.
PRIK_C_DOCS_END -->

## Post-IR Policy

`prik/policy/` is the last semantic authority before planning. It receives the
complete semantic module graph and resolves every choice needed by wrapper
generation: public exports, object kind, owner, transfer, destruction,
mutability/writeback, nullability, storage, projections, lifecycle actions,
descriptor operations, accessor behavior, and support blockers. A lower stage
may dispatch from these records but may not replace or infer them.

| Important file | Responsibility |
| --- | --- |
| `models.py` | Defines immutable backend-neutral records for completed function, argument, result, call-slot, lifecycle, class, callback, array, and module-variable policy. |
| `ownership.py` | Resolves object kind and the ownership/transfer/destruction triple into storage and strict Python/native/codegen actions. |
| `exports.py` | Completes collision-checked Python namespace and local-name policy. |
| `construction.py` | Constructs coherent wrapper-facing policy records from already completed semantic and ownership facts. |
| `completion.py` | Runs policy completion in dependency order and attaches every completed record to semantic IR. |
| `native_array_handles.py` | Defines descriptor-handle/array ABI selectors, strict dispatch records, and build requirements selected by completed handle policy. |

The package initializer exports only the public completion entrypoint. Policy
models are separate from construction rules so planning and codegen can depend
on completed vocabulary without depending on the rule implementation.

### `policy/models.py`: immutable completed decisions

The models example creates representative array and lifecycle records:

```bash
python3 prik/policy/models.py
```

```text
Array policy: rank=2, shape=('rows', 'columns'), order=F
Lifecycle policy: copy_out writeback via copy_in_out
Completed record mutation rejected: True
```

Unlike raw semantic metadata, these records state the selected phase,
operation, and codegen action. Their immutability makes policy a reliable input
to planning and both backend generators.

### `policy/ownership.py`: lifetime and barrier resolution

The ownership resolver turns one semantic argument and its use context into a
complete decision:

```bash
python3 prik/policy/ownership.py
```

```text
before: math.scale(value): Float64 semantic IR
after: scalar/caller/call_local; scalar_value -> pass_value
```

The result names the object kind, owner, transfer, Python extraction action,
and native handoff action. Binding and bridge code must consume those values;
they cannot rediscover them from `Float64` or argument intent.

### `policy/exports.py`: completed Python placement

Export policy resolves namespace placement and collision-safe local names:

```bash
python3 prik/policy/exports.py
```

```text
Native semantic owner: math.SCALE_VALUE
Python export: linear_algebra.scale_value
Completed policy type: PythonExportPolicy
```

The native identity remains unchanged while the Python-facing path becomes an
explicit immutable policy value consumed downstream.

### `policy/construction.py`: coherent wrapper policy

Construction combines completed ownership with ABI, result, and native-call
slot rules:

```bash
python3 prik/policy/construction.py
```

```text
before: math.scale(value): Float64 semantic IR
after: direct_transfer; result=native_scalar; native=pass_value
```

The output relates three sides of one call: bridge data movement, direct-result
ABI, and native-slot handoff. Construction does not generate a wrapper plan or
render code.

### `policy/completion.py`: the mandatory ordered boundary

Normal callers use this entrypoint rather than invoking individual rules:

```bash
python3 prik/policy/completion.py
```

```text
before: math.scale(value): Float64 semantic IR
after: math.scale(value): scalar_value -> pass_value
```

Completion first resolves exports and dependent graph facts, then ownership,
accessor, feature, and wrapper policies. The attached `scalar_value ->
pass_value` actions make the semantic graph eligible for planning. Unsupported
contracts retain explicit blockers and fail before codegen.

### `policy/native_array_handles.py`: descriptor ABI and build policy

This example starts from an already completed pointer-handle policy:

```bash
python3 prik/policy/native_array_handles.py
```

```text
Handle policy: pointer/pointer, storage=alias
Allowed operations: to_numpy, nullify
Array ABI: descriptor
Selected build header: ISO_Fortran_binding.h
```

The descriptor ABI, permitted operations, storage mode, and header requirement
are selected policy outputs. Planning and compilation consume them; neither
stage scans semantic datatypes to decide that the header is needed.

Primary evidence:

- `tests/fortran/infrastructure/semantics/`
- feature-local `tests/fortran/*/policy/` directories
- `tests/fortran/native_array_handles/policy/`
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`

Start a new semantic decision in `completion.py` and its focused constructor or
resolver. Put reusable immutable output vocabulary in `models.py`. Extend
strict descriptor dispatch/build selection in `native_array_handles.py`. If a
change only projects an existing decision into implementation fields, it
belongs downstream in planning; if a generator currently guesses the decision,
remove the guess and complete the policy here first.

## Wrapper Planning

`prik/planning/` mechanically projects policy-completed semantic IR into one
backend-neutral `ModulePlan`. The plan joins shared transfer facts with
binding-specific and bridge-specific views, namespace placement, stable native
symbols, lifecycle ordering, and required headers. Planning may organize and
validate completed decisions; it may not reinterpret source declarations,
select ownership, or render output text.

| Important file | Responsibility |
| --- | --- |
| `models.py` | Defines the editable typed plan tree rooted at `ModulePlan`, including namespace, function, argument/result, native-slot, lifecycle, descriptor, callback, derived-object, binding, and bridge views. |
| `planner.py` | Reads completed policy records, validates their presence/support, assigns shared roles and stable symbols, and constructs the plan tree in deterministic order. |

The package initializer exports the plan types and `WrapperPlanner`; it contains
no separate behavior to demonstrate. Codegen receives only the completed plan,
and `WrapperGenerator` validates and freezes that tree before invoking either
backend.

### `planning/models.py`: the typed plan representation

The model example constructs the smallest coherent procedure plan directly:

```bash
python3 prik/planning/models.py
```

```text
Plan owner: demo
Python export: ping
Native procedure: PING
Native slots: 0
```

The same function has an explicit Python binding view and native bridge view.
The plan carries no native slots because the example subroutine has no
arguments or results. Constructing records here demonstrates representation,
not a shortcut around normal policy completion.

### `planning/planner.py`: completed policy to plan

The planner example follows the real boundary: construct semantic IR, complete
policy, then build the plan:

```bash
python3 prik/planning/planner.py
```

```text
Plan owner: planner_demo
Python export: double_value
Native target: DOUBLE_VALUE
Conversion order: ('planner_demo.double_value.value',)
```

The final role is the stable shared identity used to order binding conversion
and connect the matching native-call slot. The planner copied selected actions
from completed policy; it did not decide them from `Float64`.

Primary evidence:

- `tests/fortran/infrastructure/codegen/test_plan.py`
- `tests/fortran/infrastructure/codegen/test_planner.py`
- feature-local `tests/fortran/*/codegen/` plan assertions
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`

Start plan-shape changes in `models.py` and projection/indexing changes in
`planner.py`. A new field is justified when codegen needs an already completed
fact in typed form. If deciding the field requires reasoning about ownership,
intent, mutability, projections, or support, complete that decision in policy
first. Rendering, emitted temporaries, and source syntax belong downstream.

## Backend Node Generation

`prik/codegen/` consumes only a validated `ModulePlan` and produces typed C and
Fortran syntax nodes plus planned Python-facade source. It owns emitted-code
mechanisms—temporary declarations, conversion calls, native bridge bodies,
module initialization, and class-facade assembly—but it must not infer semantic
policy. Language printers serialize the resulting nodes in the next stage.

| Folder or important file | Responsibility |
| --- | --- |
| `nodes.py` | Defines the typed C/Fortran syntax trees shared by emitters and printers. |
| `primitive_scalar_types.py` | Maps already resolved semantic scalar identities to C, Fortran, NumPy, CFI, and CPython conversion spellings. |
| `docstrings.py` | Renders Python-facing function/class documentation from completed plan facts. |
| `c/binding.py` | Lowers binding plan views into CPython/NumPy C nodes, headers, initialization, validation, and native-call wrappers. |
| `c/python_surface.py` | Emits the thin executable Python class/holder/module-proxy facade selected by completed class plans. |
| `fortran/bridge.py` | Lowers bridge plan views into `bind(C)` modules, procedures, holders, descriptors, accessors, and native calls. |

Supporting files are deliberately smaller. `overloads.py` answers shared
structural questions over completed overload plans; `visitor.py` supplies
strict class-name dispatch; `c/naming.py` centralizes binding-local generated
names; and `checks.py` implements the static codegen ownership/complexity gate
invoked by `tools/check_codegen_complexity.py`. Package initializers are export
manifests. These helpers are demonstrated through their owners or maintainer
command rather than receiving artificial standalone examples.

### `codegen/nodes.py`: typed syntax before printing

The node example constructs one C tree and one Fortran tree without rendering
either language:

```bash
python3 prik/codegen/nodes.py
```

```text
C node tree: CModule -> wrap_ping -> CReturn
Fortran node tree: FortranModule -> bind_c_ping -> FortranCall
Source text rendered: False
```

This is the boundary between generation and printing. Emitters choose typed
statements from the plan; printers later decide whitespace, punctuation, and
source layout.

### `codegen/primitive_scalar_types.py`: boundary spellings

Once semantic conversion has resolved `Float64`, codegen can look up every
required backend representation explicitly:

```bash
python3 prik/codegen/primitive_scalar_types.py
```

```text
Float64: C=double; Fortran=real(c_double); NumPy=numpy.float64
NumPy C macro: NPY_FLOAT64
Fresh editable node per lookup: True
```

The readable mapping makes the datatype boundary auditable. A lookup returns a
fresh node so one generator cannot mutate global catalogue state. Unknown
semantic identities fail rather than coercing to a nearby dtype.

### `codegen/docstrings.py`: plan-driven public documentation

Docstrings are rendered after planning so their signatures, types, results,
and errors match the generated API:

```bash
python3 prik/codegen/docstrings.py
```

```text
double_value(value) -> float64

Parameters
----------
value : float64

Returns
-------
result : float64

Raises
------
TypeError
    If an argument has an incompatible Python type or dtype.
```

The planner no longer depends on `WrapperDocstringBuilder`; codegen reads the
completed plan and renders presentation text without changing the plan.

### `codegen/c/python_surface.py`: generated Python facade

Derived classes are planned surfaces rendered as Python source embedded in the
extension module:

```bash
python3 prik/codegen/c/python_surface.py
```

```text
Rendered Python facade:
_prik_unset = object()

_prik_ops_state = {}
class State:
    'Opaque native state.'
    __slots__ = ('_prik_capsule', '_prik_owner', '_prik_ops', '_prik_origin')
    def __new__(cls, *args, **kwargs):
        'Construction is disabled.'
        raise TypeError('State objects come from native code.')
def _prik_wrap_State(capsule, owner=None, ops=None, origin='direct'):
    ...
```

The absent constructor, slots, operation map, and wrapper helper all come from
the class plan. The emitter does not inspect a Fortran derived type to decide
whether construction is allowed.

### `codegen/c/binding.py`: CPython/NumPy node lowering

The C binding example completes and plans a scalar function, then shows the
generated node mechanism:

```bash
python3 prik/codegen/c/binding.py
```

```text
Native procedure: DOUBLE_VALUE
Native call slots: implicit:value
C module: binding_demo_wrapper
Header guard: BINDING_DEMO_WRAPPER_H
Header prototypes: wrap_double_value
Binding wrapper: wrap_double_value
Return type: PyObject *
Parameters:
  self: PyObject *
  args: PyObject *
  kwargs: PyObject *
Body nodes:
  CDeclaration(...)
  ...
  CReturn(expression=CodeExpression(text='result_obj'))
```

This module produces structured C, not final source text. Its specialized
methods dispatch from planned barrier, ownership, result, descriptor, and
lifecycle actions into concrete node sequences.

### `codegen/fortran/bridge.py`: `bind(C)` node lowering

The matching bridge consumes the same shared call plan:

```bash
python3 prik/codegen/fortran/bridge.py
```

```text
Native procedure: DOUBLE_VALUE
Native call slots: implicit:value
Bridge module: bind_c_bridge_demo_wrapper
Module uses:
  use iso_c_binding, only: ... c_double ...
  use bridge_demo, only: native_double_value => DOUBLE_VALUE
Bridge procedure: bind_c_double_value
Binding name: bind_c_double_value
Procedure kind: function
Result: result :: real(c_double)
Parameters:
  value: real(c_double), value
Body nodes:
  FortranAssignment(target='result', expression=CodeExpression(text='native_double_value(value)'))
```

The shared slot becomes a value dummy and native function call. The bridge
selected no ownership behavior locally; it implemented the native barrier and
result ABI already present in the plan.

Primary evidence:

- `tests/fortran/infrastructure/codegen/`
- feature-local `tests/fortran/*/codegen/`
- generated-node and golden fixtures below those owners
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`
- `python3 tools/check_codegen_complexity.py`

Start a new emitted-code mechanism in the narrow binding, bridge, or facade
emitter that owns it, and add a typed node only when existing nodes cannot
represent it. Extend the primitive catalogue only for an already established
semantic scalar identity. If implementing the mechanism requires choosing
ownership, storage, projection, setter exposure, or support, stop and add the
missing policy/plan fact upstream first.

## Language Printers

`prik/printers/` is the final representation-to-text boundary. C and Fortran
printers serialize backend syntax nodes; the semantic `.pyi` printer serializes
semantic IR into an editable contract. Printers own formatting, escaping,
indentation, declaration order, and safe line wrapping. They do not invoke
generators, choose filenames, complete policy, or compile their output.

| Important file | Responsibility |
| --- | --- |
| `c.py` | Serializes C translation units, headers, declarations, functions, CPython tables, and statements. |
| `fortran.py` | Serializes bridge modules, interfaces, procedures, declarations, and statements while safely wrapping free-form lines. |
| `pyi.py` | Serializes semantic modules and their contract/projection metadata as compact editable semantic `.pyi`. |

The package initializer only exports the three printer classes and the
`emit_module` convenience function. C and Fortran source orchestration belongs
to `pipeline/wrapper.py`; `.pyi` loading belongs to `pipeline/pyi.py`.

### `printers/c.py`: C nodes to source

The C printer receives a formed module tree and freezes it before rendering:

```bash
python3 prik/printers/c.py
```

```text
Rendered C binding source:
#include <Python.h>

static PyObject * wrap_ping(PyObject * self) {
    Py_INCREF(Py_None);
    return Py_None;
}
```

Everything in the output was already represented by nodes: include, storage
class, signature, expression statement, and return. The printer supplied only
valid C layout and punctuation.

### `printers/fortran.py`: Fortran nodes to source

The Fortran printer renders the matching bridge representation:

```bash
python3 prik/printers/fortran.py
```

```text
Rendered Fortran bridge source:
module bind_c_printer_demo_wrapper
  use iso_c_binding, only: c_double
  use printer_demo, only: native_double_value => DOUBLE_VALUE
  implicit none
contains
  function bind_c_double_value(value) result(result) bind(c, name="DOUBLE_VALUE")
    real(c_double), value :: value
    real(c_double) :: result
    result = native_double_value(value)
  end function bind_c_double_value
end module bind_c_printer_demo_wrapper
```

The printer supplies free-form indentation and line-length enforcement. The
module imports, native alias, binding name, dummy attributes, and assignment
were selected by bridge generation.

### `printers/pyi.py`: semantic IR to editable contract

The `.pyi` printer works from semantic IR rather than wrapper syntax nodes:

```bash
python3 prik/printers/pyi.py
```

```text
Semantic module: printer_demo
from prik.contracts import Float64, bind

@bind("DOUBLE_VALUE")
def double_value(
    value: Float64
) -> Float64: ...
```

It derives required contract imports and preserves the native binding name in
editable Python syntax. Printing does not complete or attach wrapper policy;
the emitted contract can be edited and loaded through the `.pyi` pipeline.

Primary evidence:

- `tests/fortran/infrastructure/printers/`
- semantic `.pyi` round-trip tests in `tests/fortran/semantic_pyi_format/`
- generated-source goldens in feature-local `printers/` and `codegen/` owners
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`

Start formatting or node-serialization changes in the language printer that
owns that representation. If required information is absent from a node, add
it to generation or the plan rather than consulting semantic IR from a native
source printer. Filename, multi-source ordering, and returned artifact changes
belong to the wrapper pipeline.

## Workflow Pipeline

`prik/pipeline/` composes complete workflows across established stage
boundaries. It may decide which stage runs next, preserve progress/timing,
assign artifact filenames, write generated payloads, and coordinate compilation
and linking. It does not absorb parser grammars, semantic rules, policy
decisions, backend lowering, printer formatting, or compiler command mechanics.

| Important file | Responsibility |
| --- | --- |
| `pyi.py` | Loads semantic `.pyi` text/files/path sets, caches conversion, reconciles external types, supplies opaque dependency modules, completes copies, and emits stub packages. |
| `type_mapping_report.py` | Runs target probes through semantic conversion and codegen dtype projection to produce an auditable target-specific Markdown report. |
| `wrapper.py` | Freezes and validates one plan, renders docstrings, invokes both node generators and printers, assigns stable names, and returns `GeneratedWrapper`. |
| `build.py` | Owns public source/`.pyi` build APIs, generated-file writing, native input plans, dependency-ready compilation, linking, manifests, and `WrapperBuildResult`. |

The package initializer describes the high-level namespace but intentionally
does not flatten all of these substantial workflows. Source preprocessing and
target measurement remain in `preprocessing`; reusable command execution
remains in `compiler`.

### `pipeline/pyi.py`: combined contract loading

This example crosses the intentionally separate parser, converter, policy, and
printer stages through one loader workflow:

```bash
python3 prik/pipeline/pyi.py
```

```text
Loaded semantic module: math
Loaded contract marker: True
Functions: scale
Re-emitted module:
from prik.contracts import Float64

def scale(
    value: Float64
) -> Float64: ...
```

The loaded module retains workflow metadata. Stub emission deep-copies it,
completes policy on the copy, and uses the semantic printer, so the caller's
original editable semantic graph is not repurposed as a wrapper plan.

### `pipeline/type_mapping_report.py`: end-to-end datatype explanation

The report pipeline connects a measured native type to semantic and NumPy
representations:

```bash
python3 prik/pipeline/type_mapping_report.py
```

```text
| `int` | signed 32-bit | `Int (Int32 storage)` | `numpy.int32` |
```

The exact width is target-dependent. The four columns make the stage changes
explicit: native spelling, probed target fact, stable semantic identity with
resolved storage, and codegen NumPy expression. This example requires `cc`.

### `pipeline/wrapper.py`: plan to rendered artifact

`WrapperGenerator` is the single owner of the plan-to-text workflow:

```bash
python3 prik/pipeline/wrapper.py
```

```text
Extension initializer: PyInit_generator_demo
Rendered sources: bind_c_generator_demo_wrapper.f90, generator_demo_wrapper.c, generator_demo_wrapper.h
Native support: binding_support
```

The result is a `GeneratedWrapper` containing source payloads, stable paths,
compile-source grouping, required headers/support, and initializer identity.
Nothing has been written or compiled yet.

### `pipeline/build.py`: source to imported extension

The build example uses the public API to create and call a small extension:

```bash
python3 prik/pipeline/build.py
```

```text
scale(3.0, 2.5) = 7.5
```

Behind this concise result, the workflow preprocesses and parses source,
measures required target facts, constructs semantic IR, completes policy,
plans and renders the wrapper, writes temporary generated/native sources,
compiles dependency-ready objects, links an extension, imports it through
`WrapperBuildResult`, and calls the generated Python API. It requires the
configured C and Fortran compilers. The central example test retains the
`fortran_end_to_end` marker for this reason.

Primary evidence:

- `tests/fortran/semantic_pyi_format/pipeline/`
- `tests/fortran/data_types/pipeline/`
- `tests/fortran/infrastructure/pipeline/`
- `tests/fortran/building_shared_library/pipeline/`
- `tests/fortran/building_shared_library/compiling/`
- `tests/fortran/building_shared_library/end_to_end/`
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`

Start `.pyi` batch/cache/dependency behavior in `pyi.py`, cross-stage datatype
reporting in `type_mapping_report.py`, plan validation/artifact assembly in
`wrapper.py`, and disk/compiler/link/manifest behavior in `build.py`. A pipeline
helper should delegate a domain rule to its owning stage instead of becoming a
second implementation of that rule.

## Runtime and Bundled Native Support

`prik/runtime/` contains the Python objects that remain active after a generated
extension has been imported. Its important entry file, `handles.py`, turns the
small operation dictionaries exported by generated bindings into stable
`AllocatableArray` and `PointerArray` APIs. It validates descriptor metadata,
retains required owners, adapts operation signatures, and exposes live NumPy
views according to completed policy. It does not decide ownership or invent
operations absent from the plan.

`prik/runtime/native_support/` owns the header-only native runtime payload used
by generated bindings. Its Python initializer marks the payload as a package so
`compiler/native_support.py` can locate and install it. The generated build
still receives a `binding_support/` directory because that is the logical
include name emitted by the C binding backend; it is not the source package's
architectural location. These headers are native implementation assets, not an
independent Python workflow, so the folder intentionally has no `python3`
example.

| Important file | Responsibility |
| --- | --- |
| `runtime/handles.py` | Adapts generated descriptor operations into validated allocatable/pointer handle objects and NumPy views. |
| `runtime/native_support/prik_binding.h` | Defines the header-only capsule, array-validation, release, and Python/NumPy conversion runtime used by generated C bindings. |
| `compiler/native_support.py` | Locates the runtime payload and installs it as generated `binding_support/`; its direct example was shown in Compiler Services. |

### `runtime/handles.py`: generated operations to a stable handle

The example provides the same kind of raw callable dictionary that a generated
extension installs:

```bash
python3 prik/runtime/handles.py
```

```text
Runtime handle: AllocatableArray
Descriptor kind: allocatable
Initial view: [1.0, 2.0, 3.0]
Resized shape: (4,)
Generated resize received NumPy extents: True
```

The adapter selected `AllocatableArray` from the completed descriptor kind,
validated the declared dtype and rank, and converted `resize(4)` into the
generated operation's scalar `numpy.int64` extent convention. `to_numpy()`
returned the operation-provided live storage rather than a detached snapshot.
Consequently, callers must discard or copy outstanding views before native
deallocation, reallocation, or pointer reassociation; PRIK cannot revoke an
already exposed NumPy view.

Primary evidence:

- `tests/fortran/allocatables/runtime/`
- `tests/fortran/pointers/runtime/`
- `tests/fortran/memory_management/runtime/`
- `tests/fortran/infrastructure/runtime/`
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`

Start handle protocol, validation, owner-retention, and operation-adapter
changes in `runtime/handles.py`. Start header discovery or installation changes
in `runtime/native_support/` and `compiler/native_support.py`, respectively. A
new ownership or view policy belongs in post-IR policy first; runtime should
only enforce the completed choice.

## Shared Naming and Utilities

`prik/naming/` owns names whose stability and collision rules are shared across
planning and code generation. `prik/utilities/` contains small mechanisms that
are genuinely independent of a compiler stage. Neither folder owns semantic
policy, syntax grammar, or workflow orchestration.

| Important file | Responsibility |
| --- | --- |
| `naming/policy.py` | Normalizes public Python names, reserves namespace entries, and allocates language-safe generated names. |
| `naming/native_symbols.py` | Compacts long owner identities into deterministic, compiler-safe native symbol fragments. |
| `utilities/declaration_expressions.py` | Translates, validates, resolves, evaluates, and renders declaration extents across stage boundaries. |
| `utilities/strings.py` | Supplies minimal collision-safe generated-string helpers. |
| `utilities/visitor.py` | Supplies class-MRO dispatch shared by parsers, semantic converters, generators, and printers. |

### `naming/policy.py`: public and target-language names

```bash
python3 prik/naming/policy.py
```

```text
Normalized public name: render_value
Collision-safe public name: render_value_2
C destructor symbol: state_drop
```

The first two lines show that Python-visible normalization and collision
reservation are namespace-aware. The final line shows a separate lowering rule:
a Python destructor is translated and prefixed into a valid C symbol. These are
naming decisions, not emitted C syntax.

### `naming/native_symbols.py`: stable compact identities

```bash
python3 prik/naming/native_symbols.py
```

```text
Owner identity: geometry.point.coordinates
Stable native symbol: point_coordinate_d_c2fc5940
Within 27-character limit: True
```

The readable prefix assists generated-source inspection; the checksum retains
the full owner identity's contribution when the preferred spelling must be
shortened. Repeated calls with the same inputs return the same symbol.

### `utilities/declaration_expressions.py`: one extent across stages

```bash
python3 prik/utilities/declaration_expressions.py
```

```text
Fortran extent: ubound(source, 1) - lbound(source, 1) + 1
Public expression: source.shape[0]
Role-bound expression: __prik_extent_source_0
Fortran rendering: native_source_extent_0
Compile-time product: 6
```

This is deliberately a staged utility: a source expression becomes public
semantic syntax, then a validated role token, then backend text using a
plan-supplied substitution. Rendering does not rediscover which argument owns
the extent. The independent final line demonstrates compile-time integer
evaluation used while resolving declarations.

### `utilities/strings.py`: collision-safe local identifiers

```bash
python3 prik/utilities/strings.py
```

```text
First available name: temporary_4
Next counter: 5
```

The helper skips occupied candidates and returns both the selected name and the
next counter, allowing an emitter to allocate further local names without
rescanning from the beginning.

### `utilities/visitor.py`: explicit model dispatch

```bash
python3 prik/utilities/visitor.py
```

```text
Exact handler: literal:42
MRO fallback: expression:Expression
```

The dispatcher first selects an exact `<prefix>_<ClassName>` handler and then
walks the model class MRO for an intentional base-model fallback. Each consumer
still defines its own handlers; this utility does not merge the C, Fortran,
semantic `.pyi`, codegen, or printer visitor responsibilities.

Primary evidence:

- `tests/fortran/infrastructure/naming/`
- `tests/fortran/infrastructure/utilities/`
- `tests/fortran/arrays/semantics/test_declaration_expression_utilities.py`
- `tests/fortran/infrastructure/execution_examples/test_execution_examples.py`

Start public normalization and language-rule changes in `naming/policy.py`,
stable owner-derived ABI fragments in `naming/native_symbols.py`, and only
stage-neutral mechanisms in `utilities/`. If a helper begins consulting a
completed policy or choosing a backend behavior, move that responsibility to
the owning policy, planning, or generation stage.

## Contributor Documentation

All project-maintenance material lives under `docs/developer/`, presented in
the site navigation as **Contributor Documentation**. There is no separate
maintainer audience or `docs/maintainer/` tree: contributors need the same
architecture, testing, release, internal-design, and roadmap information.

| Area | Responsibility |
| --- | --- |
| `docs/user/` | Installation, usage, language support, tutorials, reference material, troubleshooting, and documented limitations for wrapper users. |
| `docs/developer/architecture.md` | Canonical package map, stage ownership, direct execution examples, change routes, and evidence owners. |
| `docs/developer/contributing/` | Contribution workflow, code of conduct, and security guidance. |
| `docs/developer/design/` | Detailed design constraints and rationale that supplement this package map. |
| `docs/developer/internal-architecture/` | Maintained implementation details for cross-stage internals. |
| `docs/developer/roadmap/` | Explicit planned or incomplete work, kept separate from implemented behavior. |
| `docs/developer/testing-strategy.md` | Test ownership, markers, focused-suite selection, and verification rules. |
| `docs/developer/development-workflow.md` | Local environment, edit, validation, and review workflow. |
| `docs/developer/release-process.md` | Maintainer release procedure within the shared contributor corpus. |

The executable snippets in this guide are production-owned examples. Their
output contracts are grouped in
`tests/fortran/infrastructure/execution_examples/test_execution_examples.py`, with one
explicitly named test per demonstrated file. This keeps documentation tests
focused on links, structure, and publication while making code-output drift
fail beside the stage and feature suites.

When adding another important entry file, give it a small real public-API flow
under `if __name__ == "__main__"`, document its command, representative output,
and architectural meaning here, then add
`test_fortran_<folder>_<file>_execution_example` to the central inventory. Do
not add an example merely to enumerate every helper file.
