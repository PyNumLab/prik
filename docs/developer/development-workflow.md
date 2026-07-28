---
title: Development Workflow
audience: developers, contributors
prerequisites: repository checkout, Python 3.10 or newer
related: index.md, quality-assurance.md
status: maintained
publication: draft
---

# Development Workflow

This guide is for changing x2py. It maps user-visible behavior to its owning
implementation and tests, then gives focused change and verification
workflows.

<!-- X2PY_C_DOCS_START
Use the [tutorial](../user/tutorials/basic-wrapper.md) and [examples cookbook](../user/examples/verified-cookbook.md) to inspect
the public workflows before changing them. This guide is the developer entry
point for the C and Fortran parser references, implementation ownership, and
the detailed maintained contracts.
X2PY_C_DOCS_END -->

## Start Here

Install the project and QA dependencies:

```bash
python3 -m pip install -e ".[qa]"
```

Run the smallest relevant test while iterating, then run the full suite:

```bash
PYTHONPATH=. python3 -m pytest -q tests/cli/
PYTHONPATH=. python3 -m pytest -q
```

Before changing a public behavior, trace it through these layers:

<!-- X2PY_C_DOCS_START
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
X2PY_C_DOCS_END -->

For example, a new CLI stage option normally requires:

1. A focused contract test in `tests/cli/`.
2. Dispatch or output routing in `x2py/cli.py`.
3. Preprocessing tests if the option changes source loading.
4. A copy-paste command in [Verified examples cookbook](../user/examples/verified-cookbook.md).
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
| [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md) | Main supported user workflow and boundaries |
| [Verified examples cookbook](../user/examples/verified-cookbook.md) | Copy-paste commands and Python API recipes |
| [Fortran wrapper reference](../user/reference/fortran-wrapper.md) | Implemented Fortran runtime contract, mechanism, ownership, and build modes |
| [Fortran parser reference](fortran-parser-reference.md) | Developer inventory for the Fortran frontend |
| [Semantic IR reference](../user/reference/semantic-ir.md) | Accepted semantic IR and datatype contract |
| [Semantic .pyi format](../user/reference/semantic-pyi-format.md) | User-visible semantic `.pyi` syntax and roadmap |

<!-- X2PY_C_DOCS_START
| [C parser reference](c-parser-reference.md) | Developer inventory for the C frontend |
X2PY_C_DOCS_END -->

When adding a user example:

1. Prefer a checked repository fixture or a short inline source string.
2. Run the command or snippet from the repository root.
3. Add or identify the focused test that owns the behavior.
4. State limitations next to the example when metadata is preserved but not
   executed, such as `@native_call` projection metadata.

<!-- X2PY_C_DOCS_START
5. Distinguish the implemented source-driven Fortran wrapper from deferred
   workflows such as C-input wrapping, direct edited-`.pyi` CLI builds, and
   arbitrary Pythonic projection execution.
X2PY_C_DOCS_END -->

### Automatically Verify Markdown Examples

`tests/docs/test_examples.py` executes explicitly marked
`bash` CLI examples and `python` API snippets from `README.md` and Markdown
files under `docs/`. Bash examples must be `python3 -m x2py` commands; the test replaces `python3`
with the active test interpreter and runs them without a shell. It rejects
shell operators, output-writing options, and options that select custom
executables or preprocessing command templates. Python snippets run with the
active test interpreter.

Wrapper examples that need native compilation should use
`build_fortran_extension` with `TemporaryDirectory` so verification does not
leave build artifacts in the checkout.

Mark a command that only needs to exit successfully:

````markdown
<!-- x2py-doc-test: run -->
```bash
python3 -m x2py semantics tests/data/fortran/general/basic_subroutine.f90
```
````

Mark a command whose stdout must match the documentation exactly:

````markdown
<!-- x2py-doc-test: exact -->
```bash
python3 -m x2py parse tests/data/fortran/general/basic_subroutine.f90
```

<!-- x2py-doc-test-output -->
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
<!-- x2py-doc-source: tests/data/fortran/general/basic_subroutine.f90 -->
```fortran
module m1
...
end module m1
```
````

Append a target profile to an exact marker only for compiler-generated output
that is intentionally architecture-specific:

```markdown
<!-- x2py-doc-test: exact linux-x86_64 -->
```

Off-target checks are skipped. The matching profile must still run the command
and compare its complete output.

Run the documentation checks directly:

```bash
PYTHONPATH=. python3 -m pytest -q tests/docs/test_examples.py
```

## References

- [Tutorial](../user/tutorials/basic-wrapper.md): supported end-to-end user workflow and current
  boundaries.
- [Verified examples cookbook](../user/examples/verified-cookbook.md): CLI and Python API recipes.
- [Fortran parser reference](fortran-parser-reference.md): Fortran frontend scope,
  recursive parser organization, API/CLI behavior, diagnostics, fixture
  workflow, semantic handoff, and tests.
- [Semantic `.pyi` format](../user/reference/semantic-pyi-format.md): user-visible `.pyi`
  loader/printer contract and roadmap.
- [Quality assurance](quality-assurance.md): active QA commands, tool benefits, known
  defects found by each tool, and scheduled triage process.

<!-- X2PY_C_DOCS_START
- [C parser reference](c-parser-reference.md): C frontend scope, preprocessing and
  project policy, parser architecture, CLI behavior, semantic handoff,
  fixtures, and tests.
- [Semantic IR reference](../user/reference/semantic-ir.md): shared semantic model, datatype
  policy, and C conversion facts.
X2PY_C_DOCS_END -->

## User-Facing Contract Internals

The tutorial, examples cookbook, `.pyi` format, and semantic reference describe
CLI stages, `.pyi` syntax, datatype names, and wrapper-plan diagnostics. The developer
task is to keep those user-visible contracts stable, tested, and traceable to
implementation files.

### Source Ownership Map

| User-visible area | Main implementation files | Main tests |
| --- | --- | --- |
| Fortran parse output | `x2py/parsers/fortran/parser.py`, `x2py/parsers/fortran/models.py`, `x2py/parsers/fortran/lexer.py` | `tests/parsing/fortran/`, `tests/parsing/fortran/test_fortran_fixture_suite.py`, `tests/parsing/fortran/test_error_handling.py` |
| CLI stage selection and output | `x2py/cli.py`, `x2py/parsers/fortran/cli.py` | `tests/cli/` |
| Fortran target type probing and cache | `x2py/probes/fortran_types.py` | `tests/probes/test_fortran_types.py` |
| Generated target datatype mapping examples | `x2py/probes/report.py` | `tests/types/test_mapping_report.py`, `tests/docs/test_examples.py` |
| Fortran to semantic IR | `x2py/semantics/fortran2ir.py`, `x2py/semantics/models.py` | `tests/semantics/conversion/fortran/` |
| `.pyi` printing | `x2py/wrapper_codegen/printers/pyi_printer.py` | `tests/wrapper_codegen/printers/`, `tests/wrapper_codegen/printers/test_modern_example.py` |
| `.pyi` parsing/loading/editing | `x2py/parsers/pyi/parser.py`, `x2py/pipeline/pyi.py`, `x2py/semantics/pyi2ir.py` | `tests/parsing/pyi/`, `tests/pipeline/pyi_builds/test_contract_fixtures.py` |
| Semantic policy completion | `x2py/semantics/policy_completion.py`, `x2py/semantics/ownership.py` | `tests/semantics/policy/` |
| Fortran wrapper orchestration | `x2py/pipeline/build.py` | `tests/wrapper/fortran/build_from_source/test_build_modes.py`, `tests/wrapper/fortran/multiple_files/test_multi_source_builds.py` |
| Wrapper planning, owner-local errors, and direct lowering | `x2py/wrapper_codegen/plan.py`, `x2py/wrapper_codegen/planner.py`, `x2py/wrapper_codegen/generator.py` | `tests/wrapper_codegen/`, `tests/wrapper/` |
| Native compilation and binding support | `x2py/compiling/`, `x2py/binding_support/` | `tests/wrapper/fortran/build_from_source/test_runtime_abi.py`, `tests/wrapper/fortran/build_from_source/test_build_modes.py` |
| Executable Markdown examples | `README.md`, `docs/*.md` | `tests/docs/test_examples.py` |

<!-- X2PY_C_DOCS_START
| C parse output | `x2py/parsers/c/parser.py`, `x2py/parsers/c/models.py`, `x2py/parsers/c/lexer.py` | `tests/parsing/c/test_c_declarations_and_declarators.py`, `tests/parsing/c/test_c_fixture_suite.py`, `tests/parsing/c/test_c_error_fixture_suite.py` |
| Compiler preprocessing | `x2py/pipeline/preprocessing.py` | `tests/pipeline/preprocessing/`, `tests/pipeline/preprocessing/test_parser_boundaries.py`, `tests/parsing/c/test_c_lexer_preprocessor.py` |
| C target ABI probing and cache | `x2py/probes/c_types.py` | `tests/probes/test_c_types.py` |
| C to semantic IR | `x2py/semantics/c2ir.py`, `x2py/semantics/models.py` | `tests/semantics/conversion/c/` |
| Fortran-to-C bridge and CPython binding | `x2py/wrapper_codegen/fortran/bridge.py`, `x2py/wrapper_codegen/c/binding.py` | `tests/wrapper_codegen/`, `tests/wrapper/` subject suites |
| Public API exports | `x2py/__init__.py` | `tests/parsing/fortran/test_public_entrypoints.py`, `tests/parsing/c/test_c_public_api_skeleton.py` |
X2PY_C_DOCS_END -->

### Wrapper Generator Class Organization

<!-- X2PY_C_DOCS_START
Current runtime wrapper codegen is intentionally narrow: Fortran sources lower
through the generated Fortran bridge, generated C, and the CPython extension
binding. Semantic `.pyi` emission is the editable contract printer. Do not keep
placeholder C++, pybind11, or Python source printers until
those backends have a documented runtime contract and tests.
X2PY_C_DOCS_END -->

Organize generators and printers using `FortranParser` in
`x2py/parsers/fortran/parser.py` as the structural reference. A developer
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

All model-type dispatch goes through `x2py.utilities.visitor.ClassVisitor._visit` and a
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
`x2py/parsers/pyi/parser.py`, loaded from text/files by
`x2py/pipeline/pyi.py`, converted to semantic IR by
`x2py/semantics/pyi2ir.py`, and printed by
`x2py/wrapper_codegen/printers/pyi_printer.py`. The converter and printer operate on
`x2py/semantics/models.py`.

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
<!-- X2PY_C_DOCS_START
- Plain multidimensional C `.pyi` arrays use `ORDER_C`; generated contracts
  omit that language default and retain only an intentional alternate layout.
X2PY_C_DOCS_END -->
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

1. Add or update parser tests in `tests/parsing/pyi/`.
2. Add or update printer tests in `tests/wrapper_codegen/printers/`.
3. Update fixture tests only if the public generated contract changes.
4. Update [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md) or [Verified examples cookbook](../user/examples/verified-cookbook.md) if users
   need to write or read the new syntax.
5. Update [Semantic .pyi format](../user/reference/semantic-pyi-format.md) for the full user-facing reference.
6. Update [Semantic IR reference](../user/reference/semantic-ir.md) if the underlying semantic IR contract
   changes.

### Datatype Mapping Internals

User-visible datatype names are semantic names, not raw parser spellings.
Mapping happens during parser-to-IR conversion:

- Fortran intrinsic/kind mapping and compiler storage-fact application live in
  `x2py/semantics/fortran2ir.py`.
- The shared dtype names and storage contracts live in `x2py/semantics/models.py`.
- Compiler-measured mapping snapshots are generated by
  `x2py/probes/report.py`.

<!-- X2PY_C_DOCS_START
- C primitive, typedef, and probe-aware mapping lives in `x2py/semantics/c2ir.py`.
X2PY_C_DOCS_END -->

When changing datatype mapping:

1. Add focused Fortran conversion tests in
   `tests/semantics/conversion/fortran/`.
2. Add `.pyi` printer/loader coverage if the emitted syntax changes.
3. Update semantic fixtures only when serialized semantic IR intentionally
   changes.
4. Update [Semantic IR reference](../user/reference/semantic-ir.md), plus
   [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md) or [Verified examples cookbook](../user/examples/verified-cookbook.md) when the visible
   user workflow or examples change.
5. Regenerate and update the exact target mapping snapshots in
   [Semantic IR reference](../user/reference/semantic-ir.md). The executable documentation test must match
   the complete output of:

<!-- X2PY_C_DOCS_START
1. Add focused conversion tests in `tests/semantics/conversion/fortran/` or
   `tests/semantics/conversion/c/`.
X2PY_C_DOCS_END -->

   ```bash
   python3 -m x2py probe --language fortran --compiler gfortran --format markdown
   ```

<!-- X2PY_C_DOCS_START
   ```bash
   python3 -m x2py probe &#45;&#45;language c &#45;&#45;compiler cc &#45;&#45;format markdown
   python3 -m x2py probe &#45;&#45;language fortran &#45;&#45;compiler gfortran &#45;&#45;format markdown
   ```
X2PY_C_DOCS_END -->

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

The user-facing stages all start in `x2py/cli.py`, but each stage owns a
different layer of the pipeline.

<!-- X2PY_C_DOCS_START
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
X2PY_C_DOCS_END -->

### CLI And Language Resolution

`x2py/cli.py` is the shared command-line entrypoint. It is responsible for:

- rejecting ambiguous directories and unknown suffixes without `--language`;
- building `PreprocessingConfig`;
- dispatching `parse`, `semantics`, `generate`, and `probe`;
- defaulting recognizable Fortran sources to a wrapper build when no
  subcommand is selected;
- routing the default build and `generate --sources|--makefile` through
  `x2py/pipeline/build.py`;
- routing text, JSON, and `--out` output.

<!-- X2PY_C_DOCS_START
- choosing Fortran or C from `&#45;&#45;language` and file suffixes;
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Recognizable Fortran files and `.pyi` wrapper inputs can omit `&#45;&#45;language`.
C files and directories require explicit language selection. Keep this behavior
tested in `tests/cli/` whenever stage selection changes.
X2PY_C_DOCS_END -->

The package-specific `x2py/parsers/fortran/cli.py` remains for the Fortran parser
package entrypoint. New cross-language user behavior normally belongs in
`x2py/cli.py`.

### Preprocessing Internals

`x2py/pipeline/preprocessing.py` owns compiler-backed preprocessing and provenance. The
main value object is `PreprocessingConfig`; the main execution path is
`run_compiler_preprocessor_with_recipe(...)`.

Important contracts:

- The preprocessing recipe is part of the parser payload when preprocessing
  happened. It records compiler, adapter, argv, include directories, defines,
  undefs, standard, extra compiler args, included files, source mappings, and
  diagnostics.

<!-- X2PY_C_DOCS_START
- CLI source parsing uses compiler mode. C defaults to `cc`; Fortran defaults
  to `gfortran` unless the user passes a compiler, compile database, or custom
  template.
- C direct parser entrypoints can still be used on raw strings or already
  controlled source in Python tests.
- C preprocessing uses GCC/Clang-style `-E -x c` for direct compiler mode.
  Fortran direct compiler mode uses `-E -cpp` plus source-form hints where
  needed.
- Native Fortran `include "..."` is expanded after compiler CPP output because
  it is Fortran textual inclusion, not C/CPP include semantics.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
When changing preprocessing behavior, update
`tests/pipeline/preprocessing/`, source-boundary tests in
`tests/pipeline/preprocessing/test_parser_boundaries.py`, and C raw
directive tests in `tests/parsing/c/test_c_lexer_preprocessor.py`.
X2PY_C_DOCS_END -->

### Source Loading To Semantic IR Paths

Keep source loading, parser models, and semantic conversion separate. Semantic
converters accept parsed models; they must not hide compiler preprocessing or
source loading inside conversion helpers.

Fortran direct Python API, no CPP/FPP macros:

```python
from x2py import parse_fortran_file
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

from x2py import parse_fortran_file
from semantics.fortran2ir import fortran_file_to_semantic_modules
from x2py.pipeline.preprocessing import PreprocessingConfig, preprocess_source

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

<!-- X2PY_C_DOCS_START
C direct Python API, no macro expansion needed:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```python
from x2py import parse_c_file
from semantics.c2ir import c_file_to_semantic_modules

parsed = parse_c_file("int add(int a, int b);", filename="api.h")
modules = c_file_to_semantic_modules(parsed)
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
C raw mode records include and pragma metadata and accepts simple include
guards. Macro-shaped directives such as `#if`, `#ifdef`, `#define` outside a
trivial include guard, and `#error` require compiler preprocessing and are
rejected with `CPARSE_PREPROCESSING_REQUIRED`.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
C with macros follows the compiler-preprocessed path, then parses the expanded
translation unit in `compiler` or `preprocessed` mode:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```python
from pathlib import Path

from c_parser.cli import attach_preprocessing_recipe
from x2py import parse_c_file
from semantics.c2ir import c_file_to_semantic_modules
from x2py.pipeline.preprocessing import PreprocessingConfig, preprocess_source

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
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
The C semantic converter can turn recorded object-like numeric macros into
semantic constant variables. Function-like macros and untyped macro bodies are
not wrapper-callable declarations. Declarations that depend on macros which
were recorded but not expanded remain explicit semantic facts rather than
being treated as complete wrapper contracts.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
For CLI code, do not reimplement these paths manually. `x2py/cli.py` builds
the `PreprocessingConfig`, loads or preprocesses source, attaches C
preprocessing recipes, parses, runs target type probes when configured, and
then dispatches to the semantic helpers.
X2PY_C_DOCS_END -->

### Semantic, `.pyi`, Wrapper-Planning, And Type-Probe Paths

<!-- X2PY_C_DOCS_START
The semantic stages share one rule: source inputs become semantic IR before
anything emits `.pyi` or builds a wrapper plan. Edited `.pyi` inputs are already a
semantic contract and do not go back through C or Fortran parsing.
X2PY_C_DOCS_END -->

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

<!-- X2PY_C_DOCS_START
- `parse_c_file(source_or_path, filename=...)` accepts inline source text or
  an existing file path. Existing paths are read from disk; `filename` can
  still override the diagnostic/source name.
- `parse_fortran_project(...)` and `parse_c_project(...)` accept an in-memory
  mapping of `filename -> source`, an explicit file/path list, or a directory.
  Fortran directory parsing discovers supported Fortran files and orders them
  by module dependencies. C directory parsing discovers supported C files and
  records include graph facts; include directives do not recursively open more
  files.
X2PY_C_DOCS_END -->

CLI source stages:

<!-- X2PY_C_DOCS_START
```text
source path(s)
  -> x2py/cli.py language resolution
  -> PreprocessingConfig
  -> raw source or compiler-preprocessed source
  -> CFile / FortranFile parser model
  -> C or Fortran semantic IR
  -> optional .pyi emission
  -> optional `.pyi` emission or wrapper-plan build
```
X2PY_C_DOCS_END -->

CLI `.pyi` wrapper build:

```text
.pyi path(s) or directory
  -> x2py/parsers/pyi/parser.py
  -> x2py/pipeline/pyi.py pyi_paths_to_semantic_modules(...)
  -> x2py/semantics/pyi2ir.py
  -> SemanticModule list
  -> x2py/semantics/policy_completion.py
  -> complete_semantic_policies(...)
  -> WrapperPlanner.build(...)
```

Generating `.pyi` from source is semantic conversion plus printing. In Python
API code, keep those calls visible:

```python
from x2py import emit_module_stubs, parse_fortran_file
from semantics.fortran2ir import fortran_file_to_semantic_modules

parsed = parse_fortran_file(source, filename="api.f90")
modules = fortran_file_to_semantic_modules(parsed)
stubs = emit_module_stubs(modules)
```

<!-- X2PY_C_DOCS_START
For C, the same shape uses `parse_c_file(...)` or `parse_c_project(...)`,
then `c_file_to_semantic_modules(...)` or
`c_project_to_semantic_modules(...)`, then `emit_module_stubs(...)`.
X2PY_C_DOCS_END -->

Loading or editing `.pyi` is the opposite direction:

```python
from x2py import pyi_paths_to_semantic_modules

modules = pyi_paths_to_semantic_modules("interfaces")
```

Use the `.pyi` helpers by input shape:

- `parse_pyi_text(source, filename=...)` from `x2py.parsers.pyi` for parser-only
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

<!-- X2PY_C_DOCS_START
Do not run compiler preprocessing, C ABI probes, or Fortran type probes for an
edited `.pyi` wrapper build. Once `.pyi` has been loaded, the edited semantic
IR is the source of truth.
X2PY_C_DOCS_END -->

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

<!-- X2PY_C_DOCS_START
| `&#45;&#45;compile-commands` | `compile_commands` | Project compile database; automatic C ABI probing is not allowed from this mixed recipe. |
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
`preprocess_source(...)` returns expanded source and a recipe. The C parser
needs `preprocessing="compiler"` or `"preprocessed"` for that expanded source,
and CLI code attaches the recipe with `attach_preprocessing_recipe(...)` so
macro metadata can reach semantic conversion. Fortran consumes the expanded
source with `parse_fortran_file(...)`; the parse-stage CLI payload records the
recipe separately.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
C target datatype mapping path:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```text
C source
  -> parse_c_project(...)
  -> optional C standard type report
  -> c_project_to_semantic_modules(..., standard_type_report=...)
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
For direct-compiler C semantic and `.pyi` stages, `x2py/cli.py` runs
`probe_c_standard_types_cached(...)` internally and passes the measured facts
to `x2py/semantics/c2ir.py`. The public `x2py probe` command exposes the report
as an inspection output; semantic stages do not accept that report as a second
input path. Probe execution, cache, and refresh policy belong to
`x2py/probes/c_types.py`.
X2PY_C_DOCS_END -->

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

<!-- X2PY_C_DOCS_START
The CLI performs those probe steps internally for Fortran semantic, `.pyi`, and
wrapper-build stages when a direct Fortran compiler is configured.
`compile_time_values` resolve symbolic parameters and kind expressions.
`type_facts` measure compiler-dependent intrinsic storage, such as default
integer width or target-changing flags. Source-driven wrapper builds derive the
probe configuration from preprocessing plus the native Fortran compiler flags;
this keeps flags such as `-fdefault-real-8` aligned between semantic lowering
and native compilation. The standalone `x2py probe` report is an inspection and
verification output, not an alternate semantic-stage input.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Generated datatype mapping reports are documentation and verification outputs,
not a separate parse path. `x2py/probes/report.py` uses the C and Fortran
converter/probe machinery to print target-specific mapping examples for
`docs/user/reference/semantic-ir.md`; changes there need both semantic conversion tests and
documentation-example verification.
X2PY_C_DOCS_END -->

### Fortran Runtime Wrapper Path

`x2py/pipeline/build.py::build_fortran_extension(...)` and
`x2py/pipeline/build.py::build_pyi_extension(...)` are the public orchestration
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

- `x2py/pipeline/build.py`: source order, preprocessing/probing, semantic merge,
  `.pyi` entry-contract loading, native build plan assembly, output placement,
  direct-versus-Makefile mode, and artifact reporting;
- `x2py/wrapper_codegen/planner.py`: projection from completed semantic policy
  into validated typed plans;
- `x2py/wrapper_codegen/generator.py`: direct bridge, binding, and source
  artifact generation;
- `x2py/compiling/`: compiler commands and shared-library linking; and
- `x2py/binding_support/`: native binding support copied into each build.

<!-- X2PY_C_DOCS_START
- `x2py/wrapper_codegen/fortran/bridge.py`: Fortran-to-C ABI adaptation;
- `x2py/wrapper_codegen/c/binding.py`: Python argument/result conversion,
  reference handling, and CPython wrapper construction;
- `x2py/wrapper_codegen/printers/source_printers.py`: source rendering only;
X2PY_C_DOCS_END -->

Do not move semantic ownership or projection policy into printers. Do not infer
source dependencies: multi-source source builds compile in caller order, and
the first semantic module names the merged extension. `.pyi` builds use exactly
one semantic entry contract plus a separate extension-level
`NativeBuildPlan`; they must not recover Python API facts by reparsing native
implementation sources. `--makefile` records the compiler/linker plan
without executing it; for `.pyi` builds, `x2py-build.json` is written first and
`Makefile.x2py` is projected from that manifest.

<!-- X2PY_C_DOCS_START
Generated `bind_c_<module>` Fortran bridges are a C ABI implementation detail,
not a Fortran-use API. They therefore do not emit a default `private` statement
or one `public :: ...` line per generated wrapper procedure. Python exposure is
owned by the C extension method table; the bridge only marks the allocator
interface name `c_malloc` private to avoid exporting that helper through Fortran
module use association.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
The current runtime build surface is Fortran-focused. Edited `.pyi` files can
drive `.pyi` wrapper builds when the caller supplies explicit native artifacts,
but full generated-contract parity is still tracked in the roadmap. User C
inputs currently stop at semantic conversion; their runtime backend is future
work even though the Fortran wrapper internally emits C source.
X2PY_C_DOCS_END -->

Runtime verification belongs in `tests/wrapper`. The subject index in
[`tests/wrapper/fortran/README.md`](../../tests/wrapper/fortran/README.md) maps generated behavior
to compiled/imported tests. Build-mode changes should at least cover
`test_build_modes.py`, `multiple_files/test_multi_source_builds.py`, and
the affected runtime subject test.

### Parser Model Internals

Parser models are source facts. They should answer "what did the source say?"
rather than "what Python wrapper should be generated?"

Fortran:

- `x2py/parsers/fortran/parser.py` slices the file into grammar units, then parses
  each unit's specification region.
- `x2py/parsers/fortran/models.py` stores `FortranFile`, modules, procedures,
  variables, derived types, interfaces, programs, submodules, and diagnostics.
- Execution bodies are intentionally skipped after the parser has enough
  signature/source facts.

<!-- X2PY_C_DOCS_START
C:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
- `x2py/parsers/c/lexer.py` handles comments, directives, top-level splitting, and
  token source locations.
- `x2py/parsers/c/parser.py` visits declarations and declarators, records typed
  source facts, and reports unsupported parser-owned syntax.
- `x2py/parsers/c/models.py` stores functions, variables, typedefs, structs, unions,
  enums, includes, raw directives, preprocessing facts, and diagnostics.
X2PY_C_DOCS_END -->

Adding parser fields is a schema decision. Add fields only when downstream
semantic conversion, fixtures, diagnostics, or user-visible behavior need a
new fact.

### Semantic IR Internals

The semantic layer normalizes Fortran facts into language-neutral models from
`x2py/semantics/models.py`.

<!-- X2PY_C_DOCS_START
The semantic layer normalizes C and Fortran facts into language-neutral models
from `x2py/semantics/models.py`.
X2PY_C_DOCS_END -->

- `x2py/semantics/fortran2ir.py` maps Fortran procedures, derived types, module
  variables, kinds, shapes, storage contracts, visibility, imported references,
  and compile-time values.
- `x2py/wrapper_codegen/printers/pyi_printer.py` emits editable user contracts.
- `x2py/parsers/pyi/parser.py` parses edited contracts to Python AST.
- `x2py/pipeline/pyi.py` converts edited contract text, files, and path sets.
- `x2py/semantics/pyi2ir.py` converts parsed `.pyi` AST back into semantic IR.
- `x2py/semantics/native_contract.py` validates immutable native scope, ABI,
  placement, type, callback, and projection facts before source-free codegen.
- Named data bindings keep role-specific semantic types: `SemanticVariable`
  for module variables and constants, `SemanticArgument` for callable
  parameters, and `SemanticField` for Fortran derived-type components.
- `x2py/semantics/policy_completion.py` completes semantic policies after
  Fortran or `.pyi` conversion and before wrapper planning or lowering.

<!-- X2PY_C_DOCS_START
- Named data bindings share a common base but keep role-specific types:
  `SemanticVariable` for module/global variables and macro constants,
  `SemanticArgument` for callable parameters, `SemanticField` for struct,
  union, and Fortran derived-type fields. `SemanticFunction.locals` is the
  reserved home for local variables or local constants if a frontend later
  promotes them into semantic IR; local bindings are not emitted into `.pyi` or
  treated as wrapper interface items by default.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
- `x2py/semantics/c2ir.py` maps C functions, variables, structs/opaque structs,
  enums, typedef chains, standard-type probe facts, macros, pointer/array
  storage, and C-specific semantic facts.
- C `int` keeps the semantic name `Int` while its compiler-probed concrete
  precision is stored on the semantic type. C and Fortran enums lower to
  unscoped module-level integer constants; enum names are metadata, not
  semantic datatypes.
- `x2py/semantics/policy_completion.py` completes semantic policies after
  C/Fortran/`.pyi` conversion and before wrapper planning or lowering.
X2PY_C_DOCS_END -->

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

- loader syntax and error behavior: `tests/parsing/pyi/`;
- printer round-trip shape: `tests/wrapper_codegen/printers/`;
- policy-completion decisions: `tests/semantics/policy/`;
- wrapper-plan diagnostics: `tests/wrapper_codegen/`.

<!-- X2PY_C_DOCS_START
- C semantic conversion: `tests/semantics/conversion/c/`.
X2PY_C_DOCS_END -->

When adding projection syntax, first add loader tests that prove the accepted
syntax and rejected syntax. Then add policy or wrapper-plan tests only if the
new metadata affects those layers.

## Testing Strategy

Use the smallest test layer that proves the behavior, then add broader
coverage only when the public contract changes.

### Test Layers

| Layer | Purpose | Typical files |
| --- | --- | --- |
| Focused parser tests | One construct, diagnostic, or model field | `tests/parsing/fortran/test_*.py` |
| Parser fixture goldens | Serialized Fortran parser contracts | `tests/parsing/fortran/test_fortran_fixture_suite.py` |
| Semantic tests | Fortran parser facts converted to wrapper-neutral IR | `tests/semantics/conversion/fortran/` |
| Policy tests | Completed policy decisions | `tests/semantics/policy/` |
| Wrapper-plan tests | Unsupported plan diagnostics and generated plan shape | `tests/wrapper_codegen/` |
| `.pyi` tests | Editable contract loader/printer behavior | `tests/parsing/pyi/`, `tests/wrapper_codegen/printers/` |
| CLI tests | User commands, output routing, diagnostics | `tests/cli/`, `tests/pipeline/preprocessing/` |
| Wrapper build tests | Artifact placement, direct/Makefile modes, multi-source ordering | `tests/wrapper/fortran/build_from_source/test_build_modes.py`, `tests/wrapper/fortran/multiple_files/` |
| Wrapper runtime tests | Imported extension behavior, ownership, lifetime, and failures | `tests/wrapper/` subject suites indexed by `tests/wrapper/fortran/README.md` |
| Property/fuzz tests | Broad parser robustness invariants | `tests/parsing/`, `tests/semantics/conversion/` |

<!-- X2PY_C_DOCS_START
| Semantic tests | Parser facts converted to wrapper-neutral IR | `tests/semantics/conversion/fortran/`, `tests/semantics/conversion/c/` |
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
| Focused parser tests | One construct, diagnostic, or model field | `tests/parsing/fortran/test_*.py`, `tests/parsing/c/test_*.py` |
| Parser fixture goldens | Serialized parser contract over curated files | `tests/parsing/fortran/test_fortran_fixture_suite.py`, `tests/parsing/c/test_c_fixture_suite.py` |
X2PY_C_DOCS_END -->

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

<!-- X2PY_C_DOCS_START
```bash
python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
python tests/parser/fortran/generate_fortran_parser_goldens.py tests/data/fortran/general/basic_subroutine.f90
python tests/semantics/generate_semantic_fixtures.py
python tests/pyi/generate_pyi_fixtures.py
```
X2PY_C_DOCS_END -->

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

<!-- X2PY_C_DOCS_START
### Add A C Declaration Feature
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Example target: support a new declaration spelling or compiler extension in
the C parser.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
1. Add the smallest source example to a focused C parser test:
   `tests/parsing/c/test_c_declarations_and_declarators.py`,
   `tests/parsing/c/test_c_compiler_extensions.py`, or
   `tests/parsing/c/test_c_structs_unions_enums_typedefs.py`.
2. Implement the parser change in `x2py/parsers/c/parser.py`. Add or update model
   fields in `x2py/parsers/c/models.py` only if the serialized parser contract needs
   new facts.
3. If source splitting or raw directive handling changes, update
   `x2py/parsers/c/lexer.py` and `tests/parsing/c/test_c_lexer_preprocessor.py`.
4. If project-level resolution changes, update
   `tests/parsing/c/test_c_project_resolution.py`.
5. If parser JSON changes intentionally, regenerate the relevant project
   golden:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
   ```bash
   python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
   ```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
6. If the new parser fact affects semantic conversion, update
   `x2py/semantics/c2ir.py` and add coverage in `tests/semantics/conversion/c/`.
7. If the generated `.pyi` changes, update `tests/wrapper_codegen/printers/`
   or `tests/pipeline/pyi_builds/test_contract_fixtures.py`.
8. Update [C parser reference](c-parser-reference.md), [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md),
   [Verified examples cookbook](../user/examples/verified-cookbook.md), or [Semantic IR reference](../user/reference/semantic-ir.md) if users or
   developers need to know the new behavior.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Focused verification:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
PYTHONPATH=. pytest -q tests/parsing/c/test_c_declarations_and_declarators.py
PYTHONPATH=. pytest -q tests/parsing/c/test_c_project_resolution.py
PYTHONPATH=. pytest -q tests/semantics/conversion/c/
```
X2PY_C_DOCS_END -->

### Add A Fortran Parser Feature

Example target: preserve a new declaration attribute, source fact, or argument
metadata item.

1. Add a focused parser test in the file that owns the behavior:
   `tests/parsing/fortran/`,
   `tests/parsing/fortran/test_scope_handling.py`, or
   `tests/pipeline/preprocessing/test_parser_boundaries.py`.
2. Implement parsing in `x2py/parsers/fortran/parser.py`. Add model fields in
   `x2py/parsers/fortran/models.py` only if the parser output needs to expose the
   new fact.
3. Add parser diagnostic coverage in `tests/parsing/fortran/test_error_handling.py` if
   malformed source should now fail differently.
4. If project ordering, imports, or compile-time values change, update
   `tests/parsing/fortran/test_project_scope_models.py` or
   `tests/probes/test_fortran_types.py`.
5. If serialized parser JSON changes intentionally, regenerate the selected
   fixture:

   ```bash
   python tests/parser/fortran/generate_fortran_parser_goldens.py tests/data/fortran/general/basic_subroutine.f90
   ```

6. If the new fact affects semantic output, update `x2py/semantics/fortran2ir.py`
   and `tests/semantics/conversion/fortran/`.
7. If generated `.pyi` changes, update `tests/wrapper_codegen/printers/`
   and the relevant fixture tests.
8. Update [Fortran parser reference](fortran-parser-reference.md), [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md),
   [Verified examples cookbook](../user/examples/verified-cookbook.md), or [Semantic IR reference](../user/reference/semantic-ir.md) as needed.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/parsing/fortran/
PYTHONPATH=. pytest -q tests/parsing/fortran/test_fortran_fixture_suite.py
PYTHONPATH=. pytest -q tests/semantics/conversion/fortran/
```

### Add Or Change Datatype Mapping

Example target: map a new Fortran kind or compiler-probed storage fact.

<!-- X2PY_C_DOCS_START
Example target: map a new Fortran kind, C typedef, or target-probed C type.
X2PY_C_DOCS_END -->

1. Add conversion coverage in `tests/semantics/conversion/fortran/`.
2. Implement the mapping in `x2py/semantics/fortran2ir.py`.
3. Keep the public semantic dtype names in `x2py/semantics/models.py` stable unless
   there is a deliberate schema decision.
4. If the emitted `.pyi` annotation changes, update
   `tests/wrapper_codegen/printers/` and `tests/parsing/pyi/`.
5. Update the datatype tables in [Semantic IR reference](../user/reference/semantic-ir.md), and update
   [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md) or [Verified examples cookbook](../user/examples/verified-cookbook.md) when a visible
   example changes.

<!-- X2PY_C_DOCS_START
1. Add conversion coverage in `tests/semantics/conversion/fortran/` or
   `tests/semantics/conversion/c/`.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
2. Implement the mapping in `x2py/semantics/fortran2ir.py` or `x2py/semantics/c2ir.py`.
X2PY_C_DOCS_END -->

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/semantics/conversion/fortran/
PYTHONPATH=. pytest -q tests/wrapper_codegen/printers/ tests/parsing/pyi/
```

<!-- X2PY_C_DOCS_START
```bash
PYTHONPATH=. pytest -q tests/semantics/conversion/fortran/ tests/semantics/conversion/c/
PYTHONPATH=. pytest -q tests/wrapper_codegen/printers/ tests/parsing/pyi/
```
X2PY_C_DOCS_END -->

### Add `.pyi` Syntax Or Projection Behavior

Example target: add a new `Annotated[...]` metadata item or projection helper.

1. Add loader tests in `tests/parsing/pyi/`.
2. Update `x2py/semantics/pyi2ir.py`. Update `x2py/pipeline/pyi.py`
   when loading or cross-file reconciliation changes. Update
   `x2py/parsers/pyi/parser.py` only when the raw Python AST parsing boundary
   changes.
3. Add printer tests in `tests/wrapper_codegen/printers/`.
4. Update `x2py/wrapper_codegen/printers/pyi_printer.py`.
5. Update semantic models in `x2py/semantics/models.py` only if the IR needs a new
   field or constraint.
6. Update policy completion or wrapper planning if the syntax changes a
   completed decision.
7. Update [Semantic IR reference](../user/reference/semantic-ir.md), plus [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md) or
   [Verified examples cookbook](../user/examples/verified-cookbook.md) when users need the new syntax in a workflow.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/parsing/pyi/
PYTHONPATH=. pytest -q tests/wrapper_codegen/printers/
PYTHONPATH=. pytest -q tests/semantics/policy/ tests/wrapper_codegen/
```

### Add A Stage-Owned Error

Example target: report a new unsupported Fortran semantic contract clearly.

<!-- X2PY_C_DOCS_START
Example target: report a new unsupported C/Fortran semantic contract clearly.
X2PY_C_DOCS_END -->

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
PYTHONPATH=. pytest -q tests/semantics/conversion/fortran/
PYTHONPATH=. pytest -q tests/semantics/policy/
PYTHONPATH=. pytest -q tests/wrapper_codegen/
```

<!-- X2PY_C_DOCS_START
```bash
PYTHONPATH=. pytest -q tests/semantics/conversion/c/
PYTHONPATH=. pytest -q tests/wrapper_codegen/
```
X2PY_C_DOCS_END -->

### Add Or Change CLI Behavior

Example target: add a stage option, change output routing, or improve
diagnostic formatting.

1. Add CLI tests in `tests/cli/` first.
2. Implement shared dispatch and output behavior in `x2py/cli.py`.
3. Keep Fortran package-specific CLI behavior in `x2py/parsers/fortran/cli.py`.
4. If compiler preprocessing behavior changes, update `x2py/pipeline/preprocessing.py`
   and preprocessing tests.
5. Update [Basic wrapper tutorial](../user/tutorials/basic-wrapper.md) or [Verified examples cookbook](../user/examples/verified-cookbook.md) for
   user-facing commands and this guide for developer command maps.

Focused verification:

```bash
PYTHONPATH=. pytest -q tests/cli/
PYTHONPATH=. pytest -q tests/pipeline/preprocessing/
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

<!-- X2PY_C_DOCS_START
Refresh all C parser project goldens:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
python tests/parser/c/generate_c_parser_goldens.py
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Refresh one grouped C fixture project:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
```
X2PY_C_DOCS_END -->

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

<!-- X2PY_C_DOCS_START
### C Parser
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Manual call for one C fixture:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
python -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;json
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Manual Python API call:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```python
from x2py import parse_c_file

parsed = parse_c_file("int add(int a, int b);", filename="example.h")
print([function.name for function in parsed.functions])
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Focused tests by concern:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
- Lexer/preprocessor mechanics:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_lexer_preprocessor.py`
- Declarations and declarators:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_declarations_and_declarators.py`
- Functions:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_functions.py`
- Structs, unions, enums, and typedefs:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_structs_unions_enums_typedefs.py`
- Project resolution and cross-file facts:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_project_resolution.py`
- Compiler extensions:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_compiler_extensions.py`
- Fixture project goldens:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_fixture_suite.py`
- Fatal parser diagnostics:
  `PYTHONPATH=. pytest -q tests/parsing/c/test_c_error_fixture_suite.py`
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Regenerate one grouped C fixture project:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Executable tutorial: `tests/parsing/c/test_c_parser_developer_tutorial.py`.
X2PY_C_DOCS_END -->

### Fortran Parser

Manual call for one Fortran fixture:

```bash
python -m x2py parse tests/data/fortran/general/basic_subroutine.f90 --language fortran --json
```

Manual Python API call:

```python
from x2py import parse_fortran_file

parsed = parse_fortran_file(
    "tests/data/fortran/general/basic_subroutine.f90",
)
print([module.name for module in parsed.modules])
```

Focused tests by concern:

- Parser walkthrough:
  `PYTHONPATH=. pytest -q tests/parsing/fortran/test_developer_tutorial.py`
- Procedures, declarations, derived types, and interfaces:
  `PYTHONPATH=. pytest -q tests/parsing/fortran/`
- Scope and project behavior:
  `PYTHONPATH=. pytest -q tests/parsing/fortran/test_scope_handling.py tests/parsing/fortran/test_project_scope_models.py`
- Preprocessing and execution-boundary behavior:
  `PYTHONPATH=. pytest -q tests/pipeline/preprocessing/test_parser_boundaries.py`
- Parser diagnostics:
  `PYTHONPATH=. pytest -q tests/parsing/fortran/test_error_handling.py`
- Fixture goldens:
  `PYTHONPATH=. pytest -q tests/parsing/fortran/test_fortran_fixture_suite.py`
- Parser error fixtures:
  `PYTHONPATH=. pytest -q tests/parsing/fortran/test_error_fixture_suite.py`

Regenerate one Fortran fixture:

```bash
python tests/parser/fortran/generate_fortran_parser_goldens.py tests/data/fortran/general/basic_subroutine.f90
```

Executable tutorial: `tests/parsing/fortran/test_developer_tutorial.py`.

### Semantics And `.pyi`

Manual calls:

<!-- X2PY_C_DOCS_START
```bash
python -m x2py tests/data/fortran/general/basic_subroutine.f90 &#45;&#45;semantics
python -m x2py tests/data/fortran/general/basic_subroutine.f90 &#45;&#45;pyi
python -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;semantics
python -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;pyi
```
X2PY_C_DOCS_END -->

Focused tests by concern:

- Fortran parser-to-IR conversion:
  `PYTHONPATH=. pytest -q tests/semantics/conversion/fortran/`
- Wrapper-plan support diagnostics:
  `PYTHONPATH=. pytest -q tests/wrapper_codegen/`
- `.pyi` printer:
  `PYTHONPATH=. pytest -q tests/wrapper_codegen/printers/`
- `.pyi` loader and edited stub behavior:
  `PYTHONPATH=. pytest -q tests/parsing/pyi/`
- Semantic and `.pyi` fixtures:
  `PYTHONPATH=. pytest -q tests/pipeline/pyi_builds/test_contract_fixtures.py`

<!-- X2PY_C_DOCS_START
- C parser-to-IR conversion:
  `PYTHONPATH=. pytest -q tests/semantics/conversion/c/`
X2PY_C_DOCS_END -->

Regenerate semantic and `.pyi` fixtures:

```bash
python tests/semantics/generate_semantic_fixtures.py
python tests/pyi/generate_pyi_fixtures.py
```

Executable examples: `tests/wrapper_codegen/printers/` and `tests/parsing/pyi/`.

### CLI

Manual calls:

<!-- X2PY_C_DOCS_START
```bash
python -m x2py tests/data/fortran/general/basic_subroutine.f90 &#45;&#45;parse
python -m x2py tests/data/fortran/general/basic_subroutine.f90 &#45;&#45;semantics
python -m x2py tests/data/fortran/general/basic_subroutine.f90 &#45;&#45;pyi
python -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;parse
```
X2PY_C_DOCS_END -->

Focused tests:

- Full CLI behavior:
  `PYTHONPATH=. pytest -q tests/cli/`
- Stage dispatch:
  `PYTHONPATH=. pytest -q tests/cli/ -k "parse or semantics or pyi or wrap"`
- Language and preprocessing selection:
  `PYTHONPATH=. pytest -q tests/cli/ -k "language or preprocessing"`

Executable reference: `tests/cli/`.
