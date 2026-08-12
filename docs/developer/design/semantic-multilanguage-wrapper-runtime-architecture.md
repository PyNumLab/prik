---
title: Semantic Multilanguage Wrapper and Interoperability Runtime
audience: maintainers
prerequisites: semantic IR reference, wrapper design notes
related: ../architecture.md, ../internal-architecture/wrapper-generation-pipeline.md
status: design
publication: draft
---

# Semantic Multilanguage Wrapper and Interoperability Runtime

<!-- PRIK_C_DOCS_START
> **Status:** This is a long-term architecture document, not a statement that
> every backend below exists. The source-driven Fortran-to-Python wrapper is
> implemented and documented in
> [the Fortran wrapper reference](../../user/reference/fortran-wrapper.md). C parsing, semantic IR,
> `.pyi`, and semantic inspection are implemented, but the runtime backend for
> user-supplied C inputs will be added later. Other language backends and the
> broader coercion runtime remain design goals.
PRIK_C_DOCS_END -->

## Vision

The goal of this project is to create a modern interoperability framework capable of wrapping and connecting libraries written in multiple native languages through a unified semantic API layer.

The system should:

* expose clean Python APIs
* support semantic interoperability between different native runtimes
* support automatic coercions and conversions
* support runtime constraints and validation contracts
* support zero-copy array interoperability when possible
* avoid compiler dependence whenever possible
* avoid forcing users to modify native code
* avoid the limitations of SWIG/f2py-style systems
* support wrapping libraries even when the source code is unavailable

<!-- PRIK_C_DOCS_START
* wrap native libraries from:
  * Fortran
  * C
  * C++
  * Rust
  * CUDA
  * and potentially more languages later
PRIK_C_DOCS_END -->

The project is not merely a wrapper generator.

It is a:

* semantic wrapper compiler
* interoperability runtime
* runtime coercion engine
* runtime validation engine
* runtime validation contract system
* language-independent semantic API system

---

## Core Philosophy

The most important architectural decision is:

> The semantic API layer is the source of truth.

NOT:

* parser ASTs
* compiler internals
* ABI details
* native language syntax

The system separates:

| Concern | Responsibility |
| --- | --- |
| Semantic API | `.pyi`-style interface layer |
| Runtime coercions | conversion registry and coercion graph |
| Runtime validation | constraint checks on adapted values |
| Validation contracts | reusable preconditions, postconditions, and invariants |
| Initializer contracts | import-time initialization of native state through extension hooks |
| Native ABI | backend adapters |
| Source parsing | optional helper |

This separation is the foundation of the whole architecture.

---

## Why Existing Systems Are Not Enough

### SWIG

SWIG is:

* parser-centric
* macro-heavy
* difficult to debug
* weak for scientific arrays
* poor for runtime semantics
* poor for modern interoperability

It also becomes difficult to maintain when:

* ownership becomes complex
* NumPy arrays are involved
* GPU arrays are involved
* runtime conversions are needed
* API remapping becomes advanced

### f2py

f2py is:

* Fortran-specific
* procedural
* compiler/build-centric
* not semantic-runtime oriented
* weak for object systems
* weak for heterogeneous runtimes

### pybind11

pybind11 is excellent for:

* clean bindings
* modern Python APIs

But:

* bindings are handwritten
* there is no semantic interoperability layer
* no runtime coercion model
* no language-independent abstraction

---

## High-Level Architecture

The architecture is composed of multiple layers.

<!-- PRIK_C_DOCS_START
```text
Native libraries/sources
        ↓
Optional parser frontends
        ↓
Canonical semantic interface layer (.pyi)
        ↓
Semantic IR
        ↓
Runtime coercion engine
        ↓
Runtime validation engine
        ↓
Runtime validation contracts
        ↓
Backend adapters
        ↓
Generated CPython extension
        ↓
Python API
```
PRIK_C_DOCS_END -->

The validation engine enforces concrete checks. Validation contracts describe when those checks run, what they guarantee, and how failures are reported.

---

## Canonical Semantic Interface Layer

The `.pyi`-style interface file is the central abstraction.

It defines:

* semantic APIs
* classes
* functions
* methods
* semantic types
* allowed coercions
* constraints
* validation contracts
* ownership semantics
* API remapping

This layer is:

* language-independent
* parser-independent
* editable
* human-readable
* stable

The native parser is NOT the source of truth.

The `.pyi` interface file is.

---

## Example Basic Wrapper

Suppose native Fortran code contains a procedural matrix API:

```fortran
module sparse_mod

  type :: sparse_matrix
  end type

contains

  subroutine create_sparse(A, nrows, ncols)
    type(sparse_matrix), intent(out) :: A
    integer, intent(in) :: nrows, ncols
  end subroutine

  subroutine sparse_multiply(A, x, y)
    type(sparse_matrix), intent(in) :: A
    real(8), intent(in) :: x(:)
    real(8), intent(out) :: y(:)
  end subroutine

end module
```

The semantic interface may expose a Pythonic object model:

```python
from prik.contracts import bind

@bind("sparse_matrix")
class SparseMatrix:

    @bind("create_sparse")
    def __init__(
        self,
        nrows: int[Positive],
        ncols: int[Positive],
    ) -> None: ...

    @bind("sparse_multiply")
    @contract(
        pre=lambda c: c.args.x.shape == (c.self.ncols,) and c.args.x.dtype == "float64",
        post=lambda c: c.result.shape == (c.self.nrows,) and c.result.dtype == "float64",
    )
    def multiply(
        self,
        x: Float64Vector[From(np.ndarray), CPUResident],
    ) -> Float64Vector: ...
```

This allows:

* semantic API redesign
* Pythonic APIs
* decoupling native APIs from exposed APIs
* explicit validation of user-facing expectations
* reusable runtime checks without changing native source code

---

## API Projection

The framework allows transforming procedural APIs into clean object-oriented APIs.

Native:

```fortran
call sparse_multiply(A, x, y)
```

Exposed Python API:

```python
y = A.multiply(x)
```

This is called:

> semantic API projection.

The projection records how Python-level `self`, arguments, and return values map to native parameters.

---

## Semantic Types

Semantic types represent:

> what an object means conceptually.

NOT:

* its memory layout
* its native language representation
* its ABI representation

Examples:

* `Float64Matrix`
* `SparseMatrix`
* `Tensor3D`
* `CSRMatrix`
* `ComplexVector`
* `DeviceBuffer`

Semantic types are language-independent.

---

## Coercions

Coercions define:

> how one type can be adapted into another.

Examples:

* `int -> float`
* `np.ndarray -> Float64Matrix`
* `TorchTensor -> Float64Matrix`
* `CuPyArray -> DeviceBuffer`

Coercions should be explicit in the semantic interface so that the runtime can reject surprising conversions and explain accepted ones.

---

## Declaring Coercions

The semantic interface can declare allowed coercions.

Example:

```python
def scale(alpha: float[From(int)], x: Float64Vector) -> Float64Vector: ...
```

Meaning:

```text
int -> float
```

is an allowed coercion for `alpha`.

---

## Matrix Example

```python
from prik.contracts import ORDER_F

def solve(
    A: Float64Matrix[
        From(np.ndarray),
        ORDER_F,
        Writable,
        "N", "N",
    ],
    b: Float64Vector[
        From(np.ndarray),
        "N",
    ],
) -> Float64Vector["N"]: ...
```

This means:

* target semantic type for `A`:
  * `Float64Matrix`
* allowed coercion for `A`:
  * `np.ndarray -> Float64Matrix`
* required constraints for `A`:
  * Fortran-contiguous (`ORDER_F`)
  * writable
  * square shape
* cross-argument contract:
  * `A.shape[0] == A.shape[1] == b.shape[0]`

---

## Constraints

Constraints define:

> requirements the final adapted representation must satisfy.

Constraints are NOT coercions.

Examples:

* `Positive`
* `Writable`
* `ORDER_F`
* `CPUResident`
* shape subscriptions such as `Float64["N", "N"]`
* `Aligned(64)`
* `Finite`
* `NonNull`

<!-- PRIK_C_DOCS_START
* `ORDER_C`
PRIK_C_DOCS_END -->

A constraint is usually local to one value: dtype, shape, device, alignment, mutability, ownership, or value range.

---

## Runtime Coercion Engine

The runtime coercion engine is responsible for converting accepted Python objects into semantic runtime objects.

Responsibilities:

* find an allowed conversion path from the observed input type to the target semantic type
* rank competing conversion paths by cost, safety, and zero-copy potential
* apply conversions in order
* preserve ownership and lifetime metadata
* emit a trace that can be shown in diagnostics

Example conversion trace:

<!-- PRIK_C_DOCS_START
```text
argument A:
  np.ndarray(shape=(10, 10), dtype=float64, order=C)
    -> copy_to_fortran_order
  Float64Matrix(shape=(10, 10), dtype=float64, order=F, owner=temporary)
```
PRIK_C_DOCS_END -->

---

## Runtime Validation Engine

The runtime validation engine checks that semantic runtime objects satisfy the declared constraints and contract predicates.

Responsibilities:

* validate per-argument constraints after coercion
* validate cross-argument preconditions before native calls
* validate return-value postconditions after native calls
* validate object invariants after mutating methods
* produce structured errors with the failing parameter, expected condition, observed value, and coercion trace

Example validation error:

<!-- PRIK_C_DOCS_START
```text
ValidationError in solve(A, b)
  parameter: A
  failed: ORDER_F
  observed: order='C', shape=(10, 10), dtype=float64
  hint: declare From(np.ndarray, copy=True) or pass np.asfortranarray(A)
```
PRIK_C_DOCS_END -->

The validation engine is runtime-oriented. It does not replace static typing; it protects the native ABI boundary and provides clear diagnostics for dynamic Python inputs.

---

## Runtime Validation Contracts

Runtime validation contracts are reusable groups of validation rules that describe the semantic obligations of an API.

Contracts may include:

* preconditions: requirements before a native call
* postconditions: guarantees after a native call
* invariants: requirements that must remain true for an object over its lifetime
* aliasing rules: whether inputs may overlap in memory
* mutation rules: which arguments may be modified
* ownership rules: whether returned objects borrow, own, or view native memory

Example:

```python
@contract(
    pre=[
        lambda ctx: ctx.args.A.shape == (ctx.args.N, ctx.args.N),
        lambda ctx: ctx.args.b.shape == (ctx.args.N,),
        lambda ctx: ctx.args.A.device == ctx.args.b.device == 'cpu',
    ],
    post=[
        lambda ctx: ctx.result.shape == (ctx.args.N,),
        lambda ctx: ctx.result.dtype == "float64",
    ],
    invariants=[
        lambda ctx: not ctx.result.aliases(ctx.args.A)",
    ],
)
def solve(
    A: Float64Matrix[From(np.ndarray), CPUResident],
    b: Float64Vector[From(np.ndarray), CPUResident],
) -> Float64Vector: ...
```

Contracts are higher-level than constraints. A constraint can say `b` has shape `N`; a contract can say `A` and `b` agree on the same `N` and that the returned vector does not alias mutable input storage.

---

## Runtime Initializer Contracts

Runtime initializer contracts describe how mutable native state is initialized when a generated extension module is imported.

They are separate from constants. A `Final[...]` declaration records an immutable API value, while an initializer contract writes a value into mutable native storage through the completed setter policy.

The implemented minimal slice is literal defaults on mutable module variables:

```python
from prik.contracts import Int32

counter: Int32 = 41
```

That form can be lowered to a typed value and assigned through the generated extension setter after the native module is initialized.

The longer-term contract is more general. An initializer expression may be executable Python:

```python
from prik.contracts import Float64, Int32

from .init_hooks import initial_counter, runtime_scale

counter: Int32 = initial_counter(seed=41)
scale: Float64 = 1.0 + runtime_scale()
```

Executable initializer contracts should run at the generated extension level, not by translating Python expressions into equivalent native bridge code. The extension can import Python modules, call Python hook functions, call generated Python wrappers if needed, convert the final result to the declared semantic type, and assign it through the generated setter for the native variable.

Initializer contracts complement validation contracts:

* initializers run during extension import
* preconditions run before a wrapped function call
* postconditions run after a wrapped function call
* invariants may be checked after initialization and after later mutations

Import-time initializer pipeline:

```text
Create extension module
    ↓
Install generated functions and properties
    ↓
Import requested Python hook modules
    ↓
Evaluate initializer expressions
    ↓
Convert initializer results to semantic types
    ↓
Assign through generated native setters
    ↓
Expose initialized module
```

Because executable initializers are user Python, their side effects, environment dependencies, import cycles, and exceptions belong to the user contract. If an initializer raises, extension import should fail with a diagnostic attached to the semantic declaration being initialized.

---

## Important Concept Separation

The architecture separates:

| Concept | Meaning |
| --- | --- |
| Semantic type | what the object is |
| Coercion | how another type becomes it |
| Constraint | local requirements on an adapted value |
| Validation contract | API-level preconditions, postconditions, invariants, and aliasing rules |
| Initializer contract | import-time native-state initialization through generated setters |
| Backend adapter | semantic object → ABI representation |

This separation is fundamental.

---

## Runtime Coercion Registry

Allowed coercions declared in `.pyi` are implemented through a runtime coercion registry in the equivalent `.py` file.

Example:

```python
@coercion(np.ndarray, Float64Matrix, implicit=True, cost=1, zero_copy="if_compatible")
def ndarray_to_matrix(A: np.ndarray) -> Float64MatrixObject:
    return Float64MatrixObject.from_numpy(A)
```

This registers:

```text
np.ndarray -> Float64Matrix
```

inside the runtime registry.

---

## Runtime Contract Registry

Validation contracts can also be registered and reused by name.

Example:

```python
@validation_contract
def square_linear_system(ctx):
    A = ctx.arg("A")
    b = ctx.arg("b")
    result = ctx.result

    ctx.require(A.ndim == 2, "A must be a matrix")
    ctx.require(A.shape[0] == A.shape[1], "A must be square")
    ctx.require(b.shape == (A.shape[0],), "b must match A rows")
    ctx.ensure(result.shape == b.shape, "solution shape must match b")
```

The interface can then reference the contract:

```python
@contract(square_linear_system)
def solve(A: Float64Matrix, b: Float64Vector) -> Float64Vector: ...
```

<!-- PRIK_C_DOCS_START
This allows common validation logic to be shared across Fortran, C, C++, Rust, and CUDA backends.
PRIK_C_DOCS_END -->

---

## Runtime Dispatch Flow

Suppose:

```python
x = solve(np.ones((10, 10)), np.ones(10))
```

Runtime pipeline:

```text
Input objects
    ↓
Find semantic target types
    ↓
Find coercion paths
    ↓
Apply coercions
    ↓
Validate argument constraints
    ↓
Validate contract preconditions
    ↓
Backend adapters
    ↓
Native ABI call
    ↓
Validate contract postconditions and invariants
    ↓
Return Python object
```

---

## Coercion Graphs

The runtime should support composed coercions.

Example:

```text
TorchTensor
    ↓
np.ndarray
    ↓
Float64Matrix
```

The runtime can automatically infer:

```text
TorchTensor -> Float64Matrix
```

through graph traversal when the path is declared safe and allowed for the target API.

---

## Coercion Metadata

Coercions may contain metadata.

Example:

```python
@coercion(
    np.ndarray,
    Float64Matrix,
    implicit=True,
    cost=1,
    zero_copy=True,
    preserves_aliasing=True,
)
def ndarray_to_matrix(A):
    ...
```

Possible metadata:

* implicit/explicit
* safe/unsafe
* cost
* zero-copy
* ownership
* device awareness
* aliasing behavior
* mutability preservation

---

## Semantic Runtime Objects

The runtime should internally use semantic runtime objects.

Example:

```python
class Float64MatrixObject:
    ptr: int
    shape: tuple[int, int]
    strides: tuple[int, int]
    owner: object | None
    device: str
    writable: bool
    aliases: set[int]
```

These objects are:

* language-independent
* runtime-oriented
* semantic representations

NOT:

* NumPy arrays
* Fortran descriptors
* Eigen matrices

---

## Backend Adapters

Backend adapters convert:

```text
Semantic runtime object
    ↓
Native ABI representation
```

Examples:

* Fortran descriptors
* Eigen maps
* CUDA tensors

<!-- PRIK_C_DOCS_START
* C structs
PRIK_C_DOCS_END -->

Adapters should receive values only after coercion and validation have completed. This keeps ABI code focused on call mechanics instead of user-input cleanup.

---

## Wrapping Libraries Without Source Code

The framework should support wrapping:

* `.so`
* `.dll`
* static libraries

without source code.

Users provide:

* semantic `.pyi`
* coercions if needed
* validation contracts if needed
* optional metadata

No source parsing required.

---

## Optional Parser Frontends

Parsers are helpers.

NOT the foundation.

Possible parsers:

* Fortran parser
* Rust parser

<!-- PRIK_C_DOCS_START
* C parser
* C++ parser
PRIK_C_DOCS_END -->

Their role:

* generate starter `.pyi`
* synchronize declarations
* help users bootstrap wrappers

The semantic interface remains canonical.

---

## Mixed-Language Libraries

The framework should support libraries implemented in multiple languages simultaneously.

Example:

* Fortran numerical kernels
* Rust runtime safety
* CUDA kernels

<!-- PRIK_C_DOCS_START
* C runtime layer
* C++ object systems
PRIK_C_DOCS_END -->

All unified through:

* semantic types
* coercions
* constraints
* validation contracts
* backend adapters

---

## Example Mixed-Language Workflow

Suppose:

### Fortran solver

```fortran
subroutine solve_system(A, b, x)
```

<!-- PRIK_C_DOCS_START
### C++ mesh
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```cpp
class Mesh {
public:
    void refine();
};
```
PRIK_C_DOCS_END -->

### Rust optimizer

<!-- PRIK_C_DOCS_START
```rust
extern "C" fn optimize(ptr: *mut f64, len: usize) -> i32;
```
PRIK_C_DOCS_END -->

The semantic API may expose:

```python
from prik.contracts import ORDER_F

class Solver:
    @contract(pre=square_linear_system)
    def solve(
        self,
        A: Float64Matrix[From(np.ndarray), ORDER_F],
        b: Float64Vector[From(np.ndarray)],
    ) -> Float64Vector: ...

class Mesh:
    @contract(post=[lambda ctx:ctx.self.is_valid()])
    def refine(self) -> None: ...

def optimize(
    x: Float64Vector[From(np.ndarray), Writable, CPUResident],
) -> OptimizationResult: ...
```

The user does not care about implementation language. The semantic layer records type meaning, conversion policy, validation policy, and backend dispatch.

---

## Ownership and Lifetime Management

The runtime must manage:

* borrowed references
* owned references
* zero-copy views
* temporary coercions
* destruction policies
* aliasing constraints
* mutation contracts

This is one of the hardest parts of the system.

---

## Zero-Copy Interoperability

The runtime should avoid unnecessary copies whenever possible.

Examples:

| Conversion | Strategy |
| --- | --- |
| NumPy F-order → Fortran | zero-copy |
| NumPy → Eigen::Map | zero-copy when dtype, alignment, and strides match |
| Torch CUDA → CPU array | copy, unless API accepts GPU memory |
| CuPy array → CUDA kernel | zero-copy when stream and device contracts match |

<!-- PRIK_C_DOCS_START
| NumPy C-order → Fortran descriptor requiring F-order | copy or reject, depending on contract |
PRIK_C_DOCS_END -->

The runtime should optimize coercion paths automatically while still honoring explicit API contracts.

---

## Scientific Computing Focus

The architecture is especially useful for:

* HPC
* FEM
* CFD
* climate models
* tensor runtimes
* numerical libraries
* GPU computing
* scientific Python ecosystems

because these domains already contain:

* mixed-language systems
* difficult interoperability
* array-heavy APIs
* strict shape, device, ownership, and aliasing requirements

<!-- PRIK_C_DOCS_START
* legacy Fortran/C++ code
PRIK_C_DOCS_END -->

---

<!-- PRIK_C_DOCS_START
## CPython Extension Backend
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The project should generate custom CPython extensions directly.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Reasons:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
* full control over runtime
* full control over arrays
* full control over coercions
* full control over validation contracts
* better diagnostics
* better ownership handling
* better performance
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The project should NOT fundamentally depend on:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
* SWIG
* ctypes
* pybind11
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
although optional backends may exist later.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
&#45;&#45;-
PRIK_C_DOCS_END -->

## Diagnostics

Diagnostics are extremely important.

The framework should provide:

* clear coercion errors
* constraint validation errors
* contract validation errors
* coercion trace visualization
* ownership diagnostics
* backend dispatch diagnostics

Example diagnostic:

```text
ContractError in Solver.solve(A, b)
  contract: square_linear_system
  failed: b.shape == (A.shape[0],)
  observed:
    A.shape = (10, 10)
    b.shape = (8,)
  coercion trace:
    A: np.ndarray -> Float64Matrix [zero-copy]
    b: np.ndarray -> Float64Vector [zero-copy]
```

This should be much better than typical SWIG/f2py errors.

---

## Plugin Ecosystem

Third-party ecosystems should be able to register:

* semantic types
* coercions
* constraints
* validation contracts
* backend adapters

This allows:

* NumPy support
* Torch support
* JAX support
* CUDA support
* sparse matrix ecosystems
* domain-specific runtimes

---

## Roadmap

### Phase 1: Semantic API and IR

* Define the `.pyi`-style semantic grammar.
* Represent semantic types, argument mappings, ownership rules, constraints, and validation contracts in the IR.
* Generate a minimal Python-facing wrapper skeleton from the IR.

### Phase 2: Runtime Coercion Engine

* Implement the coercion registry.
* Support direct coercions, composed coercion paths, cost ranking, and zero-copy metadata.
* Add structured coercion traces for diagnostics.

### Phase 3: Runtime Validation Engine

* Implement local constraint validation for shape, dtype, contiguity, device, mutability, ownership, and alignment.
* Attach validation failures to source parameters and semantic declarations.
* Run validation after coercion and before backend adaptation.

### Phase 4: Runtime Contracts

* Add reusable contract declarations for preconditions, postconditions, invariants, aliasing, mutation, and ownership.
* Add initializer contracts for import-time native-state setup through generated extension setters.
* Support named contract registration and inline contracts in the semantic interface.
* Validate cross-argument relationships such as matching dimensions, shared devices, non-overlapping buffers, and stable object invariants.
* Include contract traces in diagnostics.

### Phase 5: Backend Adapters

* Add CUDA/device-memory adapters once device contracts are available.

<!-- PRIK_C_DOCS_START
* Implement initial Fortran and C adapters.
* Add C++ and Rust adapters after the semantic runtime is stable.
PRIK_C_DOCS_END -->

### Phase 6: Parser Frontends and Ecosystem Plugins

* Add optional parser frontends that generate starter semantic interfaces.
* Add plugin APIs for NumPy, Torch, JAX, CUDA, and sparse matrix ecosystems.
* Keep parser output editable and subordinate to the canonical semantic interface.

---

## Long-Term Goal

The final system becomes:

* a semantic wrapper compiler
* a runtime interoperability framework
* a mixed-language scientific runtime layer
* a semantic coercion engine
* a runtime validation engine
* a runtime validation contract system
* an extension-level initializer contract system
* a modern replacement for old wrapper systems

The key innovation is:

```text
Semantic interoperability
instead of
parser-centric wrapper generation
```

---

## Final Summary

The architecture is built around:

```text
Semantic API
        ↓
Contract layer
        ├─ Initializer contracts at extension import
        └─ Validation contracts around wrapped calls
        ↓
Coercions
        ↓
Constraints
        ↓
Semantic runtime objects
        ↓
Backend adapters
        ↓
Native execution
```

The project focuses on:

* clean semantic APIs
* runtime interoperability
* mixed-language support
* runtime coercion
* runtime validation
* runtime validation contracts
* extension-level initializer contracts
* scientific computing
* extensibility
* high performance
* language independence

while avoiding:

* parser dependence
* compiler dependence
* rigid ABI-centric designs
* old wrapper system limitations.
