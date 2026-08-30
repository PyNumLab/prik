---
title: C Binding Lowering
audience: developers, maintainers, contributors
prerequisites: Code Generation Stage guide, completed wrapper plan
related: ../../architecture.md, ../codegen.md, ../planning.md, ../printers.md, fortran-bridge.md
status: maintained
publication: reviewed
---

# C Binding Lowering

## Role And Boundary

[`prik/codegen/c/binding.py`](../../../../prik/codegen/c/binding.py) lowers the
binding and native-entrypoint views of a completed `ModulePlan` into a
`CModule` and `CHeader`. The result is CPython and NumPy C syntax nodes, not
source text and not a compiled extension. `CSourcePrinter` serializes the
nodes later.

The binding view owns Python extraction, validation, local storage, returned or
output C storage, Python result construction, errors, lifecycle actions,
extension initialization, and generated Python surfaces. The entrypoint view
owns the C ABI prototype and call. The generator may select local names and
the necessary C syntax, but never reads adapter-local conversion or original
Fortran invocation facts and never chooses ownership, optionality, storage, or
conversion policy. A completed C-source entrypoint supplies the native ABI
identity and declaration facts the binding emits before calling the user symbol
directly. Source-free contracts use the completed canonical spelling. The
binding does not infer a nearby C type from a NumPy dtype or emit a C adapter.

Ordinary functions use their function-owned entrypoint. Every other externally
linked generated call is looked up in the generated support procedure registry.
That includes constructors, field/member accessors, derived-origin and holder
operations, descriptor helpers, and callback trampolines. The C lowerer may
create static Python helpers, but it does not invent an external symbol or C
prototype when a generated support procedure entrypoint is missing. A
binding-implemented callback trampoline uses the same record for its function
definition that the Fortran side uses for its interface.

Binding-local derived capsule destructors, holder presence methods, and private
field methods follow the explicit module binding-support inventories. The
lowerer may join their planned owner paths to namespace-owned derived-type
records for emitted names and fields. It does not reconstruct those inventories
from results, arguments, constructors, release actions, or holder storage. Any
native call made by a local helper still obtains its existence, symbol, and ABI
from the generated support procedure registry.

## Input And Output

```text
ModulePlan.binding + ModulePlan.entrypoint
  + namespaces + function binding/entrypoint views
  -> CBindingGenerator.require_supported()
  -> CBindingGenerator.visit()
  -> CModule + CHeader
  -> CSourcePrinter
  -> C binding source + header text
```

`require_supported()` checks that the already selected primitive spellings are
available. It is capability preflight, not a second policy pass.

`BindingModulePlan` also supplies the public package root used for Python
function metadata. The binding combines that completed root with each planned
namespace path; it does not infer notebook execution or reuse the private
extension-loading name as presentation. An empty public root means the caller
is publishing directly into an interactive namespace. Generated filenames,
the `PyInit_*` symbol, and native helper symbols continue to use the plan's
internal owner path.

Numeric scalar boundaries retain their exact NumPy contract without using the
generic dtype-conversion path on a successful call. The native support helper
checks the planned NumPy scalar class, reads its typed payload directly, and
allocates the matching typed NumPy scalar for a result. Type mismatches still
follow the generated diagnostic path; this fast path changes neither accepted
inputs nor returned result types.

## Lowering Algorithm

`_visit_ModulePlan()` returns the paired C module and header. `binding_module()`
collects namespace functions, determines whether the plan requires runtime
helpers, and assembles declarations and functions in emitted dependency order:
shared helpers, class and descriptor support, wrappers, overload dispatchers,
then module initialization. `binding_header()` lowers prototypes from the
shared entrypoint records.

`_visit_FunctionPlan()` works in three ordered parts:

1. It creates one local-name context and puts declarations before executable
   statements.
2. It applies the plan's `argument_conversion_order`; each transfer dispatches
   on its completed optional, callback, descriptor, or derived facet.
3. It invokes the planned entrypoint, receives its direct or output-parameter
   C storage, and applies selected result construction and lifecycle work.

`PythonSurfaceEmitter` is used only when the plan contains generated classes,
holders, or module proxies. `CBindingNames` keeps its private C symbols aligned
with the binding helpers. Public names still come from the plan.

## Run A Minimal Manual Plan

This is the smallest complete plan: a public Python `ping()` that calls the
standalone native `PING` subroutine. Its empty transfer, result, slot, and
lifecycle tuples are intentional—there are no datatype or ownership decisions
for code generation to infer.

In a normal build, `WrapperPlanner` constructs the plan after policy completion
and `WrapperGenerator` freezes and validates it before lowering. Construct a
plan directly only to study an isolated backend mechanism like this one.

### Plan Shape

This abbreviated, non-runnable sketch shows the records in construction order.
Expand the full source to run the complete example.

```python
binding = BindingFunctionPlan(...)
entrypoint = NativeEntrypointFunctionPlan(...)
bridge = BridgeFunctionPlan(...)
function = FunctionPlan(
    ..., binding=binding, entrypoint=entrypoint, bridge=bridge
)
namespace = NamespacePlan(..., functions=(function,))
plan = ModulePlan(
    binding=BindingModulePlan(..., public_root="demo"),
    entrypoint=NativeEntrypointModulePlan(...),
    bridge=BridgeModulePlan(...),
    namespaces=(namespace,),
)

generator = CBindingGenerator()
c_module, _header = generator.visit(plan)
print(CSourcePrinter().doprint(...))
```

<details markdown="1">
<summary>Full runnable source</summary>

<!-- prik-doc-test: exact -->
```python
from prik.codegen.c.binding import CBindingGenerator
from prik.planning.models import (
    BindingFunctionPlan, BindingModulePlan, BridgeFunctionPlan,
    BridgeModulePlan, FunctionPlan, ModulePlan,
    NativeEntrypointFunctionPlan, NativeEntrypointModulePlan,
    NativeGeneratedCodeGroupKind, NativeGeneratedCodeGroupPlan, NamespacePlan,
)
from prik.policy.models import (
    ExternalDeclarationMode, NativeEntrypointAction, NativeInvocationKind,
)
from prik.printers.c import CSourcePrinter

binding = BindingFunctionPlan(
    python_name="ping",
    docstring="Call PING.",
    release_gil=False,
    status_error=None,
    argument_conversion_order=(),
)
bridge = BridgeFunctionPlan(
    native_name="PING",
    native_invocation=NativeInvocationKind.PROCEDURE,
    native_operator=None,
    standalone=True,
    external_declaration=ExternalDeclarationMode.IMPLICIT_EXTERNAL,
    native_module=None,
    native_is_subroutine=True,
)
entrypoint = NativeEntrypointFunctionPlan(
    symbol_name="bind_c_ping",
    action=NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER,
    parameters=(),
    results=(),
    projected_slots=(),
)
function = FunctionPlan(
    owner_path="demo.ping",
    symbol_name="ping",
    binding=binding,
    entrypoint=entrypoint,
    bridge=bridge,
    class_call=None,
    arguments=(),
    results=(),
    declaration_callables=(),
    available_roles=(),
)
namespace = NamespacePlan(
    owner_path="demo",
    python_path=(),
    functions=(function,),
    docstring="Manual codegen demonstration.",
)
plan = ModulePlan(
    owner_path="demo",
    binding=BindingModulePlan(owner_path="demo", public_root="demo"),
    entrypoint=NativeEntrypointModulePlan(owner_path="demo"),
    bridge=BridgeModulePlan(owner_path="demo"),
    namespaces=(namespace,),
    native_generated_code_groups=(
        NativeGeneratedCodeGroupPlan(
            kind=NativeGeneratedCodeGroupKind.FORTRAN_ADAPTERS,
            language="fortran",
            member_keys=("demo.ping",),
            source_paths=("bind_c_demo_wrapper.f90",),
        ),
    ),
)

generator = CBindingGenerator()
generator.require_supported(plan)
c_module, _header = generator.visit(plan)
wrapper = next(item for item in c_module.functions if item.name == "wrap_ping")
print(CSourcePrinter().doprint(wrapper))
```
<!-- prik-doc-test-output -->
```text
/* Python callable 'ping'. */
/* Calls the native entrypoint 'bind_c_ping'. */
static PyObject * wrap_ping(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "", kwlist)) return NULL;
    bind_c_ping();
    Py_RETURN_NONE;
}
```

</details>

The binding record's public name produces `wrap_ping`; the entrypoint record
supplies `bind_c_ping`. The C generator adds CPython parsing and result
mechanics, but the selected plan remains the reason that call is permitted and
named that way. The bridge record's `PING` target is deliberately unavailable
to this generator.

## Run The Module Demonstration

`binding.py` also contains a direct demonstration of its normal input route.
It constructs one scalar semantic function, completes policy, builds its plan,
preflights C scalar support, lowers the binding nodes, and prints the header
and wrapper through `CSourcePrinter`. Expand **Example source** on the
published site to see that exact `__main__` setup.

```bash
python3 prik/codegen/c/binding.py
```

```text
Rendered C header:
#ifndef BINDING_DEMO_WRAPPER_H
#define BINDING_DEMO_WRAPPER_H
#include <Python.h>
static PyObject * wrap_double_value(PyObject * self, PyObject * args, PyObject * kwargs);
#endif /* BINDING_DEMO_WRAPPER_H */

Rendered C binding wrapper:
/* Python callable 'double_value'. */
/* Calls the native entrypoint 'bind_c_double_value'. */
static PyObject * wrap_double_value(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"value", NULL};
    PyObject * bound_value_obj;
    double bound_value;
    double result;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", kwlist, &bound_value_obj)) return NULL;
    if (prik_float64_unpack_exact(bound_value_obj, &bound_value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument value. Received <class '%s'>", Py_TYPE(bound_value_obj)->tp_name); } return NULL; };
    result = bind_c_double_value(bound_value);
    PyObject * result_obj = prik_float64_to_numpy(&result);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}
```

The header exposes the planned entrypoint prototype. The wrapper's rendered
body shows the Python-to-entrypoint call and conversion back to a NumPy scalar
result. Policy may route that forward call to an original Fortran `bind(C)`
symbol, a generated Fortran adapter, or the completed user C symbol.
Binding-owned callback trampolines are
reverse-call entrypoints used by adapter-local callback procedures.

## Change Routes And Evidence

- Change CPython extraction, Python results, C errors, or binding-side
  lifecycle emission in `binding.py`.
- Change generated class, holder, or proxy Python source in
  [`python_surface.py`](../../../../prik/codegen/c/python_surface.py).
- Change cross-backend names used only by C helpers in
  [`naming.py`](../../../../prik/codegen/c/naming.py).
- If the change needs a new ownership, transfer, or projection decision, stop
  at `policy/` or `planning/`; do not add a binding-local fallback.

| Evidence | What it establishes |
| --- | --- |
| [Binding infrastructure](../../../../tests/fortran/infrastructure/codegen/test_binding.py) | Invalid NumPy scalar macros fail at the C binding helper boundary. |
| [Wrapper-generator handoff](../../../../tests/fortran/infrastructure/pipeline/test_wrapper_generator.py) | Frozen-plan validation and generated C binding, header, and wrapper assembly. |
| [Array lowering](../../../../tests/fortran/arrays/codegen/test_specialized_array_roles.py) | Plan-selected specialized array roles lower through the binding boundary. |

## Failure Boundary

The C backend reports an unsupported completed action, unavailable scalar
spelling, invalid plan reference, or missing node visitor. It delegates missing
semantic decisions to `policy/` and `planning/`, source formatting to
`printers/`, and compilation to `compiler/`. Start with the first invalid plan
record, not with the generated C compiler diagnostic.
