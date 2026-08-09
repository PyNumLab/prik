"""Edit one wrapper plan and inspect the generated binding and bridge."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np

from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline import build as pipeline
from prik.pipeline.preprocessing import PreprocessingConfig
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.policy_completion import complete_semantic_policies
from prik.codegen import (
    CBindingGenerator,
    FortranBridgeGenerator,
    WrapperCodeGenerator,
    WrapperPlanner,
)


# Choose one starting point. Both paths then use the same plan, generator, and build steps.
ENTRY = os.environ.get("PRIK_WALKTHROUGH_ENTRY", "pyi")  # "fortran" or "pyi"

# This is the manual plan edit. Change it back to "ADD_R8" to generate addition.
PLAN_NATIVE_TARGET = "SUB_R8"

DEMO_FORTRAN_SOURCE = """\
      REAL*8 FUNCTION ADD_R8(X, Y)
      REAL*8 X, Y
      ADD_R8 = X + Y
      END
      REAL*8 FUNCTION SUB_R8(X, Y)
      REAL*8 X, Y
      SUB_R8 = X - Y
      END
"""

DEMO_PYI_CONTRACT = """\
from prik.contracts import Addr, Arg, Float64, bind, native_call, standalone

@bind("ADD_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def calculate(x: Float64, y: Float64) -> Float64: ...
"""


if shutil.which("gfortran") is None:
    raise RuntimeError("This walkthrough needs gfortran")

workdir = Path(tempfile.mkdtemp(prefix="prik-wrapper-plan-walkthrough-"))
source = workdir / "native.f"
contract = workdir / "demo.pyi"
source.write_text(DEMO_FORTRAN_SOURCE, encoding="utf-8")
contract.write_text(DEMO_PYI_CONTRACT, encoding="utf-8")
print(f"WORKDIR={workdir}")


# 1. Input -> one semantic module. This is the only input-specific part.
print(f"\n== {ENTRY.upper()} INPUT -> SEMANTIC MODULE ==")
if ENTRY == "fortran":
    project = parse_fortran_project({str(source): pipeline._fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(project)
    pipeline._apply_source_python_exports(modules)
    module = pipeline._merge_wrapper_modules(modules, name="demo")
elif ENTRY == "pyi":
    bundle = pipeline._pyi_contract_bundle(contract)
    module = pipeline._merge_wrapper_modules(list(bundle.modules), name="demo")
else:
    raise ValueError("ENTRY must be 'fortran' or 'pyi'")
print(f"module={module.name}; functions={[function.name for function in module.functions]}")


# 2. Semantic module -> editable wrapper plan. Inspect the selected records directly.
print("\n== EDITABLE WRAPPER PLAN ==")
complete_semantic_policies(module)
plan = WrapperPlanner().build(module)
namespace = next(
    namespace
    for namespace in plan.namespaces
    if any(function.bridge.native_name == "ADD_R8" for function in namespace.functions)
)
function = next(function for function in namespace.functions if function.bridge.native_name == "ADD_R8")
function.bridge.native_name = PLAN_NATIVE_TARGET
print(f"module: {plan.owner_path}")
binding_generator = CBindingGenerator()
bridge_generator = FortranBridgeGenerator()
for item in plan.namespaces:
    path = ".".join(item.python_path) or "<root>"
    print(f"namespace {path}: {item.owner_path}")
    for planned_function in item.functions:
        print(f"  function: {planned_function.owner_path}")
        print(f"    Python name: {planned_function.binding.python_name}")
        print(f"    native target: {planned_function.bridge.native_name}")
        for argument in planned_function.arguments:
            print(
                f"    argument {argument.binding.python_name}: "
                f"binding action={argument.binding.optional_mode!r}, "
                f"bridge action={argument.bridge.optional_mode!r}"
            )
        if not planned_function.results:
            print("    result: binding=<return None>, bridge=<no result>")
        else:
            for result in planned_function.results:
                print(
                    f"    result {result.result_position}: binding action={result.binding.codegen_action!r}, "
                    f"bridge action={result.bridge.codegen_action!r}"
                )
    for variable in item.variables:
        print(
            f"  variable {variable.binding.python_names}: "
            f"binding getter={variable.binding.getter_action!r}, setter={variable.binding.setter_action!r}; "
            f"bridge getter={variable.bridge.getter_action!r}, "
            f"assignment={variable.bridge.native_assignment!r}"
        )
print("native slots:", function.native_call_slots)
print("result plans:", function.results)


# 3. Editable plan -> generated C binding and Fortran bridge sources.
print("\n== GENERATED ARTIFACTS ==")
artifacts = WrapperCodeGenerator(
    c_generator=binding_generator,
    fortran_generator=bridge_generator,
).generate(plan)
for artifact in artifacts.sources:
    print(f"--- {artifact.path} ---")
    print(artifact.text)


# 4. Generated artifacts + native Fortran -> one importable extension.
print("\n== BUILD AND RUN ==")
build_dir = workdir / "build"
build_dir.mkdir()
compiler = pipeline._new_compiler()
native_object = pipeline._source_compile_object(source, build_dir, object_stem="native")
compiler.compile_object(native_object, verbose=False)
native_build_plan = pipeline.NativeBuildPlan(
    produced_objects=(native_object.object_path,),
    module_dirs=(build_dir,),
    include_dirs=(build_dir,),
)
build = pipeline._build_rendered_wrapper_extension(
    artifacts,
    output_dir=build_dir,
    sources=(source,) if ENTRY == "fortran" else (contract,),
    native_build_plan=native_build_plan,
    native_dependencies=(native_object,),
    native_link_args=pipeline._rendered_wrapper_native_link_args(native_build_plan),
    compiler=compiler,
)
sys.path.insert(0, str(build.output_dir))
extension = importlib.import_module(build.module_name)
sys.path.remove(str(build.output_dir))
public_namespace = extension
for part in namespace.python_path:
    public_namespace = getattr(public_namespace, part)
wrapped = getattr(public_namespace, function.binding.python_name)
value = wrapped(np.float64(1.5), np.float64(2.25))
print(f"{function.binding.python_name}(1.5, 2.25) through {PLAN_NATIVE_TARGET} = {value!r}")
