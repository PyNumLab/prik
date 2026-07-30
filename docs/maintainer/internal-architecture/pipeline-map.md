---
title: Pipeline Map
audience: maintainers
prerequisites: source map, overall architecture
related: ../../developer/source-map.md, wrapper-generation-pipeline.md, runtime-layer.md
status: maintained
publication: draft
---

# Pipeline Map

This page is the source-code route through the current wrapper and inspection
pipelines. It complements the user-facing wrapper mechanism in
`docs/user/reference/fortran-wrapper.md` with the implementation files a maintainer should
open at each stage.

## Source-Driven Fortran Wrapper Pipeline

<!-- X2PY_C_DOCS_START
```text
CLI request
  -> wrapper build orchestration
  -> compiler preprocessing
  -> Fortran parser project model
  -> Fortran target kind/storage probes
  -> semantic IR
  -> semantic policy completion
       -> ownership/transfer/destruction policy completion
  -> typed wrapper plan
  -> generated Fortran bind(C) bridge
  -> generated C/CPython binding
  -> native compile, binding support install, and link
  -> importable Python extension
  -> wrapper runtime tests
```
X2PY_C_DOCS_END -->

| Stage | Main source | Input | Output | Primary evidence |
| --- | --- | --- | --- | --- |
| CLI request | `x2py/cli.py` | source paths and stage flags | selected stage or wrapper build options | `tests/fortran/command_line_interface/pipeline/` |
| Build orchestration | `x2py/pipeline/build.py` | ordered Fortran sources or `.pyi` contracts plus explicit native artifacts | `WrapperBuildResult`, `NativeBuildPlan`, and generated artifact plan | wrapper build-mode tests |
| Preprocessing | `x2py/pipeline/preprocessing.py` | source path, compiler config | preprocessed source and dependency facts | preprocessing tests |
| Parser project model | `x2py/parsers/fortran/parser.py` | preprocessed Fortran source | parser project with modules, procedures, types, visibility | Fortran parser fixture tests |
| Target probes | `x2py/probes/fortran_types.py` | semantic type requirements and compiler flags | resolved kind/storage facts | Fortran type probe tests |
| Semantic IR | `x2py/semantics/fortran2ir.py` | parser project and target facts | `SemanticModule` objects | semantic Fortran tests |
| Semantic policy completion | `x2py/semantics/policy_completion.py`, `x2py/semantics/ownership.py` | full semantic modules with signatures and `.pyi` overrides | semantic modules annotated with every ownership, transfer, destruction, mutability, storage, accessor, and projection decision needed by wrapper generation | ownership-policy tests |
| Wrapper planning | `x2py/wrapper_codegen/planner.py`, `x2py/wrapper_codegen/plan.py` | policy-completed semantic modules | typed wrapper plans consuming completed decisions without a separate support-analysis traversal | `tests/fortran/infrastructure/wrapper_codegen/`, wrapper tests |
| Direct bridge and binding lowering | `x2py/wrapper_codegen/fortran/bridge.py`, `x2py/wrapper_codegen/c/binding.py`, `x2py/wrapper_codegen/generator.py` | validated typed wrapper plans | Fortran, C, and header syntax nodes | `tests/fortran/infrastructure/wrapper_codegen/`, wrapper tests |
| Wrapper and semantic-contract printing | `x2py/wrapper_codegen/printers/` | wrapper syntax nodes or semantic IR | wrapper source files or semantic `.pyi` text | printer, generated-contract, and wrapper artifact tests |
| Compile and link | `x2py/compiling/`, `x2py/pipeline/build.py` | explicit native objects, then generated bridge objects, then runtime/binding objects and ordered link inputs | shared library | wrapper runtime and build-mode tests |

<!-- X2PY_C_DOCS_START
X2PY_C_DOCS_END -->

## Concept Ownership Rules

The pipeline keeps separate concepts for contract facts, policy decisions,
generated implementation, and emitted source. Similar names across layers do
not mean those classes should be merged.

The Python package layout follows those ownership boundaries:

| Package | Owns | Must not become |
| --- | --- | --- |
| `x2py/contracts/` | The public semantic `.pyi` vocabulary | A home for semantic conversion or runtime type mapping |
| `x2py/types/` | Mappings from resolved semantic types to Python ecosystem types | A second semantic IR model |
| `x2py/probes/` | Compiler-derived target facts and reports built from those facts | Semantic policy or build orchestration |
| `x2py/pipeline/` | Source preprocessing, semantic `.pyi` loading, and end-to-end wrapper build orchestration | Parser models, semantic decisions, or compiler implementation details |
| `x2py/runtime/` | Python objects used by generated extensions at execution time | Build-time semantic or codegen policy |
| `x2py/utilities/` | Small domain-neutral mechanisms such as class visitor dispatch | A miscellaneous home for semantic or pipeline concepts |

Semantic metadata and ownership policy remain in `x2py/semantics/` even when
codegen consumes them. Downstream use does not turn semantic authority into
cross-cutting infrastructure.

| Concept family | Owner | What belongs there | What must stay out |
| --- | --- | --- | --- |
| Parser facts | parser packages | Source syntax, native declaration structure, source locations, and parser diagnostics | Wrapper policy, Python API projection, generated names, and compile/link decisions |
| Semantic policy completion and ownership | `x2py/semantics/policy_completion.py` and `x2py/semantics/ownership.py` | Completed policy choices for ownership, lifetime, output projection, replacement, and ABI safety | Raw parser syntax, backend-specific statement trees, and hidden lowering-time policy decisions |
| Typed wrapper plan | `x2py/wrapper_codegen/plan.py` and `x2py/wrapper_codegen/planner.py` | A validated, backend-neutral implementation plan projected from completed semantic decisions | Source-contract authority, policy inference, and target-language statement details |
| Printers and compilation | `x2py/wrapper_codegen/printers/`, `x2py/compiling/`, and wrapper orchestration | Text emission, generated artifact layout, compiler commands, native objects, libraries, include directories, and link inputs | Semantic support decisions and plan rewriting policy |

<!-- X2PY_C_DOCS_START
| Semantic IR | `x2py/semantics/models.py`, `x2py/semantics/metadata.py`, and source-to-IR converters | Language-neutral contract facts: public names, native identities, source origins, visibility, type/storage/access facts, module/class/function/variable structure, and metadata that must survive parser, policy, printer, and lowering boundaries | Generated bodies, temporaries, target-language scopes, include/import mechanics, CPython calls, and printer-only syntax |
| Backend syntax nodes | `x2py/wrapper_codegen/nodes.py`, `x2py/wrapper_codegen/fortran/bridge.py`, and `x2py/wrapper_codegen/c/binding.py` | Fortran bridge nodes, C/CPython binding nodes, target ABI/API calls, and backend-specific adapter structure | Language-neutral semantic meaning and policy decisions |
| Naming policy | `x2py/naming/` | Shared public-name and generated-symbol decisions for Python, C, and Fortran targets | Semantic IR ownership or codegen tree ownership |
X2PY_C_DOCS_END -->

Use these rules when adding a new notion:

- Put it in semantic IR when the fact changes the user-visible or native
  contract, must be preserved in `.pyi`, is needed for source-free wrapper
  replay, or is required before policy completion can decide support.
- Put it in semantic policy completion or ownership policy when it is a safety decision rather
  than a source fact: for example borrowed versus copied data, visible versus
  hidden native outputs, replacement rules, destructor ownership, or unsupported
  ABI combinations. If the decision depends on full signature context, complete
  it in `policy_completion.py` before wrapper planning.
- Put it in compiling or wrapping when it describes build inputs or build
  execution: sources, objects, libraries, library directories, include
  directories, compiler flags, link items, binding support files, and generated
  artifact paths.

<!-- X2PY_C_DOCS_START
- Put it in wrapper generation when it exists because emitted wrapper code needs it:
  generated bodies, temporaries, low-level storage variables, scopes, imports,
  includes, bridge calls, CPython API calls, cleanup paths, and target-language
  expressions.
- Put it in naming when the same source symbol needs stable Python, C, or
  Fortran spellings, reserved-word handling, or collision-free generated names.
  The naming layer is a shared policy service, not a semantic model and not a
  generated source-syntax node.
X2PY_C_DOCS_END -->

Merge or move concepts only when their invariants match:

- Merge a shared object only when it has the same meaning and lifetime in every
  layer and carries no generated implementation state. Small immutable value
  objects such as identity, origin, scalar-kind descriptors, or naming-policy
  results are candidates.
- Move a codegen concept into semantics only when it can be represented without
  a generated body, temporary, scope, include, or target-language expression and
  the fact is needed for `.pyi`, policy completion, or source-free replay.
- Move a semantic concept into a wrapper plan only when it does not change the public
  contract, native contract, completed policy, or `.pyi` representation and exists only
  to print or compile wrapper code.

<!-- X2PY_C_DOCS_START
- Keep concepts split when they share a word but not an invariant. A semantic
  function is a callable contract; a codegen function is an emitted body. A
  semantic variable is a public/native value contract; a codegen variable is a
  storage location in generated code. A semantic datatype is an API/ABI fact; a
  codegen datatype can be a concrete Fortran, C, CPython, NumPy, or bridge
  representation.
X2PY_C_DOCS_END -->

Examples:

- `@bind` and a native procedure name belong to semantic identity. The bridge
  symbol used to call it belongs to codegen naming and lowering.
- Python keyword avoidance for a public name, such as a native `def` routine,
  belongs to naming policy. The chosen public spelling is stored where the
  contract needs it, while target-specific helper symbols stay generated.
- Wrapper syntax nodes, body statements, temporaries, includes, and backend
  datatypes stay out of `x2py/semantics/models.py`.

<!-- X2PY_C_DOCS_START
- `@raises`, `@hold_gil`, output projection, and ownership metadata belong to
  semantic policy. The generated CPython error checks, GIL calls, and
  cleanup statements belong to codegen.
X2PY_C_DOCS_END -->

## Stage Maintenance Map

| Stage family | First files to read | Source navigation owner |
| --- | --- | --- |
| CLI and output routing | `x2py/cli.py`, parser CLI helpers | `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md` |
| Source loading and preprocessing | `x2py/pipeline/preprocessing.py` | `docs/developer/source-map.md`, parser references |
| Editable semantic contracts | `x2py/parsers/pyi/parser.py`, `x2py/pipeline/pyi.py`, `x2py/semantics/pyi2ir.py`, `x2py/wrapper_codegen/printers/pyi_printer.py` | `docs/user/reference/semantic-pyi-format.md` |
| Semantic and wrapper-planning errors | `x2py/semantics/fortran2ir.py`, `x2py/semantics/policy_completion.py`, `x2py/semantics/wrapper_policy.py`, `x2py/wrapper_codegen/planner.py` | `docs/user/guide/error-handling.md` |
| Wrapper policy and lowering | `x2py/semantics/policy_completion.py`, `x2py/semantics/ownership.py`, `x2py/wrapper_codegen/planner.py`, `x2py/wrapper_codegen/generator.py` | `docs/user/reference/fortran-wrapper.md`, ownership docs |
| Native build | `x2py/pipeline/build.py`, `x2py/compiling/compilers.py`, `x2py/compiling/native_support.py` | compiling package README and build-system docs |

<!-- X2PY_C_DOCS_START
| Parser facts | `x2py/parsers/c/parser.py`, `x2py/parsers/fortran/parser.py` | parser package README files and parser references |
| Semantic conversion | `x2py/semantics/fortran2ir.py`, `x2py/semantics/c2ir.py`, `x2py/semantics/pyi2ir.py`, `x2py/semantics/models.py` | `docs/user/reference/semantic-ir.md` |
| Bridge and binding generation | `x2py/wrapper_codegen/fortran/bridge.py`, `x2py/wrapper_codegen/c/binding.py` | wrapper generation docs |
X2PY_C_DOCS_END -->

## Semantic `.pyi` Wrapper Pipeline

Semantic `.pyi` builds reuse the wrapper backend but start from edited
contracts and explicit native artifacts instead of reparsing native source for
the Python API.

```text
.pyi contract
  -> x2py/parsers/pyi/parser.py
  -> x2py/pipeline/pyi.py
  -> x2py/semantics/pyi2ir.py
  -> x2py/semantics/native_contract.py
  -> x2py/semantics/policy_completion.py
  -> x2py/wrapper_codegen/planner.py
  -> x2py/wrapper_codegen/generator.py
  -> compile and link pipeline
```

The `.pyi` path must preserve native ABI facts in the semantic contract. Missing
native build inputs or contradictory contract facts fail before bridge emission
or native compilation. Ownership, transfer, and destruction policy is completed
from the full `.pyi` signature before planning; the wrapper planner and backend
generators consume that completed policy and must not invent a different one.

## Shared Semantic Policy Boundary

<!-- X2PY_C_DOCS_START
C parser facts, Fortran parser facts, and semantic `.pyi` contracts all converge
on `SemanticModule` objects before ownership policy is decided. Semantic policy
completion fills in ownership, transfer, destruction, mutability/writeback,
nullability, storage mode (`stack`, `heap`, or `alias`), and codegen-action
decisions from the full semantic signature. Field and module-variable accessors
also receive separate completed getter, native assignment, and Python setter
exposure decisions; codegen does not derive accessor behavior from datatype or
storage representation:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```text
C parser -> x2py/semantics/c2ir.py
Fortran parser -> x2py/semantics/fortran2ir.py
.pyi parser -> x2py/parsers/pyi/parser.py -> x2py/pipeline/pyi.py -> x2py/semantics/pyi2ir.py
  -> SemanticModule objects
  -> x2py/semantics/policy_completion.py
  -> wrapper planning and lowering
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
`pyi_parser.py` is intentionally small: it reads `.pyi` text or files and
returns Python AST. Semantic interpretation belongs to `pyi2ir.py`, matching
the source-parser-to-IR split used by C and Fortran. Wrapper
planning consume completed policy decisions. They must not
reconstruct policy from a raw datatype such as `Float64[:]`; that datatype is
only meaningful after the surrounding argument, result, field, or module-variable
context is known. The C source path currently uses this shared boundary for
semantic reports; the implemented source-free wrapper backend is
Fortran-focused.
X2PY_C_DOCS_END -->

The completed decision is also the only semantic input to bridge and binding
behavior selection. Each backend owns an explicit dispatch table keyed by the
completed object kind and codegen action. A selected leaf method may construct
backend-local helper variables, but it must not choose ownership, writeback,
nullability, release responsibility, or `stack`/`heap`/`alias` placement for the
contract value. Missing dispatch combinations are errors; there is no datatype-
based policy fallback in bridge or binding generation.

CLI source inspection uses a compact language dispatch table for the source
portion of this route:

```text
pipeline = SOURCE_SEMANTIC_PIPELINES[language]
parsed = pipeline.parser(...)
semantic_modules = pipeline.converter_to_ir(parsed, ...)
semantic_modules -> semantic policy completion -> wrapper planning or lowering
```

Per-language parser/converter entries may still perform target-specific
preprocessing or ABI/kind probes, but ownership, transfer, destruction,
mutability, nullability, projection, and lifetime decisions must stay out of
those entries and flow through semantic policy completion after IR exists.

## Inspection-Only Pipeline

Inspection stages stop before wrapper code generation:

```text
native source
  -> parser facts
  -> semantic IR
  -> semantic .pyi
```

<!-- X2PY_C_DOCS_START
C source currently follows this inspection pipeline. Runtime wrapping of
user-supplied C inputs is future backend work and must not be presented as
implemented support.
X2PY_C_DOCS_END -->

## Where Failures Should Happen

| Failure type | Preferred owner |
| --- | --- |
| Source cannot be preprocessed | `x2py/pipeline/preprocessing.py` |
| Source syntax cannot be represented by x2py's parser model | parser package |
| Source facts cannot form a semantic contract | semantic conversion |
| Ownership, lifetime, ABI, projection, or wrapper support decision is unsafe | `x2py/semantics/ownership.py` or policy completion |
| A completed policy is internally inconsistent while being projected | wrapper planner at the owner being projected |
| Native-language validity does not affect x2py's contract | Fortran or C compiler |
| Generated code cannot represent a supported plan | bridge or binding generator with focused tests |
| Compiler/linker invocation is wrong | `x2py/compiling/` or `x2py/pipeline/build.py` |
| Python binding behavior is wrong | generated binding, native support, or ownership policy |
