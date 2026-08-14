---
title: Fortran Bridge Lowering
audience: developers, maintainers, contributors
prerequisites: Code Generation Stage guide, completed wrapper plan
related: ../../architecture.md, ../codegen.md, ../planning.md, ../printers.md, c-binding.md
status: maintained
publication: reviewed
---

# Fortran Bridge Lowering

## Role And Boundary

[`prik/codegen/fortran/bridge.py`](../../../../prik/codegen/fortran/bridge.py)
lowers the bridge view of a completed `ModulePlan` into a `FortranModule`. The
result is a typed Fortran syntax tree, not formatted source or a compiled
library. `FortranSourcePrinter` serializes it later.

The bridge implements the ABI selected by the plan: `bind(C)` procedures,
native imports and interfaces, declarations, representation conversion,
ordered native calls, writeback, cleanup, and derived-value lifecycles. It
does not infer a native interface, argument optionality, ownership, or result
projection from source-language details.

## Input And Output

```text
ModulePlan.bridge + namespaces + function bridge views
  -> FortranBridgeGenerator.require_supported()
  -> FortranBridgeGenerator.visit()
  -> FortranModule
  -> FortranSourcePrinter
  -> Fortran bridge source
```

`require_supported()` verifies only that selected primitive representations can
be emitted. It does not validate or complete the cross-backend plan; the normal
`WrapperGenerator` handoff does that before it calls this backend.

## Lowering Algorithm

`_visit_ModulePlan()` collects the `iso_c_binding` symbols, required native
module uses, interfaces, holder definitions, and procedures for every
namespace. It adds derived and callback support only when plan facts require
them.

`_visit_FunctionPlan()` preserves the plan's execution order:

1. It determines the bridge result form and orders ABI parameters by their
   recorded position.
2. It emits declarations and representation initializers, then forms the
   native invocation from the ordered call slots.
3. It runs the selected writeback and cleanup finalizers, wrapping derived
   result or carrier lifecycles when the plan requires them.

The bridge result exposes a `bind(C)` name for the C binding. For a standalone
native procedure, the bridge record explicitly selects its external declaration;
for a module procedure, it supplies the native module use. Those are completed
plan facts, not heuristics in the generator.

## Run A Minimal Manual Plan

This is the same complete no-argument `PING` plan used by the C binding deep
dive. With no transfers, results, slots, or lifecycle actions, it is small
enough to construct explicitly while still containing both mandatory module
views and a complete bridge record.

Real builds must obtain plans from `WrapperPlanner` after policy completion and
must pass through `WrapperGenerator` for freezing and cross-backend validation.
Use direct construction only to inspect a backend lowering path.

### Plan Shape

This abbreviated, non-runnable sketch shows the records in construction order.
Expand the full source to run the complete example.

```python
binding = BindingFunctionPlan(...)
bridge = BridgeFunctionPlan(...)
function = FunctionPlan(..., binding=binding, bridge=bridge)
namespace = NamespacePlan(..., functions=(function,))
plan = ModulePlan(
    binding=BindingModulePlan(...),
    bridge=BridgeModulePlan(...),
    namespaces=(namespace,),
)

generator = FortranBridgeGenerator()
bridge_module = generator.visit(plan)
print(FortranSourcePrinter().doprint(...))
```

<details markdown="1">
<summary>Full runnable source</summary>

<!-- prik-doc-test: exact -->
```python
from prik.codegen.fortran.bridge import FortranBridgeGenerator
from prik.planning.models import (
    BindingFunctionPlan, BindingModulePlan, BridgeFunctionPlan,
    BridgeModulePlan, FunctionPlan, ModulePlan, NamespacePlan,
)
from prik.policy.models import ExternalDeclarationMode, NativeInvocationKind
from prik.printers.fortran import FortranSourcePrinter

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
function = FunctionPlan(
    owner_path="demo.ping",
    symbol_name="ping",
    binding=binding,
    bridge=bridge,
    class_call=None,
    arguments=(),
    results=(),
    native_call_slots=(),
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
    binding=BindingModulePlan(owner_path="demo"),
    bridge=BridgeModulePlan(owner_path="demo"),
    namespaces=(namespace,),
)

generator = FortranBridgeGenerator()
generator.require_supported(plan)
bridge_module = generator.visit(plan)
print(FortranSourcePrinter().doprint(bridge_module.procedures[0]))
```
<!-- prik-doc-test-output -->
```text
subroutine bind_c_ping() bind(c, name="bind_c_ping")
  external :: PING
  call PING()
end subroutine bind_c_ping
```

</details>

The bridge record fixes the public C-ABI name and marks `PING` as an external
subroutine. The generator contributes the bridge declaration and call syntax;
it does not decide whether `PING` is callable or how values cross the boundary.

## Run The Module Demonstration

`bridge.py` also contains a direct demonstration of its normal input route. It
constructs one scalar semantic function, completes policy, builds its plan,
preflights bridge scalar support, lowers the Fortran nodes, and prints the
module through `FortranSourcePrinter`. Expand **Example source** on the
published site to see that exact `__main__` setup.

```bash
python3 prik/codegen/fortran/bridge.py
```

```text
Rendered Fortran bridge source:
module bind_c_bridge_demo_wrapper
  use iso_c_binding, only: &
    c_associated, &
    c_bool, &
    c_char, &
    c_double, &
    c_double_complex, &
    c_f_pointer, &
    c_float, &
    c_float_complex, &
    c_int8_t, &
    c_int16_t, &
    c_int, &
    c_int32_t, &
    c_int64_t, &
    c_loc, &
    c_null_char, &
    c_ptr, &
    c_null_ptr, &
    c_size_t, &
    c_sizeof
  use bridge_demo, only: native_double_value => DOUBLE_VALUE
  implicit none
contains
  function bind_c_double_value(value) result(result) bind(c, name="bind_c_double_value")
    real(c_double), value :: value
    real(c_double) :: result
    result = native_double_value(value)
  end function bind_c_double_value
end module bind_c_bridge_demo_wrapper
```

The module and procedure names identify the planned C-ABI boundary. The final
assignment is the printed native call that the completed bridge plan selected.
`DOUBLE_VALUE` remains the procedure exported by `bridge_demo`; the `use`
statement imports it locally as `native_double_value`, so the bridge calls that
alias. This gives every imported module procedure a distinct bridge-local name.

## Change Routes And Evidence

- Change bridge ABI declarations, native invocation, conversion, writeback, or
  cleanup in `bridge.py`.
- Change a primitive's Fortran spelling in
  [`primitive_scalar_types.py`](../../../../prik/codegen/primitive_scalar_types.py).
- If an ABI fact is absent from a bridge record, add the completed policy and
  plan fact upstream; do not inspect semantic source or invent a default here.

| Evidence | What it establishes |
| --- | --- |
| [Wrapper-generator handoff](../../../../tests/fortran/infrastructure/pipeline/test_wrapper_generator.py) | Frozen-plan validation and generated Fortran bridge assembly. |
| [Module-variable lowering](../../../../tests/fortran/modules/codegen/test_scalar_module_variable_lowering.py) | Matched C and Fortran scalar module-variable operations and their bridge procedures. |
| [Array lowering](../../../../tests/fortran/arrays/codegen/test_specialized_array_roles.py) | Plan-selected specialized array roles lower through the bridge ABI. |

## Failure Boundary

The bridge reports unavailable primitive spellings, unsupported completed
actions, invalid plan references, and missing node visitors. It delegates
missing semantic choices to `policy/` and `planning/`, source formatting to
`printers/`, and compilation to `compiler/`. Start with the first invalid plan
record or bridge procedure, not with a later Fortran compiler error.
