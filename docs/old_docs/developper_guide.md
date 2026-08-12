---
title: Developer Guide
audience: contributors, maintainers
prerequisites: repository checkout, Python 3.10 or newer
related: developer-guide/index.md, quality.md
status: maintained
---

# Developer Guide

This guide is for changing prik. It maps user-visible behavior to its owning
implementation and tests, then gives focused change and verification
workflows.

Use the [tutorial](tutorial.md) and [examples cookbook](examples.md) to inspect
the public workflows before changing them. This guide is the maintainer entry
point for the C and Fortran parser references, implementation ownership, and
the detailed maintained contracts.

## Start Here

Install the project and QA dependencies:

```bash
python3 -m pip install -e ".[qa]"
```

Run the smallest relevant test while iterating, then run the full suite:

```bash
PYTHONPATH=. python3 -m pytest -q tests/parser/test_cli.py
PYTHONPATH=. python3 -m pytest -q
```

Before changing a public behavior, trace it through these layers:

```text
public command or Python API
  -> owning parser or CLI entrypoint
  -> parser model
  -> semantic conversion, when applicable
  -> .pyi printer/loader, when applicable
  -> policy completion and wrapper planning, when wrapping
  -> Fortran bridge, CPython binding, native build, and runtime tests, when wrapping
  -> focused tests and maintained reference docs
```

For example, a new CLI stage option normally requires:

1. A focused contract test in `tests/parser/test_cli.py`.
2. Dispatch or output routing in `prik/cli.py`.
3. Preprocessing tests if the option changes source loading.
4. A copy-paste command in [examples.md](examples.md).
5. A tutorial update only when the main user workflow changes.

## Support Evidence Rule

Documentation must describe implemented behavior, not intended behavior.
Treat a support claim as established only when it is traceable to current
implementation plus one of these forms of evidence:

- a focused test that proves the contract;
- a maintained fixture test that proves generated output;
- a repository command that has been run against a checked fixture;
- an explicit parser or semantic reference inventory backed by tests.

Use these documentation roles consistently:

| Document | Role |
| --- | --- |
| [tutorial.md](tutorial.md) | Main supported user workflow and boundaries |
| [examples.md](examples.md) | Copy-paste commands and Python API recipes |
| [fortran_wrapper.md](fortran_wrapper.md) | Implemented Fortran runtime contract, mechanism, ownership, and build modes |
| [c_parser.md](c_parser.md) | Maintainer inventory for the C frontend |
| [fortran_parser.md](fortran_parser.md) | Maintainer inventory for the Fortran frontend |
| [semantics.md](semantics.md) | Accepted semantic IR and datatype contract |
| [pyi_format.md](pyi_format.md) | User-visible semantic `.pyi` syntax and roadmap |
| [wrapper_design_notes.md](wrapper_design_notes.md) | Clearly deferred wrapper policy, not current native binding support |

When adding a user example:

1. Prefer a checked repository fixture or a short inline source string.
2. Run the command or snippet from the repository root.
3. Add or identify the focused test that owns the behavior.
4. State limitations next to the example when metadata is preserved but not
   executed, such as `@native_call` projection metadata.
5. Distinguish the implemented source-driven Fortran wrapper from deferred
   workflows such as C-input wrapping, direct edited-`.pyi` CLI builds, and
   arbitrary Pythonic projection execution.

### Automatically Verify Markdown Examples

`tests/tools/test_documentation_examples.py` executes explicitly marked
`bash` CLI examples and `python` API snippets from `README.md` and Markdown
files under `docs/`. Bash examples must be `python3 -m prik` or
`python3 -m prik.type_mapping_report` commands; the test replaces `python3`
with the active test interpreter and runs them without a shell. It rejects
shell operators, output-writing options, and options that select custom
executables or preprocessing command templates. Python snippets run with the
active test interpreter.

Wrapper examples that need native compilation should use
`build_fortran_extension` with `TemporaryDirectory` so verification does not
leave build artifacts in the checkout.

Mark a command that only needs to exit successfully:

````markdown
<!-- prik-doc-test: run -->
```bash
python3 -m prik semantics tests/data/fortran/general/basic_subroutine.f90
```
````

Mark a command whose stdout must match the documentation exactly:

````markdown
<!-- prik-doc-test: exact -->
```bash
python3 -m prik parse tests/data/fortran/general/basic_subroutine.f90
```

<!-- prik-doc-test-output -->
```text
File: tests/data/fortran/general/basic_subroutine.f90
...
```
````

Use exact checks for stable human-readable output. Use run checks for large
JSON or semantic payloads whose detailed contract is already covered by
focused tests. The same markers can precede a `python` fenced block. Do not
mark placeholder commands, snippets that modify the checkout,
environment-dependent compiler recipes, or intentionally failing diagnostic
examples.

When a command reads a checked fixture, include its source input in the user
documentation and verify the displayed source against the fixture:

````markdown
<!-- prik-doc-source: tests/data/fortran/general/basic_subroutine.f90 -->
```fortran
module m1
...
end module m1
```
````

Append a target profile to an exact marker only for compiler-generated output
that is intentionally architecture-specific:

```markdown
<!-- prik-doc-test: exact linux-x86_64 -->
```

Off-target checks are skipped. The matching profile must still run the command
and compare its complete output.

Run the documentation checks directly:

```bash
PYTHONPATH=. python3 -m pytest -q tests/tools/test_documentation_examples.py
```

## References

- [Tutorial](tutorial.md): supported end-to-end user workflow and current
  boundaries.
- [Verified examples cookbook](examples.md): CLI and Python API recipes.
- [C parser reference](c_parser.md): C frontend scope, preprocessing and
  project policy, parser architecture, CLI behavior, semantic handoff,
  fixtures, and tests.
- [Fortran parser reference](fortran_parser.md): Fortran frontend scope,
  recursive parser organization, API/CLI behavior, diagnostics, fixture
  workflow, semantic handoff, and tests.
- [Semantic IR reference](semantics.md): shared semantic model, datatype
  policy, and C conversion facts.
- [Semantic `.pyi` format](pyi_format.md): user-visible `.pyi`
  loader/printer contract and roadmap.
- [Wrapper design notes](wrapper_design_notes.md): wrapper-generation policy
  questions intentionally deferred until wrapper implementation.
- [Semantic multilanguage wrapper runtime architecture](architecture/semantic_multilanguage_wrapper_runtime_architecture.md):
  long-term architecture and runtime model.
- [Quality assurance](quality.md): active QA commands, tool benefits, known
  defects found by each tool, and scheduled triage process.

## User-Facing Contract Internals

The tutorial, examples cookbook, `.pyi` format, and semantic reference describe
CLI stages, `.pyi` syntax, datatype names, and wrapper-plan diagnostics. The developer
task is to keep those user-visible contracts stable, tested, and traceable to
implementation files.

### Source Ownership Map

| User-visible area | Main implementation files | Main tests |
| --- | --- | --- |
| Fortran parse output | `prik/fortran_parser/parser.py`, `prik/fortran_parser/models.py`, `prik/fortran_parser/lexer.py` | `tests/parser/test_procedure_and_type_parsing.py`, `tests/parser/test_fortran_fixture_suite.py`, `tests/parser/test_error_handling.py` |
| C parse output | `prik/c_parser/parser.py`, `prik/c_parser/models.py`, `prik/c_parser/lexer.py` | `tests/parser/c/test_c_declarations_and_declarators.py`, `tests/parser/c/test_c_fixture_suite.py`, `tests/parser/c/test_c_error_fixture_suite.py` |
| CLI stage selection and output | `prik/cli.py`, `prik/fortran_parser/cli.py` | `tests/parser/test_cli.py` |
| Compiler preprocessing | `prik/preprocessing.py` | `tests/parser/test_preprocessing_cli.py`, `tests/parser/test_preprocessor_and_execution_boundaries.py`, `tests/parser/c/test_c_lexer_preprocessor.py` |
| C target ABI probing and cache | `prik/c_type_probe.py` | `tests/parser/test_c_standard_type_probe.py` |
| Fortran target type probing and cache | `prik/fortran_type_probe.py` | `tests/parser/test_fortran_type_probe.py` |
| Generated target datatype mapping examples | `prik/type_mapping_report.py` | `tests/tools/test_type_mapping_report.py`, `tests/tools/test_documentation_examples.py` |
| Fortran to semantic IR | `prik/semantics/fortran2ir.py`, `prik/semantics/models.py` | `tests/semantics/test_fortran2ir.py` |
| C to semantic IR | `prik/semantics/c2ir.py`, `prik/semantics/models.py` | `tests/semantics/test_c2ir.py` |
| `.pyi` printing | `prik/printers/pyi.py` | `tests/semantics/test_pyi_printer.py`, `tests/semantics/test_pyi_printer_modern_example.py` |
| `.pyi` loading/editing | `prik/pyi_parser/parser.py` | `tests/pyi/test_pyi_to_ir.py`, `tests/pyi/test_pyi_fixture_suite.py` |
| Fortran wrapper orchestration | `prik/wrapping.py` | `tests/wrapper/fortran/native_build/test_build_modes.py`, `tests/wrapper/fortran/multi_source/test_multi_source_builds.py` |
| Wrapper planning and owner-local errors | `prik/planning/planner.py` | `tests/codegen/` |
| Semantic IR to codegen AST | `prik/semantics/ir2ast.py` | `tests/semantics/test_ir2ast.py`, `tests/wrapper/` |
| Fortran-to-C bridge and CPython binding | `prik/codegen/bridges/fortran_to_c.py`, `prik/codegen/bindings/c_to_python.py` | `tests/wrapper/` subject suites |
| Native compilation and binding support | `prik/compiling/`, `prik/binding_support/` | `tests/wrapper/fortran/native_build/test_runtime_abi.py`, `tests/wrapper/fortran/native_build/test_build_modes.py` |
| Public API exports | `prik/__init__.py` | `tests/parser/test_parser_public_entrypoints.py`, `tests/parser/c/test_c_public_api_skeleton.py` |
| Executable Markdown examples | `README.md`, `docs/*.md` | `tests/tools/test_documentation_examples.py` |

### Codegen Class Organization

Current runtime wrapper codegen is intentionally narrow: Fortran sources lower
through the generated Fortran bridge, generated C, and the CPython extension
binding. Semantic `.pyi` emission is the editable contract printer. Do not keep
placeholder C++, pybind11, or Python source printers in `prik/codegen` until
those backends have a documented runtime contract and tests.

Organize generators and printers using `FortranParser` in
`prik/fortran_parser/parser.py` as the structural reference. A maintainer
should be able to read each class from top to bottom in the same order that
data moves through it:

1. The class docstring states the class's responsibility and lists its method
   sections.
2. Construction and public entrypoints come first.
3. Dispatched model handlers follow, grouped by feature and pipeline order.
   Their names use the class's configured visitor prefix, for example
   `_visit_<ModelType>`, `_print_<ModelType>`, or `_parse_<ModelType>`.
4. Helpers immediately follow the visitor group that owns them, or appear in
   a final low-level helper section when several visitor groups share them.
5. Every method has a short contract docstring. The docstring explains the
   method's purpose or invariant; it does not restate its name.

Use the same visible section banners as `FortranParser`, for example
`Public entrypoints`, `Module visitors`, `Function visitors`, and `Shared
helpers`. Keep related visitors adjacent instead of sorting methods merely by
name.

All model-type dispatch goes through the class's `_visit` entrypoint and the
class's configured visitor prefix. Use an explicit dispatch table for a second
dispatch dimension such as datatype or ownership action. Do not add a second
independent visitor family, dynamic method name, or scattered `isinstance`
dispatch schemes. A method that performs ordinary work but is not a dispatch
target must have a descriptive helper name rather than a visitor-shaped name.

Keep functionality on the class that owns its state and policy. A module-level
function is justified only when it is a deliberate public functional API or a
genuinely stateless utility shared by unrelated classes. Do not retain a
module-level function only to preserve an old internal call path.

### `.pyi` Contract Internals

User-visible `.pyi` syntax is parsed by `prik/pyi_parser/parser.py` and printed
by `prik/printers/pyi.py`. Both operate on `prik/semantics/models.py`.

Important implementation rules:

- `Addr(T)` and `Addr(T)` are storage contracts, not just pretty syntax.
- Array subscriptions such as `Float64[n]` are semantic array contracts.
- `Annotated[..., ORDER_F]`, `ORDER_ANY`, `Allocatable`, `Pointer`, and
  output behavior is represented by storage and projected returns.
- `Final[T]` is the public constant spelling. Do not reintroduce
  `Constant` as user-facing `.pyi` syntax.
- `@native_call` is projection metadata. Use it only when the Python-visible
  signature intentionally differs from the native signature.
- Generated stubs should describe exact native contracts unless semantic IR
  explicitly carries projection metadata.

When changing `.pyi` syntax:

1. Add or update parser tests in `tests/pyi/test_pyi_to_ir.py`.
2. Add or update printer tests in `tests/semantics/test_pyi_printer.py`.
3. Update fixture tests only if the public generated contract changes.
4. Update [tutorial.md](tutorial.md) or [examples.md](examples.md) if users
   need to write or read the new syntax.
5. Update [pyi_format.md](pyi_format.md) for the full user-facing reference.
6. Update [semantics.md](semantics.md) if the underlying semantic IR contract
   changes.

### Datatype Mapping Internals

User-visible datatype names are semantic names, not raw parser spellings.
Mapping happens during parser-to-IR conversion:

- Fortran intrinsic/kind mapping and compiler storage-fact application live in
  `prik/semantics/fortran2ir.py`.
- C primitive, typedef, and probe-aware mapping lives in `prik/semantics/c2ir.py`.
- The shared dtype names and storage contracts live in `prik/semantics/models.py`.
- Compiler-measured mapping snapshots are generated by
  `prik/type_mapping_report.py`.

When changing datatype mapping:

1. Add focused conversion tests in `tests/semantics/test_fortran2ir.py` or
   `tests/semantics/test_c2ir.py`.
2. Add `.pyi` printer/loader coverage if the emitted syntax changes.
3. Update semantic fixtures only when serialized semantic IR intentionally
   changes.
4. Update [semantics.md](semantics.md), plus
   [tutorial.md](tutorial.md) or [examples.md](examples.md) when the visible
   user workflow or examples change.
5. Regenerate and update the exact target mapping snapshots in
   [semantics.md](semantics.md). The executable documentation test must match
   the complete output of:

   ```bash
   python3 -m prik.type_mapping_report --language c
   python3 -m prik.type_mapping_report --language fortran
   ```

For Fortran, keep both modern and legacy spellings in the generated report.
Legacy numeric `type*N` forms carry fixed total storage; compiler-dependent
default, kind, `DOUBLE PRECISION`, and `DOUBLE COMPLEX` forms use probe facts.

### Wrapper-Plan Support Diagnostics

Parser models record source facts and diagnostics. Semantic conversion rejects
source facts that cannot form a contract, while wrapper planning rejects
unsupported completed policy.

When adding an unsupported policy path, add a focused semantic-conversion or
wrapper-planning diagnostic test.

### Parser To Wrapper Boundary

Do not move wrapper policy into parsers. Parsers can preserve:

- source locations;
- declaration and signature facts;
- type, pointer, array, callback, and aggregate facts;
- preprocessor provenance and diagnostics;
- unresolved references.

Post-IR policy completion and wrapper planning decide:

- ownership and lifetime;
- callback registration/unregistration policy;
- output-buffer projection;
- hidden pointer/size projection;
- ABI shim requirements;
- Python-visible signature adaptation.

## Pipeline Internals

The user-facing stages all start in `prik/cli.py`, but each stage owns a
different layer of the pipeline.

```text
CLI args
  -> language resolution
  -> preprocessing config and source loading
  -> parser models
  -> semantic IR
  -> inspection: .pyi printing / .pyi loading
  -> Fortran build: codegen AST / native bridge / CPython binding / extension
```

### CLI And Language Resolution

`prik/cli.py` is the shared command-line entrypoint. It is responsible for:

- choosing Fortran or C from `--language` and file suffixes;
- rejecting ambiguous directories and unknown suffixes without `--language`;
- building `PreprocessingConfig`;
- dispatching the requested stage flags;
- defaulting recognizable Fortran sources to a wrapper build when no stage is
  selected;
- routing the default build and `--makefile` through `prik/wrapping.py`;
- routing text, JSON, and `--out` output.

Recognizable Fortran files and `.pyi` wrapper inputs can omit `--language`.
C files and directories require explicit language selection. Keep this behavior
tested in `tests/parser/test_cli.py` whenever stage selection changes.

The package-specific `prik/fortran_parser/cli.py` remains for the Fortran parser
package entrypoint. New cross-language user behavior normally belongs in
`prik/cli.py`.

### Preprocessing Internals

`prik/preprocessing.py` owns compiler-backed preprocessing and provenance. The
main value object is `PreprocessingConfig`; the main execution path is
`run_compiler_preprocessor_with_recipe(...)`.

Important contracts:

- CLI source parsing uses compiler mode. C defaults to `cc`; Fortran defaults
  to `gfortran` unless the user passes a compiler, compile database, or custom
  template.
- C direct parser entrypoints can still be used on raw strings or already
  controlled source in Python tests.
- The preprocessing recipe is part of the parser payload when preprocessing
  happened. It records compiler, adapter, argv, include directories, defines,
  undefs, standard, extra compiler args, included files, source mappings, and
  diagnostics.
- C preprocessing uses GCC/Clang-style `-E -x c` for direct compiler mode.
  Fortran direct compiler mode uses `-E -cpp` plus source-form hints where
  needed.
- Native Fortran `include "..."` is expanded after compiler CPP output because
  it is Fortran textual inclusion, not C/CPP include semantics.

When changing preprocessing behavior, update
`tests/parser/test_preprocessing_cli.py`, source-boundary tests in
`tests/parser/test_preprocessor_and_execution_boundaries.py`, and C raw
directive tests in `tests/parser/c/test_c_lexer_preprocessor.py`.

### Source Loading To Semantic IR Paths

Keep source loading, parser models, and semantic conversion separate. Semantic
converters accept parsed models; they must not hide compiler preprocessing or
source loading inside conversion helpers.

Fortran direct Python API, no CPP/FPP macros:

```python
from prik import parse_fortran_file
from semantics.fortran2ir import fortran_module_to_semantic_module

parsed = parse_fortran_file(source, filename="visibility_mod.f90")
semantic = fortran_module_to_semantic_module(parsed.modules[0])
```

`parse_fortran_file(...)` runs the parser's internal line preparation:
source-form detection, comment stripping, and continuation folding. It does
not expand `#define`, `#ifdef`, or other CPP/FPP directives. Raw CPP/FPP
directives are rejected with `PARSE_PREPROCESSING_REQUIRED`.

Fortran with macros or textual configuration must be compiler-preprocessed
before parsing:

```python
from pathlib import Path

from prik import parse_fortran_file
from semantics.fortran2ir import fortran_file_to_semantic_modules
from prik.preprocessing import PreprocessingConfig, preprocess_source

path = Path("configured.F90")
preprocessed = preprocess_source(
    path,
    language="fortran",
    config=PreprocessingConfig(
        mode="compiler",
        compiler="gfortran",
        defines=["USE_MPI", "N=32"],
        include_dirs=["include"],
    ),
)

parsed = parse_fortran_file(preprocessed.source, filename=str(path))
modules = fortran_file_to_semantic_modules(parsed)
```

Choose the Fortran semantic helper from the parser model shape:

- `fortran_module_to_semantic_module(parsed.modules[0])` for one selected
  module.
- `[fortran_module_to_semantic_module(m) for m in parsed.modules]` when a file
  contains multiple modules and no top-level standalone procedures matter.
- `fortran_file_to_semantic_modules(parsed, standalone_module_name=...)` when
  top-level procedures should become a synthetic semantic module too.
- `fortran_project_to_semantic_modules(project)` when project-level module and
  derived-type context matters.

Fortran `parameter` values and kind expressions are not CPP macros. If the
parser leaves a Fortran compile-time expression symbolic, collect missing
values with `collect_semantic_compile_time_requirements(parsed)`, evaluate
them with the target compiler or a reusable type report, and pass
`compile_time_values=...` to the semantic converter. The shared CLI semantic
stage performs this target probing when a Fortran compiler or report is
configured; direct API callers must do it explicitly.

C direct Python API, no macro expansion needed:

```python
from prik import parse_c_file
from semantics.c2ir import c_file_to_semantic_modules

parsed = parse_c_file("int add(int a, int b);", filename="api.h")
modules = c_file_to_semantic_modules(parsed)
```

C raw mode records include and pragma metadata and accepts simple include
guards. Macro-shaped directives such as `#if`, `#ifdef`, `#define` outside a
trivial include guard, and `#error` require compiler preprocessing and are
rejected with `CPARSE_PREPROCESSING_REQUIRED`.

C with macros follows the compiler-preprocessed path, then parses the expanded
translation unit in `compiler` or `preprocessed` mode:

```python
from pathlib import Path

from c_parser.cli import attach_preprocessing_recipe
from prik import parse_c_file
from semantics.c2ir import c_file_to_semantic_modules
from prik.preprocessing import PreprocessingConfig, preprocess_source

path = Path("api.h")
preprocessed = preprocess_source(
    path,
    language="c",
    config=PreprocessingConfig(
        mode="compiler",
        compiler="cc",
        defines=["API_EXPORT="],
        include_dirs=["include"],
    ),
)

parsed = parse_c_file(
    preprocessed.source,
    filename=str(path),
    preprocessing="compiler",
)
attach_preprocessing_recipe(parsed, preprocessed.recipe)
modules = c_file_to_semantic_modules(parsed)
```

The C semantic converter can turn recorded object-like numeric macros into
semantic constant variables. Function-like macros and untyped macro bodies are
not wrapper-callable declarations. Declarations that depend on macros which
were recorded but not expanded remain explicit semantic facts rather than
being treated as complete wrapper contracts.

For CLI code, do not reimplement these paths manually. `prik/cli.py` builds
the `PreprocessingConfig`, loads or preprocesses source, attaches C
preprocessing recipes, parses, runs target type probes when configured, and
then dispatches to the semantic helpers.

### Semantic, `.pyi`, Wrapper-Planning, And Type-Probe Paths

The semantic stages share one rule: source inputs become semantic IR before
anything emits `.pyi` or builds a wrapper plan. Edited `.pyi` inputs are already a
semantic contract and do not go back through C or Fortran parsing.

Input shapes are part of the contract:

- `parse_fortran_file(source_or_path, filename=...)` accepts inline source
  text. It reads from disk only when `source_or_path` names an existing file
  and `filename` is omitted. Pass `filename` with inline text for diagnostic
  provenance.
- `parse_c_file(source_or_path, filename=...)` accepts inline source text or
  an existing file path. Existing paths are read from disk; `filename` can
  still override the diagnostic/source name.
- `parse_fortran_project(...)` and `parse_c_project(...)` accept an in-memory
  mapping of `filename -> source`, an explicit file/path list, or a directory.
  Fortran directory parsing discovers supported Fortran files and orders them
  by module dependencies. C directory parsing discovers supported C files and
  records include graph facts; include directives do not recursively open more
  files.
- `preprocess_source(path, language=..., config=...)` is path-based because it
  shells out to a compiler. Feed `preprocessed.source` to the parser afterward.
- `parse_pyi_text(...)` accepts inline `.pyi` source text and returns Python
  AST. `convert_pyi_to_ir(...)` converts that parsed AST to semantic IR.
  `pyi_text_to_semantic_module(...)`, `pyi_file_to_semantic_module(...)`, and `pyi_paths_to_semantic_modules(...)`
  combine parsing and conversion for inline text, one file, or a file set.
- The CLI accepts source, `.pyi`, and directory paths. It does not accept
  inline source text on the command line.

CLI source stages:

```text
source path(s)
  -> prik/cli.py language resolution
  -> PreprocessingConfig
  -> raw source or compiler-preprocessed source
  -> CFile / FortranFile parser model
  -> C or Fortran semantic IR
  -> optional .pyi emission
  -> optional `.pyi` emission or wrapper-plan build
```

CLI `.pyi` wrapper build:

```text
.pyi path(s) or directory
  -> pyi_paths_to_semantic_modules(...)
  -> SemanticModule list
  -> complete_semantic_policies(...)
  -> WrapperPlanner.build(...)
```

Generating `.pyi` from source is semantic conversion plus printing. In Python
API code, keep those calls visible:

```python
from prik import emit_module_stubs, parse_fortran_file
from semantics.fortran2ir import fortran_file_to_semantic_modules

parsed = parse_fortran_file(source, filename="api.f90")
modules = fortran_file_to_semantic_modules(parsed)
stubs = emit_module_stubs(modules)
```

For C, the same shape uses `parse_c_file(...)` or `parse_c_project(...)`,
then `c_file_to_semantic_modules(...)` or
`c_project_to_semantic_modules(...)`, then `emit_module_stubs(...)`.

Loading or editing `.pyi` is the opposite direction:

```python
from prik import pyi_paths_to_semantic_modules

modules = pyi_paths_to_semantic_modules("interfaces")
```

Use the `.pyi` helpers by input shape:

- `parse_pyi_text(source, filename=...)` from `prik.pyi_parser` for parser-only
  AST parsing.
- `convert_pyi_to_ir(tree, module_name=..., source=...)` for AST-to-IR
  conversion.
- `pyi_text_to_semantic_module(source, module_name=..., filename=...)` for inline text.
- `pyi_file_to_semantic_module(path, module_name=...)` for one file.
- `pyi_paths_to_semantic_modules(paths_or_directory)` for a set of interfaces that may
  reference each other.

Do not run compiler preprocessing, C ABI probes, or Fortran type probes for an
edited `.pyi` wrapper build. Once `.pyi` has been loaded, the edited semantic
IR is the source of truth.

Compiler preprocessing flags all flow through `PreprocessingConfig`:

| CLI flag | `PreprocessingConfig` field | Notes |
| --- | --- | --- |
| `--compiler` | `compiler` | Exact executable for direct preprocessing and automatic type probes. |
| `--compile-commands` | `compile_commands` | Project compile database; automatic C ABI probing is not allowed from this mixed recipe. |
| `--preprocessor-adapter` | `adapter` | Adapter family, including `command-template`. |
| `--preprocess-template` | `command_template` | Custom command; requires `--preprocessor-adapter command-template`. |
| `-I` / `--include-dir` | `include_dirs` | Passed to compiler preprocessing and native Fortran include expansion. |
| `-D` / `--define` | `defines` | Macro definitions for compiler preprocessing. |
| `-U` / `--undef` | `undefs` | Macro undefinitions for compiler preprocessing. |
| `--std` | `std` | Passed as `-std=...`. |
| `--compiler-arg` | `compiler_args` | Raw target/sysroot/compiler options. |
| `--public-include`, `--private-include`, `--include-exposure` | include exposure fields | Controls provenance exposure, not parser grammar. |

`preprocess_source(...)` returns expanded source and a recipe. The C parser
needs `preprocessing="compiler"` or `"preprocessed"` for that expanded source,
and CLI code attaches the recipe with `attach_preprocessing_recipe(...)` so
macro metadata can reach semantic conversion. Fortran consumes the expanded
source with `parse_fortran_file(...)`; the parse-stage CLI payload records the
recipe separately.

C target datatype mapping path:

```text
C source
  -> parse_c_project(...)
  -> optional C standard type report
  -> c_project_to_semantic_modules(..., standard_type_report=...)
```

For direct-compiler C semantic and `.pyi` stages, `prik/cli.py` runs
`probe_c_standard_types_cached(...)` internally and passes the facts to
`prik/semantics/c2ir.py`. The standalone report is an inspection output, not a
second semantic-stage input path. Probe execution and cache policy belong to
the probe implementation.

Fortran target datatype mapping and compile-time path:

```text
Fortran source
  -> parse_fortran_file(...)
  -> collect_semantic_compile_time_requirements(...)
  -> evaluate_fortran_type_requirements(...)
  -> collect_fortran_type_storage_requirements(...)
  -> evaluate_fortran_type_facts(...)
  -> fortran_module_to_semantic_module(..., compile_time_values=..., type_facts=...)
```

The CLI performs those probe steps internally for Fortran semantic, `.pyi`, and
wrapper-build stages when a direct Fortran compiler is configured.
`compile_time_values` resolve symbolic parameters and kind expressions.
`type_facts` measure compiler-dependent intrinsic storage, such as default
integer width or target-changing flags. Standalone reports are inspection and
verification outputs, not alternate semantic-stage inputs.

Generated datatype mapping reports are documentation and verification outputs,
not a separate parse path. `prik/type_mapping_report.py` uses the C and Fortran
converter/probe machinery to print target-specific mapping examples for
`docs/semantics.md`; changes there need both semantic conversion tests and
documentation-example verification.

### Fortran Runtime Wrapper Path

`prik/wrapping.py::build_fortran_extension(...)` is the public orchestration
boundary for direct Fortran builds. Keep its stages explicit:

```text
ordered source paths
  -> preprocess_source(..., language="fortran")
  -> parse_fortran_project(...)
  -> compile-time expression and storage probes
  -> fortran_project_to_semantic_modules(...)
  -> merge public semantic modules
  -> semantic_ir_to_codegen_ast(...)
  -> Codegen and create_shared_library(...)
  -> WrapperBuildResult
```

The main ownership boundaries are:

- `prik/wrapping.py`: source order, preprocessing/probing, semantic merge,
  output placement, direct-versus-Makefile mode, and artifact reporting;
- `prik/semantics/ir2ast.py`: semantic contract validation and conversion to
  codegen models;
- `prik/codegen/bridges/fortran_to_c.py`: Fortran-to-C ABI adaptation;
- `prik/codegen/bindings/c_to_python.py`: Python argument/result conversion,
  reference handling, and CPython wrapper construction;
- `prik/printers/{c,fortran,pyi}.py`: language source rendering only;
- `prik/compiling/`: compiler commands and shared-library linking; and
- `prik/binding_support/`: native binding support copied into each build.

Do not move semantic ownership or projection policy into printers. Do not infer
source dependencies: multi-source builds compile in caller order, and the first
semantic module names the merged extension. `--makefile` records the same
compiler/linker plan without executing it.

The current CLI build is Fortran-only. Edited `.pyi` files can drive a wrapper
build when provided with native implementation artifacts. User C inputs currently stop at
semantic conversion; their runtime backend is future work even though the
Fortran wrapper internally emits C source.

Runtime verification belongs in `tests/wrapper`. The subject index in
[`tests/wrapper/fortran/README.md`](../tests/wrapper/fortran/README.md) maps generated behavior
to compiled/imported tests. Build-mode changes should at least cover
`test_build_modes.py`, `multi_source/test_multi_source_builds.py`, and
the affected runtime subject test.

### Parser Model Internals

Parser models are source facts. They should answer "what did the source say?"
rather than "what Python wrapper should be generated?"

Fortran:

- `prik/fortran_parser/parser.py` slices the file into grammar units, then parses
  each unit's specification region.
- `prik/fortran_parser/models.py` stores `FortranFile`, modules, procedures,
  variables, derived types, interfaces, programs, submodules, and diagnostics.
- Execution bodies are intentionally skipped after the parser has enough
  signature/source facts.

C:

- `prik/c_parser/lexer.py` handles comments, directives, top-level splitting, and
  token source locations.
- `prik/c_parser/parser.py` visits declarations and declarators, records typed
  source facts, and reports unsupported parser-owned syntax.
- `prik/c_parser/models.py` stores functions, variables, typedefs, structs, unions,
  enums, includes, raw directives, preprocessing facts, and diagnostics.

Adding parser fields is a schema decision. Add fields only when downstream
semantic conversion, fixtures, diagnostics, or user-visible behavior need a
new fact.

### Semantic IR Internals

The semantic layer normalizes C and Fortran facts into language-neutral models
from `prik/semantics/models.py`.

- `prik/semantics/fortran2ir.py` maps Fortran procedures, derived types, module
  variables, kinds, shapes, storage contracts, visibility, imported references,
  and compile-time values.
- `prik/semantics/c2ir.py` maps C functions, variables, structs/opaque structs,
  enums, typedef chains, standard-type probe facts, macros, pointer/array
  storage, and C-specific semantic facts.
- C `int` keeps the semantic name `Int` while its compiler-probed concrete
  precision is stored on the semantic type. C and Fortran enums lower to
  unscoped module-level integer constants; enum names are metadata, not
  semantic datatypes.
- Named data bindings share a common base but keep role-specific types:
  `SemanticVariable` for module/global variables and macro constants,
  `SemanticArgument` for callable parameters, `SemanticField` for struct,
  union, and Fortran derived-type fields. `SemanticFunction.locals` is the
  reserved home for local variables or local constants if a frontend later
  promotes them into semantic IR; local bindings are not emitted into `.pyi` or
  treated as wrapper interface items by default.
- `prik/printers/pyi.py` emits editable user contracts.
- `prik/pyi_parser/parser.py` loads edited contracts back into semantic IR.
- `prik/policy/completion.py` completes the decisions required for
  wrapping.

Keep semantic IR stable where possible. If a parser change does not affect the
semantic contract, avoid changing semantic fixtures.

### `.pyi` Projection Internals

`@native_call` is stored as projection metadata on `SemanticFunction`. The
loader and printer currently support `Arg`, `Return`, ABI-typed literal calls
such as `Int32(1)`, `Len`, `IsPresent`, `Work`, and `.shape[...]` value
references. They do not currently
implement future wrapper projection helpers such as `Addr(Arg(...))`, `As[...]`,
status-return policy, ownership conversion, or coercion execution.

The test ownership is:

- loader syntax and error behavior: `tests/pyi/test_pyi_to_ir.py`;
- printer round-trip shape: `tests/semantics/test_pyi_printer.py`;
- wrapper-plan support diagnostics: `tests/codegen/`.

When adding projection syntax, first add loader tests that prove the accepted
syntax and rejected syntax. Then add policy or wrapper-plan tests only if the
new metadata affects those layers.

## Testing Strategy

Use the smallest test layer that proves the behavior, then add broader
coverage only when the public contract changes.

### Test Layers

| Layer | Purpose | Typical files |
| --- | --- | --- |
| Focused parser tests | One construct, diagnostic, or model field | `tests/parser/test_*.py`, `tests/parser/c/test_*.py` |
| Parser fixture goldens | Serialized parser contract over curated files | `tests/parser/test_fortran_fixture_suite.py`, `tests/parser/c/test_c_fixture_suite.py` |
| Semantic tests | Parser facts converted to wrapper-neutral IR | `tests/semantics/test_fortran2ir.py`, `tests/semantics/test_c2ir.py` |
| `.pyi` tests | Editable contract loader/printer behavior | `tests/pyi/test_pyi_to_ir.py`, `tests/semantics/test_pyi_printer.py` |
| Wrapper-plan tests | Completed-policy and unsupported-contract diagnostics | `tests/codegen/` |
| CLI tests | User commands, output routing, diagnostics | `tests/parser/test_cli.py`, `tests/parser/test_preprocessing_cli.py` |
| Wrapper build tests | Artifact placement, direct/Makefile modes, multi-source ordering | `tests/wrapper/fortran/native_build/test_build_modes.py`, `tests/wrapper/fortran/multi_source/` |
| Wrapper runtime tests | Imported extension behavior, ownership, lifetime, and failures | `tests/wrapper/` subject suites indexed by `tests/wrapper/fortran/README.md` |
| Property/fuzz tests | Broad parser robustness invariants | `tests/property/test_parser_properties.py`, `tests/property/test_semantic_properties.py` |

### Choosing Tests For A Change

- Parser-only source fact: focused parser test first; fixture golden only if
  serialized output changes intentionally.
- CLI flag or output change: CLI test first; update README/user docs if the
  visible command changes.
- New datatype mapping: semantic conversion test plus `.pyi` printer/loader
  tests if emitted syntax changes.
- New `.pyi` syntax: loader and printer tests, plus policy or plan tests when
  it changes a completed decision or lowering.
- New unsupported case: a semantic-conversion, policy, or wrapper-plan test at
  the stage that detects it.
- Preprocessing behavior: preprocessing CLI tests and at least one parser path
  that consumes the recipe.
- Wrapper orchestration or codegen behavior: the focused `tests/wrapper`
  build-mode or subject suite, including an imported runtime assertion rather
  than build success alone.

### Golden Fixture Rules

Do not regenerate broad fixture sets to hide uncertainty. First write or run a
focused test that explains the intended behavior. Then regenerate only the
affected fixture group when the serialized contract really changed.

Useful commands:

```bash
python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
python tests/parser/fortran/generate_fortran_parser_goldens.py tests/data/fortran/general/basic_subroutine.f90
python tests/semantics/generate_semantic_fixtures.py
python tests/pyi/generate_pyi_fixtures.py
```

### Coverage And CI Parity

When investigating coverage failures, mirror the GitHub Actions coverage flow
instead of relying on a plain local run:

```bash
COVERAGE_PROCESS_START=pyproject.toml PYTHONPATH=. coverage run -m pytest
python -m coverage combine
python -m coverage report
```

The `COVERAGE_PROCESS_START` environment variable matters because subprocess
CLI tests need the same coverage configuration as CI.

## Feature Change Walkthroughs

Use these walkthroughs when adding behavior. They are deliberately procedural:
change the smallest owned layer first, test that layer, then update downstream
contracts only when the public behavior actually changes.

### Add A C Declaration Feature

Example target: support a new declaration spelling or compiler extension in
the C parser.

1. Add the smallest source example to a focused C parser test:
   `tests/parser/c/test_c_declarations_and_declarators.py`,
   `tests/parser/c/test_c_compiler_extensions.py`, or
   `tests/parser/c/test_c_structs_unions_enums_typedefs.py`.
2. Implement the parser change in `prik/c_parser/parser.py`. Add or update model
   fields in `prik/c_parser/models.py` only if the serialized parser contract needs
   new facts.
3. If source splitting or raw directive handling changes, update
   `prik/c_parser/lexer.py` and `tests/parser/c/test_c_lexer_preprocessor.py`.
4. If project-level resolution changes, update
   `tests/parser/c/test_c_project_resolution.py`.
5. If parser JSON changes intentionally, regenerate the relevant project
   golden:

   ```bash
   python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
   ```

6. If the new parser fact affects semantic conversion, update
   `prik/semantics/c2ir.py` and add coverage in `tests/semantics/test_c2ir.py`.
7. If the generated `.pyi` changes, update `tests/semantics/test_pyi_printer.py`
   or `tests/pyi/test_pyi_fixture_suite.py`.
8. Update [c_parser.md](c_parser.md), [tutorial.md](tutorial.md),
   [examples.md](examples.md), or [semantics.md](semantics.md) if users or
   maintainers need to know the new behavior.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/parser/c/test_c_declarations_and_declarators.py
PYTHONPATH=. pytest -q tests/parser/c/test_c_project_resolution.py
PYTHONPATH=. pytest -q tests/semantics/test_c2ir.py
```

### Add A Fortran Parser Feature

Example target: preserve a new declaration attribute, source fact, or argument
metadata item.

1. Add a focused parser test in the file that owns the behavior:
   `tests/parser/test_procedure_and_type_parsing.py`,
   `tests/parser/test_scope_handling.py`, or
   `tests/parser/test_preprocessor_and_execution_boundaries.py`.
2. Implement parsing in `prik/fortran_parser/parser.py`. Add model fields in
   `prik/fortran_parser/models.py` only if the parser output needs to expose the
   new fact.
3. Add parser diagnostic coverage in `tests/parser/test_error_handling.py` if
   malformed source should now fail differently.
4. If project ordering, imports, or compile-time values change, update
   `tests/parser/test_project_scope_models.py` or
   `tests/parser/test_fortran_type_probe.py`.
5. If serialized parser JSON changes intentionally, regenerate the selected
   fixture:

   ```bash
   python tests/parser/fortran/generate_fortran_parser_goldens.py tests/data/fortran/general/basic_subroutine.f90
   ```

6. If the new fact affects semantic output, update `prik/semantics/fortran2ir.py`
   and `tests/semantics/test_fortran2ir.py`.
7. If generated `.pyi` changes, update `tests/semantics/test_pyi_printer.py`
   and the relevant fixture tests.
8. Update [fortran_parser.md](fortran_parser.md), [tutorial.md](tutorial.md),
   [examples.md](examples.md), or [semantics.md](semantics.md) as needed.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/parser/test_procedure_and_type_parsing.py
PYTHONPATH=. pytest -q tests/parser/test_fortran_fixture_suite.py
PYTHONPATH=. pytest -q tests/semantics/test_fortran2ir.py
```

### Add Or Change Datatype Mapping

Example target: map a new Fortran kind, C typedef, or target-probed C type.

1. Add conversion coverage in `tests/semantics/test_fortran2ir.py` or
   `tests/semantics/test_c2ir.py`.
2. Implement the mapping in `prik/semantics/fortran2ir.py` or `prik/semantics/c2ir.py`.
3. Keep the public semantic dtype names in `prik/semantics/models.py` stable unless
   there is a deliberate schema decision.
4. If the emitted `.pyi` annotation changes, update
   `tests/semantics/test_pyi_printer.py` and `tests/pyi/test_pyi_to_ir.py`.
5. Update the datatype tables in [semantics.md](semantics.md), and update
   [tutorial.md](tutorial.md) or [examples.md](examples.md) when a visible
   example changes.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/semantics/test_fortran2ir.py tests/semantics/test_c2ir.py
PYTHONPATH=. pytest -q tests/semantics/test_pyi_printer.py tests/pyi/test_pyi_to_ir.py
```

### Add `.pyi` Syntax Or Projection Behavior

Example target: add a new `Annotated[...]` metadata item or projection helper.

1. Add loader tests in `tests/pyi/test_pyi_to_ir.py`.
2. Update `prik/pyi_parser/parser.py`.
3. Add printer tests in `tests/semantics/test_pyi_printer.py`.
4. Update `prik/printers/pyi.py`.
5. Update semantic models in `prik/semantics/models.py` only if the IR needs a new
   field or constraint.
6. Update policy completion or wrapper planning if the syntax changes a
   completed decision.
7. Update [semantics.md](semantics.md), plus [tutorial.md](tutorial.md) or
   [examples.md](examples.md) when users need the new syntax in a workflow.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/pyi/test_pyi_to_ir.py
PYTHONPATH=. pytest -q tests/semantics/test_pyi_printer.py
```

### Add A Stage-Owned Error

Example target: report a new unsupported C/Fortran semantic contract clearly.

1. Preserve the source fact in the parser if it is not already present.
2. Complete the unsupported decision in post-IR policy when it is a wrapper
   policy limitation, or raise during semantic conversion when the fact cannot
   form a semantic contract.
3. Let the real planner call the completed-policy accessor for that owner; do
   not create a separate diagnostic traversal or blocker metadata payload.
4. Add a focused test for the owning semantic, policy, planning, or compiler
   stage.

6. Update [tutorial.md](tutorial.md) or [examples.md](examples.md) if users
   can fix the blocker by editing `.pyi`.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/codegen/
```

### Add Or Change CLI Behavior

Example target: add a stage option, change output routing, or improve
diagnostic formatting.

1. Add CLI tests in `tests/parser/test_cli.py` first.
2. Implement shared dispatch and output behavior in `prik/cli.py`.
3. Keep Fortran package-specific CLI behavior in `prik/fortran_parser/cli.py`.
4. If compiler preprocessing behavior changes, update `prik/preprocessing.py`
   and preprocessing tests.
5. Update [tutorial.md](tutorial.md) or [examples.md](examples.md) for
   user-facing commands and this guide for maintainer command maps.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/parser/test_cli.py
PYTHONPATH=. pytest -q tests/parser/test_preprocessing_cli.py
```

## Testing Map

Use this map when changing one part of the project. Each section shows how to
call that part manually, which focused test file to run, and where to look for
more executable examples. Run the broader suite before merging.

### Pre-Merge Checks

Run the full suite from the repository root before merging:

```bash
PYTHONPATH=. pytest -q
```

Run the major suites individually while iterating:

```bash
PYTHONPATH=. pytest -q tests/parser
PYTHONPATH=. pytest -q tests/semantics
PYTHONPATH=. pytest -q tests/pyi
PYTHONPATH=. pytest -q tests/wrapper
```

As a project policy, do not merge pull requests unless all checks are green.

### Fixture Maintenance

Refresh all C parser project goldens:

```bash
python tests/parser/c/generate_c_parser_goldens.py
```

Refresh one grouped C fixture project:

```bash
python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
```

Refresh all Fortran parser goldens:

```bash
python tests/parser/fortran/generate_fortran_parser_goldens.py
```

Refresh one Fortran fixture:

```bash
python tests/parser/fortran/generate_fortran_parser_goldens.py tests/data/fortran/general/basic_subroutine.f90
```

In-test Fortran parser fixture update mode:

```bash
FORTRAN_PARSER_UPDATE_GOLDENS=1 PYTHONPATH=. pytest -q tests/parser --confcutdir=tests/
```

Refresh semantic and `.pyi` fixtures:

```bash
python tests/semantics/generate_semantic_fixtures.py
python tests/pyi/generate_pyi_fixtures.py
```

When parser model output changes, include the regenerated parser goldens and a
short explanation in the PR. For `.pyi`, semantic IR, policy, or wrapper-planning behavior
changes, update the corresponding fixtures under `tests/pyi/fixtures` or
`tests/semantics/fixtures`.

### C Parser

Manual call for one C fixture:

```bash
python -m prik parse tests/data/c/general/math_api.h --language c --json
```

Manual Python API call:

```python
from prik import parse_c_file

parsed = parse_c_file("int add(int a, int b);", filename="example.h")
print([function.name for function in parsed.functions])
```

Focused tests by concern:

- Lexer/preprocessor mechanics:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_lexer_preprocessor.py`
- Declarations and declarators:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_declarations_and_declarators.py`
- Functions:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_functions.py`
- Structs, unions, enums, and typedefs:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_structs_unions_enums_typedefs.py`
- Project resolution and cross-file facts:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_project_resolution.py`
- Compiler extensions:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_compiler_extensions.py`
- Fixture project goldens:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_fixture_suite.py`
- Fatal parser diagnostics:
  `PYTHONPATH=. pytest -q tests/parser/c/test_c_error_fixture_suite.py`

Regenerate one grouped C fixture project:

```bash
python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
```

Executable tutorial: `tests/parser/c/test_c_parser_developer_tutorial.py`.

### Fortran Parser

Manual call for one Fortran fixture:

```bash
python -m prik parse tests/data/fortran/general/basic_subroutine.f90 --language fortran --json
```

Manual Python API call:

```python
from prik import parse_fortran_file

parsed = parse_fortran_file(
    "tests/data/fortran/general/basic_subroutine.f90",
)
print([module.name for module in parsed.modules])
```

Focused tests by concern:

- Parser walkthrough:
  `PYTHONPATH=. pytest -q tests/parser/test_parser_developer_tutorial.py`
- Procedures, declarations, derived types, and interfaces:
  `PYTHONPATH=. pytest -q tests/parser/test_procedure_and_type_parsing.py`
- Scope and project behavior:
  `PYTHONPATH=. pytest -q tests/parser/test_scope_handling.py tests/parser/test_project_scope_models.py`
- Preprocessing and execution-boundary behavior:
  `PYTHONPATH=. pytest -q tests/parser/test_preprocessor_and_execution_boundaries.py`
- Parser diagnostics:
  `PYTHONPATH=. pytest -q tests/parser/test_error_handling.py`
- Fixture goldens:
  `PYTHONPATH=. pytest -q tests/parser/test_fortran_fixture_suite.py`
- Parser error fixtures:
  `PYTHONPATH=. pytest -q tests/parser/test_fortran_error_fixture_suite.py`

Regenerate one Fortran fixture:

```bash
python tests/parser/fortran/generate_fortran_parser_goldens.py tests/data/fortran/general/basic_subroutine.f90
```

Executable tutorial: `tests/parser/test_parser_developer_tutorial.py`.

### Semantics And `.pyi`

Manual calls:

```bash
python -m prik semantics tests/data/fortran/general/basic_subroutine.f90
python -m prik generate --pyi tests/data/fortran/general/basic_subroutine.f90
python -m prik semantics tests/data/c/general/math_api.h --language c
python -m prik generate --pyi tests/data/c/general/math_api.h --language c
```

Focused tests by concern:

- Fortran parser-to-IR conversion:
  `PYTHONPATH=. pytest -q tests/semantics/test_fortran2ir.py`
- C parser-to-IR conversion:
  `PYTHONPATH=. pytest -q tests/semantics/test_c2ir.py`
- Wrapper-plan support diagnostics:
  `PYTHONPATH=. pytest -q tests/codegen/`
- `.pyi` printer:
  `PYTHONPATH=. pytest -q tests/semantics/test_pyi_printer.py`
- `.pyi` loader and edited stub behavior:
  `PYTHONPATH=. pytest -q tests/pyi/test_pyi_to_ir.py`
- Semantic and `.pyi` fixtures:
  `PYTHONPATH=. pytest -q tests/pyi/test_pyi_fixture_suite.py`

Regenerate semantic and `.pyi` fixtures:

```bash
python tests/semantics/generate_semantic_fixtures.py
python tests/pyi/generate_pyi_fixtures.py
```

Executable examples: `tests/semantics/test_pyi_printer.py` and
`tests/pyi/test_pyi_to_ir.py`.

### CLI

Manual calls:

```bash
python -m prik parse tests/data/fortran/general/basic_subroutine.f90
python -m prik semantics tests/data/fortran/general/basic_subroutine.f90
python -m prik generate --pyi tests/data/fortran/general/basic_subroutine.f90
python -m prik parse tests/data/c/general/math_api.h --language c
```

Focused tests:

- Full CLI behavior:
  `PYTHONPATH=. pytest -q tests/parser/test_cli.py`
- Stage dispatch:
  `PYTHONPATH=. pytest -q tests/parser/test_cli.py -k "parse or semantics or pyi or wrap"`
- Language and preprocessing selection:
  `PYTHONPATH=. pytest -q tests/parser/test_cli.py -k "language or preprocessing"`

Executable reference: `tests/parser/test_cli.py`.
