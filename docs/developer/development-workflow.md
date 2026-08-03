---
title: Development Workflow
audience: developers, contributors
prerequisites: repository checkout, Python 3.10 or newer
related: index.md, quality-assurance.md
status: maintained
publication: draft
---

# Development Workflow

This guide is for changing prik. It maps user-visible behavior to its owning
implementation and tests, then gives focused change and verification
workflows.

<!-- PRIK_C_DOCS_START
Use [Getting Started](../user/getting-started/index.md) and the
[Examples Gallery](../user/examples/index.md) to inspect the public workflows
before changing them. This guide is the developer entry
point for the C and Fortran parser references, implementation ownership, and
the detailed maintained contracts.
PRIK_C_DOCS_END -->

## Start Here

Install the project and QA dependencies:

```bash
python3 -m pip install -e ".[qa]"
```

Run the smallest relevant test while iterating, then run the full suite:

```bash
PYTHONPATH=. python3 -m pytest -q tests/fortran/command_line_interface/pipeline/
PYTHONPATH=. python3 -m pytest -q
```

Before changing a public behavior, trace it through these layers:

<!-- PRIK_C_DOCS_START
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
PRIK_C_DOCS_END -->

For example, a new CLI stage option normally requires:

1. A focused contract test in `tests/fortran/command_line_interface/pipeline/`.
2. Dispatch or output routing in `prik/cli.py`.
3. Preprocessing tests if the option changes source loading.
4. A copy-paste command in the relevant user guide or checked example.
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
| [Getting Started](../user/getting-started/index.md) | Main supported user workflow and boundaries |
| [Examples Gallery](../user/examples/index.md) | Checked commands and Python API recipes |
| [Fortran wrapper reference](../user/reference/fortran-wrapper.md) | Implemented Fortran runtime contract, mechanism, ownership, and build modes |
| [Fortran parser reference](fortran-parser-reference.md) | Developer inventory for the Fortran frontend |
| [Semantic IR reference](../user/reference/semantic-ir.md) | Accepted semantic IR and datatype contract |
| [Semantic .pyi format](../user/reference/semantic-pyi-format.md) | User-visible semantic `.pyi` syntax and roadmap |

<!-- PRIK_C_DOCS_START
| [C parser reference](c-parser-reference.md) | Developer inventory for the C frontend |
PRIK_C_DOCS_END -->

When adding a user example:

1. Prefer a checked repository fixture or a short inline source string.
2. Run the command or snippet from the repository root.
3. Add or identify the focused test that owns the behavior.
4. State limitations next to the example when metadata is preserved but not
   executed, such as `@native_call` projection metadata.

<!-- PRIK_C_DOCS_START
5. Distinguish the implemented source-driven Fortran wrapper from deferred
   workflows such as C-input wrapping, direct edited-`.pyi` CLI builds, and
   arbitrary Pythonic projection execution.
PRIK_C_DOCS_END -->

### Automatically Verify Markdown Examples

`tests/shared/docs/test_examples.py` executes explicitly marked
`bash` CLI examples and `python` API snippets from `README.md` and Markdown
files under `docs/`. Bash examples must be `python3 -m prik` commands; the test replaces `python3`
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
python3 -m prik semantics tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```
````

Mark a command whose stdout must match the documentation exactly:

````markdown
<!-- prik-doc-test: exact -->
```bash
python3 -m prik parse tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

<!-- prik-doc-test-output -->
```text
File: tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
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
<!-- prik-doc-source: tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 -->
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
PYTHONPATH=. python3 -m pytest -q tests/shared/docs/test_examples.py
```

## References

- [Getting Started](../user/getting-started/index.md): supported end-to-end user
  workflow and current boundaries.
- [Examples Gallery](../user/examples/index.md): checked CLI and Python API
  recipes.
- [Fortran parser reference](fortran-parser-reference.md): Fortran frontend scope,
  recursive parser organization, API/CLI behavior, diagnostics, fixture
  workflow, semantic handoff, and tests.
- [Semantic `.pyi` format](../user/reference/semantic-pyi-format.md): user-visible `.pyi`
  loader/printer contract and roadmap.
- [Quality assurance](quality-assurance.md): active QA commands, tool benefits, known
  defects found by each tool, and scheduled triage process.

<!-- PRIK_C_DOCS_START
- [C parser reference](c-parser-reference.md): C frontend scope, preprocessing and
  project policy, parser architecture, CLI behavior, semantic handoff,
  fixtures, and tests.
- [Semantic IR reference](../user/reference/semantic-ir.md): shared semantic model, datatype
  policy, and C conversion facts.
PRIK_C_DOCS_END -->

## User-Facing Contract Internals

The tutorial, examples cookbook, `.pyi` format, and semantic reference describe
CLI stages, `.pyi` syntax, datatype names, and wrapper-plan diagnostics. The developer
task is to keep those user-visible contracts stable, tested, and traceable to
implementation files.

### Source Ownership Map

| User-visible area | Main implementation files | Main tests |
| --- | --- | --- |
| Fortran parse output | `prik/parsers/fortran/parser.py`, `prik/parsers/fortran/models.py`, `prik/parsers/fortran/lexer.py` | `tests/fortran/source_parsing/parsing/`, `tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py`, `tests/fortran/source_parsing/parsing/test_error_handling.py` |
| CLI stage selection and output | `prik/cli.py`, `prik/parsers/fortran/cli.py` | `tests/fortran/command_line_interface/pipeline/` |
| Fortran target type probing and cache | `prik/probes/fortran_types.py` | `tests/fortran/data_types/probes/test_fortran_type_probes.py` |
| Generated target datatype mapping examples | `prik/probes/report.py` | `tests/shared/types/test_mapping_report.py`, `tests/shared/docs/test_examples.py` |
| Fortran to semantic IR | `prik/semantics/fortran2ir.py`, `prik/semantics/models.py` | `tests/fortran/semantic_ir/semantics/` |
| `.pyi` printing | `prik/wrapper_codegen/printers/pyi_printer.py` | `tests/fortran/semantic_pyi_format/pipeline/`, `tests/fortran/semantic_pyi_format/pipeline/test_modern_example.py` |
| `.pyi` parsing/loading/editing | `prik/parsers/pyi/parser.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py` | `tests/fortran/semantic_pyi_format/` |
| Semantic policy completion | `prik/semantics/policy_completion.py`, `prik/semantics/ownership.py` | `tests/fortran/infrastructure/policy/` and feature-local `policy/` directories |
| Fortran wrapper orchestration | `prik/pipeline/build.py` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py` |
| Wrapper planning, owner-local errors, and direct lowering | `prik/wrapper_codegen/plan.py`, `prik/wrapper_codegen/planner.py`, `prik/wrapper_codegen/generator.py` | `tests/fortran/infrastructure/wrapper_codegen/`, feature-local `wrapper_codegen/` stages |
| Native compilation and binding support | `prik/compiling/`, `prik/binding_support/` | `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py`, `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py` |
| Executable Markdown examples | `README.md`, `docs/*.md` | `tests/shared/docs/test_examples.py` |

<!-- PRIK_C_DOCS_START
| C parse output | `prik/parsers/c/parser.py`, `prik/parsers/c/models.py`, `prik/parsers/c/lexer.py` | `tests/c/parsing/test_c_declarations_and_declarators.py`, `tests/c/parsing/test_c_fixture_suite.py`, `tests/c/parsing/test_c_error_fixture_suite.py` |
| Compiler preprocessing | `prik/pipeline/preprocessing.py` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`, `tests/c/parsing/test_c_lexer_preprocessor.py` |
| C target ABI probing and cache | `prik/probes/c_types.py` | `tests/c/probes/test_c_types.py` |
| C to semantic IR | `prik/semantics/c2ir.py`, `prik/semantics/models.py` | `tests/c/semantics/conversion/` |
| Fortran-to-C bridge and CPython binding | `prik/wrapper_codegen/fortran/bridge.py`, `prik/wrapper_codegen/c/binding.py` | `tests/fortran/infrastructure/wrapper_codegen/`, feature-local `wrapper_codegen/` stages |
| Public API exports | `prik/__init__.py` | `tests/fortran/source_parsing/parsing/test_public_entrypoints.py`, `tests/c/parsing/test_c_public_api_skeleton.py` |
PRIK_C_DOCS_END -->

### Wrapper Generator Class Organization

<!-- PRIK_C_DOCS_START
Current runtime wrapper codegen is intentionally narrow: Fortran sources lower
through the generated Fortran bridge, generated C, and the CPython extension
binding. Semantic `.pyi` emission is the editable contract printer. Do not keep
placeholder C++, pybind11, or Python source printers until
those backends have a documented runtime contract and tests.
PRIK_C_DOCS_END -->

Organize generators and printers using `FortranParser` in
`prik/parsers/fortran/parser.py` as the structural reference. A developer
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

All model-type dispatch goes through `prik.utilities.visitor.ClassVisitor._visit` and a
matching `<prefix>_<ClassName>` handler. Parser-model converters, semantic
lowering, `.pyi` AST visitors, bridges, bindings, and printers share that one
implementation; do not duplicate its MRO lookup in an individual class.

An explicit table is allowed only for a genuine second dispatch dimension,
such as a completed policy action or primitive ABI datatype mapping. Such a
table must not replace model-class visitation. Do not add a second independent
visitor family, `visit_<ClassName>`, or scattered `isinstance` dispatch
schemes.
A method that performs ordinary work but is not a dispatch target must have a
descriptive helper name rather than a visitor-shaped name.

Keep functionality on the class that owns its state and policy. A module-level
function is justified only when it is a deliberate public functional API or a
genuinely stateless utility shared by unrelated classes. Do not retain a
module-level function only to preserve an old internal call path.

### `.pyi` Contract Internals

User-visible `.pyi` syntax is first parsed to Python AST by
`prik/parsers/pyi/parser.py`, loaded from text/files by
`prik/pipeline/pyi.py`, converted to semantic IR by
`prik/semantics/pyi2ir.py`, and printed by
`prik/wrapper_codegen/printers/pyi_printer.py`. The converter and printer operate on
`prik/semantics/models.py`.

Important implementation rules:

- `Addr(T)` and `Addr(T)` are storage contracts, not just pretty syntax.
- Array subscriptions such as `Float64[n]` are semantic array contracts.
- `Annotated[..., ORDER_F]` and `ORDER_ANY` are non-default array storage
  metadata. Plain multidimensional Fortran `.pyi` arrays use `ORDER_F`; do not
  print or retain that default marker in a generated contract.
  `Allocatable[T[...]]` and `Pointer[T[...]]` are descriptor-handle wrappers
  around the array storage contract. Output and writeback behavior is
  represented by writable storage plus `Returns["name", T]` when a Python
  result is projected.
<!-- PRIK_C_DOCS_START
- Plain multidimensional C `.pyi` arrays use `ORDER_C`; generated contracts
  omit that language default and retain only an intentional alternate layout.
PRIK_C_DOCS_END -->
- `Final[T]` is the public constant spelling. Do not reintroduce
  `Constant` as user-facing `.pyi` syntax.
- `@native_call` is projection metadata. Use it only when the Python-visible
  signature intentionally differs from the native signature.
- Generated stubs should preserve behavior-changing native contracts while
  staying compact; exact source intent that does not change execution can stay
  in semantic IR instead of the printed `.pyi`.
- Use `SourceName("...")` only when a source identifier cannot be used as the
  Python target. Do not infer source identifiers from normalized Python names.
- Binding locals derived from a Python-visible argument must use the reserved
  `bound_` namespace. Generated binding sources include Python, standard-library,
  optional descriptor, NumPy, and runtime headers, so their imported identifier
  sets are not a stable public-name vocabulary.
- Omit `Polymorphic` only for the passed-object dummy of a type-bound procedure,
  where the binding itself restores that native fact. Ordinary `class(T)`
  arguments must retain it.

When changing `.pyi` syntax:

1. Add or update parser tests in `tests/fortran/semantic_pyi_format/parsing/`.
2. Add or update printer tests in `tests/fortran/semantic_pyi_format/pipeline/`.
3. Update fixture tests only if the public generated contract changes.
4. Update the relevant [User Guide](../user/guide/index.md) or checked
   [example](../user/examples/index.md) if users need to write or read the new
   syntax.
5. Update [Semantic .pyi format](../user/reference/semantic-pyi-format.md) for the full user-facing reference.
6. Update [Semantic IR reference](../user/reference/semantic-ir.md) if the underlying semantic IR contract
   changes.

### Datatype Mapping Internals

User-visible datatype names are semantic names, not raw parser spellings.
Mapping happens during parser-to-IR conversion:

- Fortran intrinsic/kind mapping and compiler storage-fact application live in
  `prik/semantics/fortran2ir.py`.
- The shared dtype names and storage contracts live in `prik/semantics/models.py`.
- Compiler-measured mapping snapshots are generated by
  `prik/probes/report.py`.

<!-- PRIK_C_DOCS_START
- C primitive, typedef, and probe-aware mapping lives in `prik/semantics/c2ir.py`.
PRIK_C_DOCS_END -->

When changing datatype mapping:

1. Add focused Fortran conversion tests in
   `tests/fortran/semantic_ir/semantics/`.
2. Add `.pyi` printer/loader coverage if the emitted syntax changes.
3. Update semantic fixtures only when serialized semantic IR intentionally
   changes.
4. Update [Semantic IR reference](../user/reference/semantic-ir.md), plus the
   relevant [User Guide](../user/guide/index.md) or checked
   [example](../user/examples/index.md) when the visible user workflow or
   examples change.
5. Regenerate and update the exact target mapping snapshots in
   [Semantic IR reference](../user/reference/semantic-ir.md). The executable documentation test must match
   the complete output of:

<!-- PRIK_C_DOCS_START
1. Add focused conversion tests in `tests/fortran/semantic_ir/semantics/` or
   `tests/c/semantics/conversion/`.
PRIK_C_DOCS_END -->

   ```bash
   python3 -m prik probe --language fortran --compiler gfortran --format markdown
   ```

<!-- PRIK_C_DOCS_START
   ```bash
   python3 -m prik probe &#45;&#45;language c &#45;&#45;compiler cc &#45;&#45;format markdown
   python3 -m prik probe &#45;&#45;language fortran &#45;&#45;compiler gfortran &#45;&#45;format markdown
   ```
PRIK_C_DOCS_END -->

For Fortran, keep both modern and legacy spellings in the generated report.
Legacy numeric `type*N` forms carry fixed total storage; compiler-dependent
default, kind, `DOUBLE PRECISION`, and `DOUBLE COMPLEX` forms use probe facts.

### Error Ownership

Diagnostics belong to the earliest stage that has enough facts to explain the
failure. Parsers report source syntax and preprocessing faults. Semantic
conversion reports facts that cannot form a valid contract. Policy completion
records every lowering decision; the wrapper planner reports an unsupported
completed policy with its owner path. Add focused tests to that owning stage,
and update the relevant user guide when a user can correct the input or
contract.

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

<!-- PRIK_C_DOCS_START
```text
CLI args
  -> language resolution
  -> preprocessing config and source loading
  -> parser models
  -> semantic IR
  -> post-IR policy completion
  -> inspection: .pyi printing / .pyi loading
  -> Fortran build: WrapperPlan / direct bridge and binding lowering / extension
```
PRIK_C_DOCS_END -->

### CLI And Language Resolution

`prik/cli.py` is the shared command-line entrypoint. It is responsible for:

- rejecting ambiguous directories and unknown suffixes without `--language`;
- building `PreprocessingConfig`;
- dispatching `parse`, `semantics`, `generate`, and `probe`;
- defaulting recognizable Fortran sources to a wrapper build when no
  subcommand is selected;
- routing the default build and `generate --sources|--makefile` through
  `prik/pipeline/build.py`;
- routing text, JSON, and `--out` output.

<!-- PRIK_C_DOCS_START
- choosing Fortran or C from `&#45;&#45;language` and file suffixes;
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Recognizable Fortran files and `.pyi` wrapper inputs can omit `&#45;&#45;language`.
C files and directories require explicit language selection. Keep this behavior
tested in `tests/fortran/command_line_interface/pipeline/` whenever stage selection changes.
PRIK_C_DOCS_END -->

The package-specific `prik/parsers/fortran/cli.py` remains for the Fortran parser
package entrypoint. New cross-language user behavior normally belongs in
`prik/cli.py`.

### Preprocessing Internals

`prik/pipeline/preprocessing.py` owns compiler-backed preprocessing and provenance. The
main value object is `PreprocessingConfig`; the main execution path is
`run_compiler_preprocessor_with_recipe(...)`.

Important contracts:

- The preprocessing recipe is part of the parser payload when preprocessing
  happened. It records compiler, adapter, argv, include directories, defines,
  undefs, standard, extra compiler args, included files, source mappings, and
  diagnostics.

<!-- PRIK_C_DOCS_START
- CLI source parsing uses compiler mode. C defaults to `cc`; Fortran defaults
  to `gfortran` unless the user passes a compiler, compile database, or custom
  template.
- C direct parser entrypoints can still be used on raw strings or already
  controlled source in Python tests.
- C preprocessing uses GCC/Clang-style `-E -x c` for direct compiler mode.
  Fortran direct compiler mode uses `-E -cpp` plus source-form hints where
  needed. LLVM Flang additionally uses `-P` so its preprocessed parser input
  contains no `#line` markers; provenance remains available from the recorded
  preprocessing recipe.
- Native Fortran `include "..."` is expanded after compiler CPP output because
  it is Fortran textual inclusion, not C/CPP include semantics.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
When changing preprocessing behavior, update
`tests/fortran/source_preprocessing/preprocessing/`, source-boundary tests in
`tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`, and C raw
directive tests in `tests/c/parsing/test_c_lexer_preprocessor.py`.
PRIK_C_DOCS_END -->

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
from prik.pipeline.preprocessing import PreprocessingConfig, preprocess_source

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

<!-- PRIK_C_DOCS_START
C direct Python API, no macro expansion needed:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik import parse_c_file
from semantics.c2ir import c_file_to_semantic_modules

parsed = parse_c_file("int add(int a, int b);", filename="api.h")
modules = c_file_to_semantic_modules(parsed)
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
C raw mode records include and pragma metadata and accepts simple include
guards. Macro-shaped directives such as `#if`, `#ifdef`, `#define` outside a
trivial include guard, and `#error` require compiler preprocessing and are
rejected with `CPARSE_PREPROCESSING_REQUIRED`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
C with macros follows the compiler-preprocessed path, then parses the expanded
translation unit in `compiler` or `preprocessed` mode:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from pathlib import Path

from c_parser.cli import attach_preprocessing_recipe
from prik import parse_c_file
from semantics.c2ir import c_file_to_semantic_modules
from prik.pipeline.preprocessing import PreprocessingConfig, preprocess_source

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
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The C semantic converter can turn recorded object-like numeric macros into
semantic constant variables. Function-like macros and untyped macro bodies are
not wrapper-callable declarations. Declarations that depend on macros which
were recorded but not expanded remain explicit semantic facts rather than
being treated as complete wrapper contracts.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
For CLI code, do not reimplement these paths manually. `prik/cli.py` builds
the `PreprocessingConfig`, loads or preprocesses source, attaches C
preprocessing recipes, parses, runs target type probes when configured, and
then dispatches to the semantic helpers.
PRIK_C_DOCS_END -->

### Semantic, `.pyi`, Wrapper-Planning, And Type-Probe Paths

<!-- PRIK_C_DOCS_START
The semantic stages share one rule: source inputs become semantic IR before
anything emits `.pyi` or builds a wrapper plan. Edited `.pyi` inputs are already a
semantic contract and do not go back through C or Fortran parsing.
PRIK_C_DOCS_END -->

Input shapes are part of the contract:

- `parse_fortran_file(source_or_path, filename=...)` accepts inline source
  text. It reads from disk only when `source_or_path` names an existing file
  and `filename` is omitted. Pass `filename` with inline text for diagnostic
  provenance.
- `preprocess_source(path, language=..., config=...)` is path-based because it
  shells out to a compiler. Feed `preprocessed.source` to the parser afterward.
- `parse_pyi_text(...)` accepts inline `.pyi` source text and returns Python
  AST. `convert_pyi_to_ir(...)` converts that parsed AST to semantic IR.
  `pyi_text_to_semantic_module(...)`, `pyi_file_to_semantic_module(...)`, and
  `pyi_paths_to_semantic_modules(...)` combine parsing and conversion for
  inline text, one file, or a file set.
- The CLI accepts source, `.pyi`, and directory paths. It does not accept
  inline source text on the command line.

<!-- PRIK_C_DOCS_START
- `parse_c_file(source_or_path, filename=...)` accepts inline source text or
  an existing file path. Existing paths are read from disk; `filename` can
  still override the diagnostic/source name.
- `parse_fortran_project(...)` and `parse_c_project(...)` accept an in-memory
  mapping of `filename -> source`, an explicit file/path list, or a directory.
  Fortran directory parsing discovers supported Fortran files and orders them
  by module dependencies. C directory parsing discovers supported C files and
  records include graph facts; include directives do not recursively open more
  files.
PRIK_C_DOCS_END -->

CLI source stages:

<!-- PRIK_C_DOCS_START
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
PRIK_C_DOCS_END -->

CLI `.pyi` wrapper build:

```text
.pyi path(s) or directory
  -> prik/parsers/pyi/parser.py
  -> prik/pipeline/pyi.py pyi_paths_to_semantic_modules(...)
  -> prik/semantics/pyi2ir.py
  -> SemanticModule list
  -> prik/semantics/policy_completion.py
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

<!-- PRIK_C_DOCS_START
For C, the same shape uses `parse_c_file(...)` or `parse_c_project(...)`,
then `c_file_to_semantic_modules(...)` or
`c_project_to_semantic_modules(...)`, then `emit_module_stubs(...)`.
PRIK_C_DOCS_END -->

Loading or editing `.pyi` is the opposite direction:

```python
from prik import pyi_paths_to_semantic_modules

modules = pyi_paths_to_semantic_modules("interfaces")
```

Use the `.pyi` helpers by input shape:

- `parse_pyi_text(source, filename=...)` from `prik.parsers.pyi` for parser-only
  AST parsing.
- `convert_pyi_to_ir(tree, module_name=..., source=...)` from `pyi2ir.py` for
  AST-to-IR conversion.
- `pyi_text_to_semantic_module(source, module_name=..., filename=...)` from
  `pyi_pipeline.py` for inline text.
- `pyi_file_to_semantic_module(path, module_name=...)` for one file.
- `pyi_paths_to_semantic_modules(paths_or_directory)` for a set of interfaces
  that may reference each other.

The `.pyi` pipeline uses a per-operation in-memory conversion cache. Wrapper
entry-contract discovery reuses the same converted modules when it later builds
the reconciled contract bundle, so an imported file is not parsed and converted
twice in one build. Do not make this cache process-global: semantic modules are
mutated by reconciliation, export selection, and policy completion.

<!-- PRIK_C_DOCS_START
Do not run compiler preprocessing, C ABI probes, or Fortran type probes for an
edited `.pyi` wrapper build. Once `.pyi` has been loaded, the edited semantic
IR is the source of truth.
PRIK_C_DOCS_END -->

Compiler preprocessing flags all flow through `PreprocessingConfig`:

| CLI flag | `PreprocessingConfig` field | Notes |
| --- | --- | --- |
| `--compiler` | `compiler` | Exact executable for direct preprocessing and automatic type probes. |
| `--preprocessor-adapter` | `adapter` | Adapter family, including `command-template`. |
| `--preprocess-template` | `command_template` | Custom command; requires `--preprocessor-adapter command-template`. |
| `-I` / `--include-dir` | `include_dirs` | Passed to compiler preprocessing and native Fortran include expansion. |
| `-D` / `--define` | `defines` | Macro definitions for compiler preprocessing. |
| `-U` / `--undef` | `undefs` | Macro undefinitions for compiler preprocessing. |
| `--std` | `std` | Passed as `-std=...`. |
| `--compiler-arg` | `compiler_args` | Raw target/sysroot/compiler options. |
| `--public-include`, `--private-include`, `--include-exposure` | include exposure fields | Controls provenance exposure, not parser grammar. |

<!-- PRIK_C_DOCS_START
| `&#45;&#45;compile-commands` | `compile_commands` | Project compile database; automatic C ABI probing is not allowed from this mixed recipe. |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`preprocess_source(...)` returns expanded source and a recipe. The C parser
needs `preprocessing="compiler"` or `"preprocessed"` for that expanded source,
and CLI code attaches the recipe with `attach_preprocessing_recipe(...)` so
macro metadata can reach semantic conversion. Fortran consumes the expanded
source with `parse_fortran_file(...)`; the parse-stage CLI payload records the
recipe separately.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
C target datatype mapping path:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```text
C source
  -> parse_c_project(...)
  -> optional C standard type report
  -> c_project_to_semantic_modules(..., standard_type_report=...)
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
For direct-compiler C semantic and `.pyi` stages, `prik/cli.py` runs
`probe_c_standard_types_cached(...)` internally and passes the measured facts
to `prik/semantics/c2ir.py`. The public `prik probe` command exposes the report
as an inspection output; semantic stages do not accept that report as a second
input path. Probe execution, cache, and refresh policy belong to
`prik/probes/c_types.py`.
PRIK_C_DOCS_END -->

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

<!-- PRIK_C_DOCS_START
The CLI performs those probe steps internally for Fortran semantic, `.pyi`, and
wrapper-build stages when a direct Fortran compiler is configured.
`compile_time_values` resolve symbolic parameters and kind expressions.
`type_facts` measure compiler-dependent intrinsic storage, such as default
integer width or target-changing flags. Source-driven wrapper builds derive the
probe configuration from preprocessing plus the native Fortran compiler flags;
this keeps flags such as `-fdefault-real-8` aligned between semantic lowering
and native compilation. The standalone `prik probe` report is an inspection and
verification output, not an alternate semantic-stage input.

Post-IR module-variable policy distinguishes literal constants from symbolic
numeric source parameters. Literal constants use binding-owned materialization;
symbolic numeric source parameters use a read-only Fortran bridge getter and
never require binding or bridge lowering to recover the initializer value.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Generated datatype mapping reports are documentation and verification outputs,
not a separate parse path. `prik/probes/report.py` uses the C and Fortran
converter/probe machinery to print target-specific mapping examples for
`docs/user/reference/semantic-ir.md`; changes there need both semantic conversion tests and
documentation-example verification.
PRIK_C_DOCS_END -->

### Fortran Runtime Wrapper Path

`prik/pipeline/build.py::build_fortran_extension(...)` and
`prik/pipeline/build.py::build_pyi_extension(...)` are the public orchestration
boundaries for wrapper builds. Keep their stages explicit:

```text
ordered source paths
  -> preprocess_source(..., language="fortran")
  -> parse_fortran_project(...)
  -> compile-time expression and storage probes
  -> fortran_project_to_semantic_modules(...)
  -> merge public semantic modules
  -> WrapperPlanner and WrapperCodeGenerator
  -> create_shared_library(...)
  -> WrapperBuildResult
```

The main ownership boundaries are:

- `prik/pipeline/build.py`: source order, preprocessing/probing, semantic merge,
  `.pyi` entry-contract loading, native build plan assembly, output placement,
  direct-versus-Makefile mode, and artifact reporting;
- `prik/wrapper_codegen/planner.py`: projection from completed semantic policy
  into validated typed plans;
- `prik/wrapper_codegen/generator.py`: direct bridge, binding, and source
  artifact generation;
- `prik/compiling/`: compiler commands and shared-library linking; and
- `prik/binding_support/`: native binding support copied into each build.

<!-- PRIK_C_DOCS_START
- `prik/wrapper_codegen/fortran/bridge.py`: Fortran-to-C ABI adaptation;
- `prik/wrapper_codegen/c/binding.py`: Python argument/result conversion,
  reference handling, and CPython wrapper construction;
- `prik/wrapper_codegen/printers/source_printers.py`: source rendering only;
PRIK_C_DOCS_END -->

Do not move semantic ownership or projection policy into printers. Do not infer
source dependencies: multi-source source builds compile in caller order, and
the first semantic module names the merged extension. `.pyi` builds use exactly
one semantic entry contract plus a separate extension-level
`NativeBuildPlan`; they must not recover Python API facts by reparsing native
implementation sources. `--makefile` records the compiler/linker plan
without executing it; for `.pyi` builds, `prik-build.json` is written first and
`Makefile.prik` is projected from that manifest.

<!-- PRIK_C_DOCS_START
Generated `bind_c_<module>` Fortran bridges are a C ABI implementation detail,
not a Fortran-use API. They therefore do not emit a default `private` statement
or one `public :: ...` line per generated wrapper procedure. Python exposure is
owned by the C extension method table; the bridge only marks the allocator
interface name `c_malloc` private to avoid exporting that helper through Fortran
module use association.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The current runtime build surface is Fortran-focused. Edited `.pyi` files can
drive `.pyi` wrapper builds when the caller supplies explicit native artifacts,
but full generated-contract parity is still tracked in the roadmap. User C
inputs currently stop at semantic conversion; their runtime backend is future
work even though the Fortran wrapper internally emits C source.
PRIK_C_DOCS_END -->

Runtime verification belongs under the relevant
`tests/fortran/<feature>/end_to_end/` owner. The
[`tests/fortran` index](../../tests/fortran/README.md) and permanent
[contract ledger](../../tests/fortran/CONTRACT_COVERAGE.md) map generated
behavior to compiled/imported tests. Build-mode changes should at least cover
`tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`,
`tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py`,
and the affected runtime subject test.

### Parser Model Internals

Parser models are source facts. They should answer "what did the source say?"
rather than "what Python wrapper should be generated?"

Fortran:

- `prik/parsers/fortran/parser.py` slices the file into grammar units, then parses
  each unit's specification region.
- `prik/parsers/fortran/models.py` stores `FortranFile`, modules, procedures,
  variables, derived types, interfaces, programs, submodules, and diagnostics.
- Execution bodies are intentionally skipped after the parser has enough
  signature/source facts.

<!-- PRIK_C_DOCS_START
C:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- `prik/parsers/c/lexer.py` handles comments, directives, top-level splitting, and
  token source locations.
- `prik/parsers/c/parser.py` visits declarations and declarators, records typed
  source facts, and reports unsupported parser-owned syntax.
- `prik/parsers/c/models.py` stores functions, variables, typedefs, structs, unions,
  enums, includes, raw directives, preprocessing facts, and diagnostics.
PRIK_C_DOCS_END -->

Adding parser fields is a schema decision. Add fields only when downstream
semantic conversion, fixtures, diagnostics, or user-visible behavior need a
new fact.

### Semantic IR Internals

The semantic layer normalizes Fortran facts into language-neutral models from
`prik/semantics/models.py`.

<!-- PRIK_C_DOCS_START
The semantic layer normalizes C and Fortran facts into language-neutral models
from `prik/semantics/models.py`.
PRIK_C_DOCS_END -->

- `prik/semantics/fortran2ir.py` maps Fortran procedures, derived types, module
  variables, kinds, shapes, storage contracts, visibility, imported references,
  and compile-time values.
- `prik/wrapper_codegen/printers/pyi_printer.py` emits editable user contracts.
- `prik/parsers/pyi/parser.py` parses edited contracts to Python AST.
- `prik/pipeline/pyi.py` converts edited contract text, files, and path sets.
- `prik/semantics/pyi2ir.py` converts parsed `.pyi` AST back into semantic IR.
- `prik/semantics/native_contract.py` validates immutable native scope, ABI,
  placement, type, callback, and projection facts before source-free codegen.
- Named data bindings keep role-specific semantic types: `SemanticVariable`
  for module variables and constants, `SemanticArgument` for callable
  parameters, and `SemanticField` for Fortran derived-type components.
- `prik/semantics/policy_completion.py` completes semantic policies after
  Fortran or `.pyi` conversion and before wrapper planning or lowering.

<!-- PRIK_C_DOCS_START
- Named data bindings share a common base but keep role-specific types:
  `SemanticVariable` for module/global variables and macro constants,
  `SemanticArgument` for callable parameters, `SemanticField` for struct,
  union, and Fortran derived-type fields. `SemanticFunction.locals` is the
  reserved home for local variables or local constants if a frontend later
  promotes them into semantic IR; local bindings are not emitted into `.pyi` or
  treated as wrapper interface items by default.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- `prik/semantics/c2ir.py` maps C functions, variables, structs/opaque structs,
  enums, typedef chains, standard-type probe facts, macros, pointer/array
  storage, and C-specific semantic facts.
- C `int` keeps the semantic name `Int` while its compiler-probed concrete
  precision is stored on the semantic type. C and Fortran enums lower to
  unscoped module-level integer constants; enum names are metadata, not
  semantic datatypes.
- `prik/semantics/policy_completion.py` completes semantic policies after
  C/Fortran/`.pyi` conversion and before wrapper planning or lowering.
PRIK_C_DOCS_END -->

Keep semantic IR stable where possible. If a parser change does not affect the
semantic contract, avoid changing semantic fixtures.

### `.pyi` Projection Internals

`@native_call` is stored as projection metadata on `SemanticFunction`. The
loader and printer currently support `Arg`, `Return`, ABI-typed literal calls
such as `Int32(1)`, `Len`, `IsPresent`, `Work`, `Pass`, and `.shape[...]`
value references. Generated Fortran contracts use it when outputs make the
Python-visible argument order differ from native order. `Pass()` preserves the
hidden passed object when a type-bound method also needs such a projection. They do not currently
implement future wrapper projection helpers such as `Addr(Arg(...))`, `As[...]`,
status-return policy, ownership conversion, or coercion execution.

The test ownership is:

- loader syntax and error behavior: `tests/fortran/semantic_pyi_format/parsing/`;
- printer round-trip shape: `tests/fortran/semantic_pyi_format/pipeline/`;
- policy-completion decisions: `tests/fortran/infrastructure/policy/` and feature-local `policy/` directories;
- wrapper-plan diagnostics: `tests/fortran/infrastructure/wrapper_codegen/`.

<!-- PRIK_C_DOCS_START
- C semantic conversion: `tests/c/semantics/conversion/`.
PRIK_C_DOCS_END -->

When adding projection syntax, first add loader tests that prove the accepted
syntax and rejected syntax. Then add policy or wrapper-plan tests only if the
new metadata affects those layers.

## Testing Strategy

Use the smallest test layer that proves the behavior, then add broader
coverage only when the public contract changes.

### Test Layers

| Layer | Purpose | Typical files |
| --- | --- | --- |
| Focused parser tests | One construct, diagnostic, or model field | `tests/fortran/source_parsing/parsing/test_*.py` |
| Parser fixture goldens | Serialized Fortran parser contracts | `tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py` |
| Semantic tests | Fortran parser facts converted to wrapper-neutral IR | `tests/fortran/semantic_ir/semantics/` |
| Policy tests | Completed policy decisions | `tests/fortran/infrastructure/policy/` and feature-local `policy/` directories |
| Wrapper-plan tests | Unsupported plan diagnostics and generated plan shape | `tests/fortran/infrastructure/wrapper_codegen/` |
| `.pyi` tests | Editable contract loader/printer behavior | `tests/fortran/semantic_pyi_format/`, `tests/fortran/semantic_pyi_format/pipeline/` |
| CLI tests | User commands, output routing, diagnostics | `tests/fortran/command_line_interface/pipeline/`, `tests/fortran/source_preprocessing/preprocessing/` |
| Wrapper build tests | Artifact placement, direct/Makefile modes, multi-source ordering | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py` |
| Wrapper runtime tests | Imported extension behavior, ownership, lifetime, and failures | Feature-local `tests/fortran/*/end_to_end/` suites indexed by `tests/fortran/README.md` |
| Property/fuzz tests | Broad parser robustness invariants | `tests/fortran/source_parsing/parsing/` and feature-local semantic property tests |

<!-- PRIK_C_DOCS_START
| Semantic tests | Parser facts converted to wrapper-neutral IR | `tests/fortran/semantic_ir/semantics/`, `tests/c/semantics/conversion/` |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Focused parser tests | One construct, diagnostic, or model field | `tests/fortran/source_parsing/parsing/test_*.py`, `tests/c/parsing/test_*.py` |
| Parser fixture goldens | Serialized parser contract over curated files | `tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py`, `tests/c/parsing/test_c_fixture_suite.py` |
PRIK_C_DOCS_END -->

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
- Wrapper orchestration or codegen behavior: the focused feature-local
  `end_to_end/` or `wrapper_codegen/` owner, including an imported runtime
  assertion rather than build success alone.

### Golden Fixture Rules

Do not regenerate broad fixture sets to hide uncertainty. First write or run a
focused test that explains the intended behavior. Then regenerate only the
affected fixture group when the serialized contract really changed.

Useful commands:

<!-- PRIK_C_DOCS_START
```bash
python tests/c/fixtures/parser/generate_c_parser_goldens.py tests/c/fixtures/native/general/math_api.h
python tests/fortran/source_parsing/parsing/generate_parser_goldens.py tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
python tests/fortran/semantic_ir/semantics/generate_semantic_fixtures.py
WRAPPER_UPDATE_PYI_FIXTURES=1 python3 -m pytest -q tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py
```
PRIK_C_DOCS_END -->

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

<!-- PRIK_C_DOCS_START
### Add A C Declaration Feature
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Example target: support a new declaration spelling or compiler extension in
the C parser.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
1. Add the smallest source example to a focused C parser test:
   `tests/c/parsing/test_c_declarations_and_declarators.py`,
   `tests/c/parsing/test_c_compiler_extensions.py`, or
   `tests/c/parsing/test_c_structs_unions_enums_typedefs.py`.
2. Implement the parser change in `prik/parsers/c/parser.py`. Add or update model
   fields in `prik/parsers/c/models.py` only if the serialized parser contract needs
   new facts.
3. If source splitting or raw directive handling changes, update
   `prik/parsers/c/lexer.py` and `tests/c/parsing/test_c_lexer_preprocessor.py`.
4. If project-level resolution changes, update
   `tests/c/parsing/test_c_project_resolution.py`.
5. If parser JSON changes intentionally, regenerate the relevant project
   golden:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
   ```bash
   python tests/c/fixtures/parser/generate_c_parser_goldens.py tests/c/fixtures/native/general/math_api.h
   ```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
6. If the new parser fact affects semantic conversion, update
   `prik/semantics/c2ir.py` and add coverage in `tests/c/semantics/conversion/`.
7. If the generated `.pyi` changes, update `tests/fortran/semantic_pyi_format/pipeline/`
   or `tests/fortran/semantic_pyi_format/pipeline/test_contract_loading.py`.
8. Update [C parser reference](c-parser-reference.md), the relevant
   [User Guide](../user/guide/index.md), checked
   [example](../user/examples/index.md), or
   [Semantic IR reference](../user/reference/semantic-ir.md) if users or
   developers need to know the new behavior.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Focused verification:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
PYTHONPATH=. pytest -q tests/c/parsing/test_c_declarations_and_declarators.py
PYTHONPATH=. pytest -q tests/c/parsing/test_c_project_resolution.py
PYTHONPATH=. pytest -q tests/c/semantics/conversion/
```
PRIK_C_DOCS_END -->

### Add A Fortran Parser Feature

Example target: preserve a new declaration attribute, source fact, or argument
metadata item.

1. Add a focused parser test in the file that owns the behavior:
   `tests/fortran/source_parsing/parsing/`,
   `tests/fortran/modules/parsing/test_scope_handling.py`, or
   `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`.
2. Implement parsing in `prik/parsers/fortran/parser.py`. Add model fields in
   `prik/parsers/fortran/models.py` only if the parser output needs to expose the
   new fact.
3. Add parser diagnostic coverage in `tests/fortran/source_parsing/parsing/test_error_handling.py` if
   malformed source should now fail differently.
4. If project ordering, imports, or compile-time values change, update
   `tests/fortran/modules/parsing/test_project_scope_models.py` or
   `tests/fortran/data_types/probes/test_fortran_type_probes.py`.
5. If serialized parser JSON changes intentionally, regenerate the selected
   fixture:

   ```bash
   python tests/fortran/source_parsing/parsing/generate_parser_goldens.py tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
   ```

6. If the new fact affects semantic output, update `prik/semantics/fortran2ir.py`
   and `tests/fortran/semantic_ir/semantics/`.
7. If generated `.pyi` changes, update `tests/fortran/semantic_pyi_format/pipeline/`
   and the relevant fixture tests.
8. Update [Fortran parser reference](fortran-parser-reference.md), the relevant
   [User Guide](../user/guide/index.md), checked
   [example](../user/examples/index.md), or
   [Semantic IR reference](../user/reference/semantic-ir.md) as needed.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/
PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py
PYTHONPATH=. pytest -q tests/fortran/semantic_ir/semantics/
```

### Add Or Change Datatype Mapping

Example target: map a new Fortran kind or compiler-probed storage fact.

<!-- PRIK_C_DOCS_START
Example target: map a new Fortran kind, C typedef, or target-probed C type.
PRIK_C_DOCS_END -->

1. Add conversion coverage in `tests/fortran/semantic_ir/semantics/`.
2. Implement the mapping in `prik/semantics/fortran2ir.py`.
3. Keep the public semantic dtype names in `prik/semantics/models.py` stable unless
   there is a deliberate schema decision.
4. If the emitted `.pyi` annotation changes, update
   `tests/fortran/semantic_pyi_format/pipeline/` and
   `tests/fortran/semantic_pyi_format/parsing/`.
5. Update the datatype tables in
   [Semantic IR reference](../user/reference/semantic-ir.md), and update the
   relevant [User Guide](../user/guide/index.md) or checked
   [example](../user/examples/index.md) when a visible example changes.

<!-- PRIK_C_DOCS_START
1. Add conversion coverage in `tests/fortran/semantic_ir/semantics/` or
   `tests/c/semantics/conversion/`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
2. Implement the mapping in `prik/semantics/fortran2ir.py` or `prik/semantics/c2ir.py`.
PRIK_C_DOCS_END -->

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/fortran/semantic_ir/semantics/
PYTHONPATH=. pytest -q tests/fortran/semantic_pyi_format/pipeline/ tests/fortran/semantic_pyi_format/parsing/
```

<!-- PRIK_C_DOCS_START
```bash
PYTHONPATH=. pytest -q tests/fortran/semantic_ir/semantics/ tests/c/semantics/conversion/
PYTHONPATH=. pytest -q tests/fortran/semantic_pyi_format/pipeline/ tests/fortran/semantic_pyi_format/parsing/
```
PRIK_C_DOCS_END -->

### Add `.pyi` Syntax Or Projection Behavior

Example target: add a new `Annotated[...]` metadata item or projection helper.

1. Add loader tests in `tests/fortran/semantic_pyi_format/parsing/`.
2. Update `prik/semantics/pyi2ir.py`. Update `prik/pipeline/pyi.py`
   when loading or cross-file reconciliation changes. Update
   `prik/parsers/pyi/parser.py` only when the raw Python AST parsing boundary
   changes.
3. Add printer tests in `tests/fortran/semantic_pyi_format/pipeline/`.
4. Update `prik/wrapper_codegen/printers/pyi_printer.py`.
5. Update semantic models in `prik/semantics/models.py` only if the IR needs a new
   field or constraint.
6. Update policy completion or wrapper planning if the syntax changes a
   completed decision.
7. Update [Semantic IR reference](../user/reference/semantic-ir.md), plus the
   relevant [User Guide](../user/guide/index.md) or checked
   [example](../user/examples/index.md) when users need the new syntax in a
   workflow.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/fortran/semantic_pyi_format/parsing/
PYTHONPATH=. pytest -q tests/fortran/semantic_pyi_format/pipeline/
PYTHONPATH=. pytest -q tests/fortran/semantic_ir/semantics/ tests/fortran/infrastructure/wrapper_codegen/
```

### Add A Stage-Owned Error

Example target: report a new unsupported Fortran semantic contract clearly.

<!-- PRIK_C_DOCS_START
Example target: report a new unsupported C/Fortran semantic contract clearly.
PRIK_C_DOCS_END -->

1. Preserve the source fact in the parser if it is not already present.
2. Raise a semantic-conversion error when no valid contract can be formed; do
   not attach a deferred diagnostic payload.
3. If the source facts are valid but a selected wrapper behavior is unsafe,
   express that result in completed policy and let the planner name the owner
   path and reason.
4. Add a focused conversion, policy, or wrapper-plan test at that owning
   stage.
5. Update the relevant user guide and [Error Handling](../user/guide/error-handling.md)
   when users can correct the source or edited `.pyi` contract.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/fortran/semantic_ir/semantics/
PYTHONPATH=. pytest -q tests/fortran/semantic_ir/semantics/
PYTHONPATH=. pytest -q tests/fortran/infrastructure/wrapper_codegen/
```

<!-- PRIK_C_DOCS_START
```bash
PYTHONPATH=. pytest -q tests/c/semantics/conversion/
PYTHONPATH=. pytest -q tests/fortran/infrastructure/wrapper_codegen/
```
PRIK_C_DOCS_END -->

### Add Or Change CLI Behavior

Example target: add a stage option, change output routing, or improve
diagnostic formatting.

1. Add CLI tests in `tests/fortran/command_line_interface/pipeline/` first.
2. Implement shared dispatch and output behavior in `prik/cli.py`.
3. Keep Fortran package-specific CLI behavior in `prik/parsers/fortran/cli.py`.
4. If compiler preprocessing behavior changes, update `prik/pipeline/preprocessing.py`
   and preprocessing tests.
5. Update the relevant [User Guide](../user/guide/index.md) or checked
   [example](../user/examples/index.md) for user-facing commands and this guide
   for developer command maps.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/fortran/command_line_interface/pipeline/
PYTHONPATH=. pytest -q tests/fortran/source_preprocessing/preprocessing/
```

## Testing Map

Use this map when changing one part of the project. Each section shows how to
call that part manually, which focused test file to run, and where to look for
more executable examples. Run the broader suite before merging.

### Pre-Merge Checks

Run the ordinary suite from the repository root before merging. Full
BLAS/LAPACK cases belong to their designated real-library lane:

```bash
PYTHONPATH=. pytest -q -m "not real_library" \
  tests/architecture tests/c tests/fortran tests/shared
```

Run the major suites individually while iterating:

```bash
PYTHONPATH=. pytest -q tests/c
PYTHONPATH=. pytest -q -m "not real_library" tests/fortran
PYTHONPATH=. pytest -q tests/shared
```

As a project policy, do not merge pull requests unless all checks are green.

### Fixture Maintenance

<!-- PRIK_C_DOCS_START
Refresh all C parser project goldens:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
python tests/c/fixtures/parser/generate_c_parser_goldens.py
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Refresh one grouped C fixture project:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
python tests/c/fixtures/parser/generate_c_parser_goldens.py tests/c/fixtures/native/general/math_api.h
```
PRIK_C_DOCS_END -->

Refresh all Fortran parser goldens:

```bash
python tests/fortran/source_parsing/parsing/generate_parser_goldens.py
```

Refresh one Fortran fixture:

```bash
python tests/fortran/source_parsing/parsing/generate_parser_goldens.py tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

In-test Fortran parser fixture update mode:

```bash
FORTRAN_PARSER_UPDATE_GOLDENS=1 PYTHONPATH=. pytest -q \
  tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py
```

Refresh semantic and `.pyi` fixtures:

```bash
python tests/fortran/semantic_ir/semantics/generate_semantic_fixtures.py
WRAPPER_UPDATE_PYI_FIXTURES=1 python3 -m pytest -q tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py
```

When parser model output changes, include the regenerated parser goldens and a
short explanation in the PR. For `.pyi`, semantic IR, policy, or wrapper-planning behavior
changes, update the reviewed contracts under
`tests/fortran/semantic_pyi_format/pipeline/fixtures/contracts/` or
the semantic fixtures under `tests/fortran/semantic_ir/semantics/fixtures`.

<!-- PRIK_C_DOCS_START
### C Parser
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Manual call for one C fixture:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
python -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;json
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Manual Python API call:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik import parse_c_file

parsed = parse_c_file("int add(int a, int b);", filename="example.h")
print([function.name for function in parsed.functions])
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Focused tests by concern:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- Lexer/preprocessor mechanics:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_lexer_preprocessor.py`
- Declarations and declarators:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_declarations_and_declarators.py`
- Functions:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_functions.py`
- Structs, unions, enums, and typedefs:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_structs_unions_enums_typedefs.py`
- Project resolution and cross-file facts:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_project_resolution.py`
- Compiler extensions:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_compiler_extensions.py`
- Fixture project goldens:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_fixture_suite.py`
- Fatal parser diagnostics:
  `PYTHONPATH=. pytest -q tests/c/parsing/test_c_error_fixture_suite.py`
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Regenerate one grouped C fixture project:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
python tests/c/fixtures/parser/generate_c_parser_goldens.py tests/c/fixtures/native/general/math_api.h
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Executable tutorial: `tests/c/parsing/test_c_parser_developer_tutorial.py`.
PRIK_C_DOCS_END -->

### Fortran Parser

Manual call for one Fortran fixture:

```bash
python -m prik parse tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 --language fortran --json
```

Manual Python API call:

```python
from prik import parse_fortran_file

parsed = parse_fortran_file(
    "tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90",
)
print([module.name for module in parsed.modules])
```

Focused tests by concern:

- Parser walkthrough:
  `PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/test_developer_tutorial.py`
- Procedures, declarations, derived types, and interfaces:
  `PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/`
- Scope and project behavior:
  `PYTHONPATH=. pytest -q tests/fortran/modules/parsing/test_scope_handling.py tests/fortran/modules/parsing/test_project_scope_models.py`
- Preprocessing and execution-boundary behavior:
  `PYTHONPATH=. pytest -q tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`
- Parser diagnostics:
  `PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/test_error_handling.py`
- Fixture goldens:
  `PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py`
- Parser error fixtures:
  `PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/test_error_fixture_suite.py`

Regenerate one Fortran fixture:

```bash
python tests/fortran/source_parsing/parsing/generate_parser_goldens.py tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

Executable tutorial: `tests/fortran/source_parsing/parsing/test_developer_tutorial.py`.

### Semantics And `.pyi`

Manual calls:

<!-- PRIK_C_DOCS_START
```bash
python -m prik tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 &#45;&#45;semantics
python -m prik tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 &#45;&#45;pyi
python -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;semantics
python -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;pyi
```
PRIK_C_DOCS_END -->

Focused tests by concern:

- Fortran parser-to-IR conversion:
  `PYTHONPATH=. pytest -q tests/fortran/semantic_ir/semantics/`
- Wrapper-plan support diagnostics:
  `PYTHONPATH=. pytest -q tests/fortran/infrastructure/wrapper_codegen/`
- `.pyi` printer:
  `PYTHONPATH=. pytest -q tests/fortran/semantic_pyi_format/pipeline/`
- `.pyi` loader and edited stub behavior:
  `PYTHONPATH=. pytest -q tests/fortran/semantic_pyi_format/parsing/`
- Semantic and `.pyi` fixtures:
  `PYTHONPATH=. pytest -q tests/fortran/semantic_pyi_format/pipeline/test_contract_loading.py`

<!-- PRIK_C_DOCS_START
- C parser-to-IR conversion:
  `PYTHONPATH=. pytest -q tests/c/semantics/conversion/`
PRIK_C_DOCS_END -->

Regenerate semantic and `.pyi` fixtures:

```bash
python tests/fortran/semantic_ir/semantics/generate_semantic_fixtures.py
WRAPPER_UPDATE_PYI_FIXTURES=1 python3 -m pytest -q tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py
```

Executable examples: `tests/fortran/semantic_pyi_format/pipeline/` and
`tests/fortran/semantic_pyi_format/parsing/`.

### CLI

Manual calls:

<!-- PRIK_C_DOCS_START
```bash
python -m prik tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 &#45;&#45;parse
python -m prik tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 &#45;&#45;semantics
python -m prik tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 &#45;&#45;pyi
python -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;parse
```
PRIK_C_DOCS_END -->

Focused tests:

- Full CLI behavior:
  `PYTHONPATH=. pytest -q tests/fortran/command_line_interface/pipeline/`
- Stage dispatch:
  `PYTHONPATH=. pytest -q tests/fortran/command_line_interface/pipeline/ -k "parse or semantics or pyi or wrap"`
- Language and preprocessing selection:
  `PYTHONPATH=. pytest -q tests/fortran/command_line_interface/pipeline/ -k "language or preprocessing"`

Executable reference: `tests/fortran/command_line_interface/pipeline/`.
