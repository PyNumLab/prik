"""Public PRIK API."""

from importlib import import_module
from importlib.metadata import version as _distribution_version

from prik.parsers.c.models import CFile, CParseError, CProject
from prik.parsers.c.parser import parse_c_file, parse_c_project
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranBlockData,
    FortranDerivedType,
    FortranFile,
    FortranInterface,
    FortranModule,
    FortranParseError,
    FortranProcedureSignature,
    FortranProgram,
    FortranProject,
    FortranSubmodule,
)
from prik.parsers.fortran.parser import parse_fortran_file, parse_fortran_project
from prik.parsers.pyi import parse_pyi_file, parse_pyi_text
from prik.semantics.fortran2ir import (
    collect_semantic_compile_time_requirements,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    fortran_project_to_semantic_modules,
    resolve_semantic_compile_time_values,
)
from prik.semantics.c2ir import (
    CToIRConverter,
    c_file_to_semantic_module,
    c_file_to_semantic_modules,
    c_function_to_semantic_function,
    c_parameter_to_semantic_argument,
    c_project_to_semantic_module,
    c_project_to_semantic_modules,
    c_struct_to_semantic_class,
    c_type_to_semantic_type,
)
from prik.semantics.pyi2ir import convert_pyi_to_ir
from prik.pipeline.pyi import (
    emit_module_stubs,
    opaque_dependency_modules,
    pyi_file_to_semantic_module,
    pyi_paths_to_semantic_modules,
    pyi_text_to_semantic_module,
)
from prik.runtime.handles import AllocatableArray, NativeArrayHandleBase, PointerArray

__version__ = _distribution_version("prik")

_CLI_EXPORTS = {"main"}
_FORTRAN_TYPE_PROBE_EXPORTS = {
    "FortranTypeProbeError",
    "FortranTypeProbeReport",
    "build_fortran_type_probe_source",
    "evaluate_fortran_type_requirements",
    "fortran_type_probe_expressions",
    "probe_fortran_type_expressions",
}
_WRAPPING_EXPORTS = {
    "NativeBuildPlan",
    "NativeCompilationUnit",
    "NativeLinkItem",
    "NativePrebuiltArtifact",
    "WrapperBuildResult",
    "build_fortran_extension",
    "build_pyi_extension",
    "build_pyi_extension_from_manifest",
}


def __getattr__(name: str):
    if name in _CLI_EXPORTS:
        module = import_module("prik.cli")
        return getattr(module, name)
    if name in _FORTRAN_TYPE_PROBE_EXPORTS:
        module = import_module("prik.preprocessing.probes.fortran_types")
        return getattr(module, name)
    if name in _WRAPPING_EXPORTS:
        module = import_module("prik.pipeline.build")
        return getattr(module, name)
    raise AttributeError(f"module 'prik' has no attribute {name!r}")


__all__ = (
    "AllocatableArray",
    "CFile",
    "CParseError",
    "CProject",
    "CToIRConverter",
    "FortranArgument",
    "FortranBlockData",
    "FortranDerivedType",
    "FortranFile",
    "FortranInterface",
    "FortranModule",
    "FortranParseError",
    "FortranProcedureSignature",
    "FortranProgram",
    "FortranProject",
    "FortranSubmodule",
    "FortranTypeProbeError",
    "FortranTypeProbeReport",
    "NativeArrayHandleBase",
    "NativeBuildPlan",
    "NativeCompilationUnit",
    "NativeLinkItem",
    "NativePrebuiltArtifact",
    "PointerArray",
    "WrapperBuildResult",
    "__version__",
    "build_fortran_extension",
    "build_fortran_type_probe_source",
    "build_pyi_extension",
    "build_pyi_extension_from_manifest",
    "c_file_to_semantic_module",
    "c_file_to_semantic_modules",
    "c_function_to_semantic_function",
    "c_parameter_to_semantic_argument",
    "c_project_to_semantic_module",
    "c_project_to_semantic_modules",
    "c_struct_to_semantic_class",
    "c_type_to_semantic_type",
    "collect_semantic_compile_time_requirements",
    "convert_pyi_to_ir",
    "emit_module_stubs",
    "evaluate_fortran_type_requirements",
    "fortran_file_to_semantic_modules",
    "fortran_module_to_semantic_module",
    "fortran_project_to_semantic_modules",
    "fortran_type_probe_expressions",
    "main",
    "opaque_dependency_modules",
    "parse_c_file",
    "parse_c_project",
    "parse_fortran_file",
    "parse_fortran_project",
    "parse_pyi_file",
    "parse_pyi_text",
    "probe_fortran_type_expressions",
    "pyi_file_to_semantic_module",
    "pyi_paths_to_semantic_modules",
    "pyi_text_to_semantic_module",
    "resolve_semantic_compile_time_values",
)


if __name__ == "__main__":
    parsed = parse_fortran_file("subroutine ping()\nend subroutine ping\n", filename="ping.f90")
    procedure = parsed.procedures[0]

    print(f"PRIK {__version__}")
    print(f"Public parser result: {procedure.kind} {procedure.name} from {parsed.filename}")
