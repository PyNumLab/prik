"""Generate complete rendered wrappers from editable wrapper plans.

``WrapperGenerator`` is the pipeline boundary between an editable
``ModulePlan`` and source-bearing ``GeneratedWrapper``. It validates cross-view
plan consistency, asks each backend to preflight and lower its completed plan,
prints the resulting C, Fortran, and header nodes, assigns stable filenames,
and returns the complete handoff consumed by build integration.

Its public surface is ``GeneratedSource``, ``GeneratedWrapper``, and
``WrapperGenerator.generate()``. The private sections first report completed-
plan inconsistencies, then assemble the rendered wrapper; they do not infer
semantic policy.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import time

from prik.utilities.stage_values import StageRecord
from prik.policy.ownership import (
    AssignmentMode,
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    SetterAction,
    StorageMode,
    TransferMode,
)
from prik.semantics.metadata import SCALAR_STORAGE_CATEGORY
from prik.policy.models import (
    ArgumentHandoffMode,
    ArrayLogicalABI,
    ArrayWritebackABI,
    BridgeDataAction,
    CallbackABIKind,
    CallbackFatalAction,
    CallbackGILAction,
    CallbackLifecycleAction,
    CallbackResultAction,
    CallbackThreadAction,
    CallbackTransferAction,
    ClassConstructorKind,
    ClassInvocationKind,
    ConstructionLifecycleAction,
    DerivedActualAccess,
    DerivedCallAction,
    DerivedDummyCategory,
    DerivedFieldAccessMechanism,
    DerivedNativeHandoff,
    DerivedObjectStorage,
    DerivedObjectOrigin,
    DerivedOwnerRetention,
    DerivedRelease,
    DerivedWriteback,
    DeclarationCallableAction,
    DirectResultABI,
    LifecycleOperation,
    FIXED_STRING_RESULT_COPY_REASON,
    OWNED_NATIVE_ARRAY_HANDLE_COPY_REASON,
    ORDINARY_ARRAY_RESULT_COPY_REASON,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    NativeInvocationKind,
    NativeEntrypointAction,
    NativeArrayDescriptorInterop,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorOwnership,
    NativeArrayDefaultConstruction,
    NativeArrayDestroyBehavior,
    NativeArrayExtractionAction,
    NativeArrayHandleKind,
    NativeArrayHandleOrigin,
    NativeArrayOperation,
    NativeArrayOutputProjection,
    NativeArrayOwnerRetention,
    NativeArrayRelease,
    NativeArraySourceKind,
    NativeDescriptorHandoffABI,
    OptionalMode,
    PythonExceptionKind,
    RAW_STRING_ADDRESS_COPY_REASON,
    SCALAR_DESCRIPTOR_RESULT_COPY_REASON,
    ScalarLogicalABI,
    STRING_INPUT_COPY_REASON,
    STRING_REPLACEMENT_COPY_REASON,
    STRING_STORAGE_COPY_REASON,
    TransformationAction,
    TransformationLayer,
    WritebackPhase,
)
from prik.policy.native_array_handles import NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER
from prik.codegen.c.binding import CBindingGenerator
from prik.codegen.docstrings import WrapperDocstringBuilder
from prik.codegen.fortran.bridge import FortranBridgeGenerator
from prik.planning.models import (
    ArrayHandoffPlan,
    ArgumentTransferPlan,
    CallbackHandoffPlan,
    CallbackTransferPlan,
    OverloadPlan,
    ClassSurfacePlan,
    DatatypeFamily,
    DeclarationCallablePlan,
    FunctionPlan,
    LifecycleActionPlan,
    ModulePlan,
    ModuleVariablePlan,
    NativeArrayHandlePlan,
    NativeEntrypointProjectedSlotPlan,
    NativeGeneratedCodeGroupKind,
    NativeGeneratedCodeGroupPlan,
    NamespacePlan,
    GeneratedSupportProcedureImplementationOwner,
    GeneratedSupportProcedureEntrypointPlan,
    ProcedurePrototypeArgumentPlan,
    ProcedurePrototypePlan,
    ProcedurePrototypeResultPlan,
    ResultPlan,
    WrapperPlanDiagnostic,
)
from prik.planning.entrypoints import build_generated_support_procedure_projection
from prik.printers import CSourcePrinter, FortranSourcePrinter

__all__ = ("GeneratedSource", "GeneratedWrapper", "WrapperGenerator")


@dataclass
class GeneratedSource(StageRecord):
    """One generated source payload before it is written to disk."""

    path: Path
    text: str


@dataclass
class GeneratedWrapper(StageRecord):
    """Rendered wrapper sources and the metadata required by build integration."""

    module_name: str
    sources: tuple[GeneratedSource, ...]
    bridge_sources: tuple[Path, ...]
    binding_sources: tuple[Path, ...]
    headers: tuple[Path, ...]
    native_support_keys: tuple[str, ...]
    required_headers: tuple[str, ...]
    extension_init_name: str
    required_link_languages: tuple[str, ...] = ()
    native_generated_code_groups: tuple[NativeGeneratedCodeGroupPlan, ...] = ()

    @property
    def source_paths(self) -> tuple[Path, ...]:
        """Return generated payload paths in stable write order."""
        return tuple(source.path for source in self.sources)

    @property
    def compile_sources(self) -> tuple[Path, ...]:
        """Return bridge and binding source paths in compiler order."""
        return (*self.bridge_sources, *self.binding_sources)

    @property
    def generated_files(self) -> tuple[Path, ...]:
        """Return all generated wrapper paths, including headers."""
        return (*self.compile_sources, *self.headers)


class WrapperGenerator:
    """Turn one editable ``ModulePlan`` into one complete generated wrapper.

    Use :meth:`generate` after ``WrapperPlanner.build`` and before build
    integration writes or compiles sources.  This class owns the plan's final
    freeze and cross-backend consistency validation, then delegates backend
    node construction and source printing to the injected or default C and
    Fortran components.  Its private sections cover the generation entrypoint,
    typed plan diagnostics, and generated-wrapper assembly.
    """

    def __init__(
        self,
        *,
        c_generator: CBindingGenerator | None = None,
        fortran_generator: FortranBridgeGenerator | None = None,
        docstring_builder: WrapperDocstringBuilder | None = None,
        c_printer: CSourcePrinter | None = None,
        fortran_printer: FortranSourcePrinter | None = None,
    ):
        """Create a generator with default or explicitly supplied backend components.

        Supplying a docstring builder, backend generator, or printer is useful
        when an established caller needs to observe or substitute one
        generation component. Omitted components use the standard plan-driven
        documentation, direct-lowering, and printing paths; no semantic policy
        is stored or inferred during initialization.
        """
        self._c_generator = c_generator or CBindingGenerator()
        self._fortran_generator = fortran_generator or FortranBridgeGenerator()
        self._docstring_builder = docstring_builder or WrapperDocstringBuilder()
        self._c_printer = c_printer or CSourcePrinter()
        self._fortran_printer = fortran_printer or FortranSourcePrinter()

    # Public entrypoint: freeze, validate, preflight, lower, print, and assemble.
    def generate(
        self,
        plan: ModulePlan,
        *,
        progress: Callable[[str, float | None], None] | None = None,
    ) -> GeneratedWrapper:
        """Render one editable plan into a complete generated wrapper.

        The received ``plan`` is frozen before validation, so later mutation
        raises the stage-record error.  ``progress``, when provided, receives
        a stage label with ``None`` before each rendering operation and the
        same label with its elapsed seconds afterward.  The result is normally
        passed to build integration, which owns writing and compilation.

        Raises:
            ValueError: If the frozen plan is inconsistent or a selected
                backend cannot lower one of its completed actions.
        """
        # Complete presentation from the editable plan before consuming and freezing it.
        self._docstring_builder.render(plan)

        # Freeze the exact editable handoff, then validate cross-backend plan facts.
        plan.freeze()
        self._validate_plan(plan)

        # Each backend preflights only the typed mechanisms it is responsible for.
        self._c_generator.require_supported(plan)
        if plan.bridge is not None:
            self._fortran_generator.require_supported(plan)

        # Lower and print binding translation units in their established progress order.
        if progress is not None:
            progress("Generate binding source", None)
            started = time.perf_counter()
        c_modules = self._c_generator.binding_modules(plan)
        c_sources = tuple(self._c_printer.doprint(module) for module in c_modules)
        c_module_names = tuple(module.name for module in c_modules)
        if progress is not None:
            progress("Generate binding source", time.perf_counter() - started)

        # Lower a bridge only when planning selected at least one Fortran-owned
        # adapter or generated support procedure for this module.
        fortran_source = None
        if plan.bridge is not None:
            if progress is not None:
                progress("Generate bridge source", None)
                started = time.perf_counter()
            fortran_module = self._fortran_generator.visit(plan)
            fortran_source = self._fortran_printer.doprint(fortran_module)
            if progress is not None:
                progress("Generate bridge source", time.perf_counter() - started)

        # Render the shared binding header after all source nodes are available.
        if progress is not None:
            progress("Generate binding header", None)
            started = time.perf_counter()
        c_header = self._c_generator.binding_header(plan)
        c_header_source = self._c_printer.doprint(c_header)
        if progress is not None:
            progress("Generate binding header", time.perf_counter() - started)

        # Assemble source text with the stable filenames consumed by build integration.
        return self._generated_wrapper(
            plan.owner_path,
            c_sources,
            c_module_names,
            c_header_source,
            fortran_source,
            native_support_keys=(("binding_support",) if self._c_generator.requires_native_support(plan) else ()),
            required_headers=plan.required_headers,
            required_link_languages=plan.entrypoint.native_languages,
            native_generated_code_groups=plan.native_generated_code_groups,
        )

    # Plan-consistency diagnostics: module graph first, then typed member records.
    def _validate_plan(self, plan: ModulePlan) -> None:
        """Raise one ordered summary when the final frozen plan is inconsistent.

        The method consumes the exact frozen plan passed to :meth:`generate`.
        It retains every typed diagnostic in collection order so callers see a
        stable, owner-local error summary before either backend lowers nodes.
        """
        diagnostics = self._plan_diagnostics(plan)
        if diagnostics:
            raise ValueError(self._diagnostic_summary(diagnostics))

    def _plan_diagnostics(self, plan: ModulePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Collect ordered cross-backend diagnostics for one frozen module plan.

        Module identity and namespace structure are checked first, followed by
        each namespace-owned function, variable, class, and overload.  Global
        class, symbol, and header consistency checks finish the collection.
        The method only reports facts already present in the plan.
        """
        diagnostics = []

        # Validate module ownership and the complete namespace tree before member links.
        if plan.binding.owner_path != plan.owner_path:
            diagnostics.append(self._diagnostic(plan.owner_path, "binding-module-owner", plan.binding.owner_path))
        diagnostics.extend(self._binding_public_root_diagnostics(plan))
        if plan.entrypoint.owner_path != plan.owner_path:
            diagnostics.append(self._diagnostic(plan.owner_path, "entrypoint-module-owner", plan.entrypoint.owner_path))
        if plan.bridge is not None and plan.bridge.owner_path != plan.owner_path:
            diagnostics.append(self._diagnostic(plan.owner_path, "bridge-module-owner", plan.bridge.owner_path))
        diagnostics.extend(self._native_generated_code_group_diagnostics(plan))
        if (plan.bridge is not None) is not bool(plan.native_generated_code_groups):
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-module-bridge-presence",
                    bool(plan.native_generated_code_groups),
                )
            )
        diagnostics.extend(self._generated_support_procedure_entrypoint_diagnostics(plan))
        diagnostics.extend(self._namespace_tree_diagnostics(plan))

        # Validate every typed member against the shared records in its namespace.
        for namespace in plan.namespaces:
            diagnostics.extend(self._namespace_diagnostics(namespace))
            for function in namespace.functions:
                diagnostics.extend(self._function_diagnostics(function))
            for variable in namespace.variables:
                diagnostics.extend(self._module_variable_diagnostics(variable))
            for class_surface in namespace.classes:
                diagnostics.extend(self._class_surface_diagnostics(namespace, class_surface))
            functions = {id(function) for function in namespace.functions}
            for overload in namespace.overloads:
                diagnostics.extend(self._overload_diagnostics(overload, functions))

        # Validate graph-wide ordering, generated spellings, and header dependencies.
        diagnostics.extend(self._class_graph_diagnostics(plan))
        diagnostics.extend(self._generated_symbol_diagnostics(plan))
        diagnostics.extend(self._required_header_diagnostics(plan))
        return tuple(diagnostics)

    def _binding_public_root_diagnostics(self, plan: ModulePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the completed public presentation root before C lowering."""
        root = plan.binding.public_root
        if isinstance(root, str) and (not root or root.isidentifier()):
            return ()
        return (self._diagnostic(plan.owner_path, "binding-public-root", repr(root)),)

    def _native_generated_code_group_diagnostics(
        self,
        plan: ModulePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require exact independent adapter and Fortran-support membership."""
        adapter_members = tuple(
            function.owner_path
            for namespace in plan.namespaces
            for function in namespace.functions
            if function.entrypoint.action is NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER
        )
        support_members = tuple(
            procedure.key
            for procedure in plan.entrypoint.support_procedures
            if procedure.implementation_owner is GeneratedSupportProcedureImplementationOwner.FORTRAN
        )
        expected_members = {
            NativeGeneratedCodeGroupKind.FORTRAN_ADAPTERS: adapter_members,
            NativeGeneratedCodeGroupKind.FORTRAN_SUPPORT: support_members,
        }
        groups = plan.native_generated_code_groups
        diagnostics = []
        if len({group.kind for group in groups}) != len(groups):
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path, "duplicate-native-generated-code-group", tuple(g.kind for g in groups)
                )
            )
        for kind, members in expected_members.items():
            actual = next((group for group in groups if group.kind is kind), None)
            if bool(actual) is not bool(members):
                diagnostics.append(self._diagnostic(plan.owner_path, "missing-native-generated-code-group", kind))
                continue
            if actual is None:
                continue
            if actual.language != "fortran" or actual.member_keys != members or not actual.source_paths:
                diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-native-generated-code-group", kind))
        if any(group.kind not in expected_members for group in groups):
            diagnostics.append(
                self._diagnostic(plan.owner_path, "unknown-native-generated-code-group", tuple(g.kind for g in groups))
            )
        return tuple(diagnostics)

    def _generated_support_procedure_entrypoint_diagnostics(
        self,
        plan: ModulePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one complete planner-owned support-procedure registry."""
        diagnostics = []
        operations = plan.entrypoint.support_procedures
        keys = tuple(operation.key for operation in operations)
        symbols = tuple(operation.symbol_name for operation in operations)
        if len(keys) != len(set(keys)):
            diagnostics.append(self._diagnostic(plan.owner_path, "duplicate-auxiliary-entrypoint-key", keys))
        if len(symbols) != len(set(symbols)):
            diagnostics.append(self._diagnostic(plan.owner_path, "duplicate-auxiliary-entrypoint-symbol", symbols))
        for operation in operations:
            diagnostics.extend(self._generated_support_procedure_diagnostics(operation))
        try:
            expected_projection = build_generated_support_procedure_projection(plan.namespaces)
        except ValueError as error:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-auxiliary-entrypoint-inventory", str(error)))
            return tuple(diagnostics)
        expected = expected_projection.support_procedures
        binding_inventories = (
            plan.binding.owned_derived_type_owner_paths,
            plan.binding.allocatable_holder_type_owner_paths,
            plan.binding.pointer_holder_type_owner_paths,
        )
        expected_binding_inventories = (
            expected_projection.binding_owned_derived_type_owner_paths,
            expected_projection.binding_allocatable_holder_type_owner_paths,
            expected_projection.binding_pointer_holder_type_owner_paths,
        )
        if binding_inventories != expected_binding_inventories:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-binding-derived-support-inventory",
                    (expected_binding_inventories, binding_inventories),
                )
            )
        if plan.bridge is not None:
            bridge_inventories = (
                plan.bridge.allocatable_holder_type_owner_paths,
                plan.bridge.pointer_holder_type_owner_paths,
                plan.bridge.allocatable_holder_field_type_owner_paths,
                plan.bridge.pointer_holder_field_type_owner_paths,
            )
            expected_bridge_inventories = (
                expected_projection.bridge_allocatable_holder_type_owner_paths,
                expected_projection.bridge_pointer_holder_type_owner_paths,
                expected_projection.bridge_allocatable_holder_field_type_owner_paths,
                expected_projection.bridge_pointer_holder_field_type_owner_paths,
            )
            if bridge_inventories != expected_bridge_inventories:
                diagnostics.append(
                    self._diagnostic(
                        plan.owner_path,
                        "inconsistent-bridge-derived-support-inventory",
                        (expected_bridge_inventories, bridge_inventories),
                    )
                )
        expected_by_key = {operation.key: operation for operation in expected}
        actual_by_key = {operation.key: operation for operation in operations}
        if expected_by_key.keys() != actual_by_key.keys():
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "incomplete-auxiliary-entrypoint-inventory",
                    (tuple(expected_by_key), tuple(actual_by_key)),
                )
            )
        for callback in (
            argument.callback
            for namespace in plan.namespaces
            for function in namespace.functions
            for argument in function.arguments
            if argument.callback is not None
        ):
            operation = actual_by_key.get(callback.entrypoint.support_procedure.key)
            if operation is not callback.entrypoint.support_procedure:
                diagnostics.append(
                    self._diagnostic(
                        callback.owner_path,
                        "unshared-callback-entrypoint-operation",
                        callback.entrypoint.support_procedure.key,
                    )
                )
        return tuple(diagnostics)

    def _generated_support_procedure_diagnostics(
        self,
        operation: GeneratedSupportProcedureEntrypointPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one operation key, implementation owner, and structured signature."""
        diagnostics = []
        if operation.key != f"{operation.owner_path}::{operation.role}":
            diagnostics.append(
                self._diagnostic(operation.owner_path, "invalid-auxiliary-entrypoint-key", operation.key)
            )
        if not operation.symbol_name or not operation.symbol_name.isidentifier():
            diagnostics.append(
                self._diagnostic(
                    operation.owner_path,
                    "invalid-auxiliary-entrypoint-symbol",
                    operation.symbol_name,
                )
            )
        if operation.implementation_owner not in tuple(GeneratedSupportProcedureImplementationOwner):
            diagnostics.append(
                self._diagnostic(
                    operation.owner_path,
                    "invalid-auxiliary-entrypoint-implementation",
                    operation.implementation_owner,
                )
            )
        values = (*operation.signature.parameters, operation.signature.result)
        if any(
            not value.role
            or not value.c_name
            or not value.c_name.isidentifier()
            or not value.fortran_name
            or not value.fortran_name.isidentifier()
            or value.pointer_depth < 0
            for value in values
        ):
            diagnostics.append(
                self._diagnostic(operation.owner_path, "invalid-auxiliary-entrypoint-signature", operation.key)
            )
        return tuple(diagnostics)

    def _required_header_diagnostics(self, plan: ModulePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require module headers to equal the completed handle-plan union."""
        handles = tuple(
            handle
            for namespace in plan.namespaces
            for handle in self._namespace_native_array_handles(namespace)
            if handle is not None
        )
        expected_headers = list(self._native_array_required_headers(handles))
        if any(
            field.access
            in {
                DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR,
                DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE,
            }
            for namespace in plan.namespaces
            for derived in namespace.derived_types
            for field in derived.fields
        ):
            expected_headers.append(NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER)
        expected = tuple(dict.fromkeys(expected_headers))
        if plan.required_headers == expected:
            return ()
        return (self._diagnostic(plan.owner_path, "inconsistent-required-headers", plan.required_headers),)

    def _namespace_native_array_handles(
        self,
        namespace: NamespacePlan,
    ) -> tuple[NativeArrayHandlePlan | None, ...]:
        """Return every datatype-varying native handle in one namespace."""
        return (
            *(argument.native_array_handle for function in namespace.functions for argument in function.arguments),
            *(result.native_array_handle for function in namespace.functions for result in function.results),
            *(variable.native_array_handle for variable in namespace.variables),
            *(field.native_array_handle for derived in namespace.derived_types for field in derived.fields),
        )

    def _native_array_required_headers(self, handles: tuple[NativeArrayHandlePlan, ...]) -> tuple[str, ...]:
        """Return stable deduplicated headers selected by handle plans."""
        return tuple(dict.fromkeys(header for handle in handles for header in handle.required_headers))

    def _namespace_tree_diagnostics(self, plan: ModulePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return root, ancestor, owner, and duplicate-path diagnostics."""
        paths = [namespace.python_path for namespace in plan.namespaces]
        counts = Counter(paths)
        diagnostics = []
        if () not in counts:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-root-namespace", ()))
        diagnostics.extend(
            self._diagnostic(plan.owner_path, "duplicate-namespace-path", path)
            for path, occurrences in counts.items()
            if occurrences > 1
        )
        path_set = set(paths)
        for namespace in plan.namespaces:
            diagnostics.extend(self._namespace_path_diagnostics(plan, namespace, path_set))
        return tuple(diagnostics)

    def _namespace_path_diagnostics(
        self,
        module: ModulePlan,
        namespace: NamespacePlan,
        paths: set[tuple[str, ...]],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return owner, parent, and identifier diagnostics for one path."""
        diagnostics = []
        expected_owner = ".".join((module.owner_path, *namespace.python_path))
        if namespace.owner_path != expected_owner:
            diagnostics.append(self._diagnostic(namespace.owner_path, "inconsistent-namespace-owner", expected_owner))
        if namespace.python_path and namespace.python_path[:-1] not in paths:
            diagnostics.append(
                self._diagnostic(namespace.owner_path, "missing-parent-namespace", namespace.python_path[:-1])
            )
        diagnostics.extend(
            self._diagnostic(namespace.owner_path, "invalid-namespace-name", part)
            for part in namespace.python_path
            if not part.isidentifier()
        )
        return tuple(diagnostics)

    def _namespace_diagnostics(self, plan: NamespacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject ambiguous Python exports within one namespace."""
        return (
            *self._python_export_name_diagnostics(plan),
            *self._export_owner_diagnostics(plan),
            *self._derived_type_diagnostics(plan),
        )

    # Namespace, class, derived-type, and module-variable diagnostics.
    # Class validation keeps construction and method references mechanical.
    def _class_surface_diagnostics(
        self,
        namespace: NamespacePlan,
        surface: ClassSurfacePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one class against its referenced type and function plans."""
        functions = {id(function) for function in namespace.functions}
        return (
            *self._class_identity_diagnostics(namespace, surface),
            *self._class_method_reference_diagnostics(surface, functions),
            *(
                diagnostic
                for overload in surface.overloads
                for diagnostic in self._overload_diagnostics(overload, functions)
            ),
            *self._constructor_diagnostics(surface),
            *self._constructor_reference_diagnostics(surface, functions),
        )

    def _class_identity_diagnostics(
        self,
        namespace: NamespacePlan,
        surface: ClassSurfacePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one matching Phase 8 type and identical Python exports."""
        derived = tuple(item for item in namespace.derived_types if item.type_identity == surface.type_identity)
        if len(derived) != 1:
            return (
                self._diagnostic(surface.owner_path, "invalid-class-derived-type-reference", surface.type_identity),
            )
        if surface.python_names != derived[0].python_names:
            return (self._diagnostic(surface.owner_path, "inconsistent-class-python-exports", surface.python_names),)
        return ()

    def _class_method_reference_diagnostics(
        self,
        surface: ClassSurfacePlan,
        functions: set[int],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require every class method to reuse a namespace function plan."""
        return tuple(
            self._diagnostic(method.owner_path, "missing-class-method-function", method.function.owner_path)
            for method in surface.methods
            if id(method.function) not in functions
        )

    def _constructor_reference_diagnostics(
        self,
        surface: ClassSurfacePlan,
        functions: set[int],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the constructor's optional direct or overload target graph."""
        diagnostics = []
        constructor = surface.constructor
        if constructor.target is not None and id(constructor.target) not in functions:
            diagnostics.append(
                self._diagnostic(surface.owner_path, "missing-constructor-target", constructor.target.owner_path)
            )
        if constructor.overload is not None:
            diagnostics.extend(self._overload_diagnostics(constructor.overload, functions))
        return tuple(diagnostics)

    def _overload_diagnostics(
        self,
        overload: OverloadPlan,
        functions: set[int],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate candidate references and exact runtime signatures once."""
        missing = tuple(
            self._diagnostic(overload.owner_path, "missing-overload-candidate", candidate.owner_path)
            for candidate in overload.candidates
            if id(candidate) not in functions
        )
        return (
            *self._overload_cardinality_diagnostics(overload),
            *missing,
            *self._overload_signature_diagnostics(overload),
        )

    def _overload_cardinality_diagnostics(
        self,
        overload: OverloadPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one match and passed-object record per overload candidate."""
        diagnostics = []
        if not overload.candidates:
            diagnostics.append(self._diagnostic(overload.owner_path, "empty-overload", overload.python_name))
        expected = len(overload.candidates)
        for actual, code in (
            (len(overload.candidate_ids), "incomplete-overload-candidate-ids"),
            (len(overload.candidate_matches), "incomplete-overload-match-plan"),
            (len(overload.candidate_passed_objects), "incomplete-overload-call-plan"),
        ):
            if actual != expected:
                diagnostics.append(self._diagnostic(overload.owner_path, code, (expected, actual)))
        if len(set(overload.candidate_ids)) != len(overload.candidate_ids):
            diagnostics.append(
                self._diagnostic(overload.owner_path, "duplicate-overload-candidate-id", overload.python_name)
            )
        if any(
            type(candidate_id) is not int or not 0 <= candidate_id <= 2_147_483_647
            for candidate_id in overload.candidate_ids
        ):
            diagnostics.append(
                self._diagnostic(overload.owner_path, "invalid-overload-candidate-id", overload.candidate_ids)
            )
        return tuple(diagnostics)

    def _overload_signature_diagnostics(
        self,
        overload: OverloadPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject ambiguous predicates and inconsistent receiver selection."""
        diagnostics = []
        signatures = tuple(self._overload_signature(matches) for matches in overload.candidate_matches)
        if len(set(signatures)) != len(signatures):
            diagnostics.append(self._diagnostic(overload.owner_path, "ambiguous-overload", overload.python_name))
        builtin_signatures = tuple(self._overload_builtin_signature(matches) for matches in overload.candidate_matches)
        if len(set(builtin_signatures)) != len(builtin_signatures):
            diagnostics.append(
                self._diagnostic(overload.owner_path, "overlapping-reflected-overload", overload.python_name)
            )
        if len(set(overload.candidate_passed_objects)) > 1:
            diagnostics.append(self._diagnostic(overload.owner_path, "mixed-overload-receivers", overload.python_name))
        return tuple(diagnostics)

    @staticmethod
    def _overload_signature(matches: tuple) -> tuple:
        """Return the runtime-relevant signature of one overload candidate."""
        return tuple(
            (
                match.kind,
                match.optional,
                match.semantic_type_name,
                match.rank,
                match.derived_type_identity,
            )
            for match in matches
        )

    @staticmethod
    def _overload_builtin_signature(matches: tuple) -> tuple:
        """Normalize reflected Python scalar domains for overlap validation."""
        return tuple(
            (
                match.kind,
                match.optional,
                match.builtin_scalar_family or match.semantic_type_name,
                match.rank,
                match.derived_type_identity,
            )
            for match in matches
        )

    def _constructor_diagnostics(self, surface: ClassSurfacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one complete constructor kind and its exact lifecycle."""
        constructor = surface.constructor
        if constructor.kind is ClassConstructorKind.ABSENT:
            return self._absent_constructor_diagnostics(surface)
        if constructor.lifecycle != self._expected_constructor_lifecycle():
            return (self._diagnostic(surface.owner_path, "invalid-constructor-lifecycle", constructor.lifecycle),)
        return self._constructor_kind_diagnostics(surface)

    @staticmethod
    def _expected_constructor_lifecycle() -> tuple[ConstructionLifecycleAction, ...]:
        """Return the one balanced lifecycle shared by all owning constructors."""
        return (
            ConstructionLifecycleAction.ALLOCATE,
            ConstructionLifecycleAction.INITIALIZE,
            ConstructionLifecycleAction.COMMIT_OWNER,
            ConstructionLifecycleAction.CLEANUP_UNCOMMITTED,
            ConstructionLifecycleAction.DESTROY_OWNED,
        )

    def _absent_constructor_diagnostics(self, surface: ClassSurfacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require nonconstructible classes to carry only an explicit rejection."""
        constructor = surface.constructor
        if constructor.lifecycle or not constructor.rejection_message:
            return (self._diagnostic(surface.owner_path, "invalid-absent-constructor", constructor),)
        return ()

    def _constructor_kind_diagnostics(self, surface: ClassSurfacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate only the target facet selected by the completed kind."""
        constructor = surface.constructor
        if constructor.kind is ClassConstructorKind.DEFAULT_FIELDS and (
            constructor.target_owner_path is not None
            or constructor.overload_name is not None
            or constructor.target is not None
            or constructor.overload is not None
        ):
            return (self._diagnostic(surface.owner_path, "mixed-default-constructor", constructor),)
        if constructor.kind is ClassConstructorKind.BOUND_PROCEDURE and constructor.target is None:
            return (self._diagnostic(surface.owner_path, "missing-bound-constructor-target", constructor),)
        if constructor.kind is ClassConstructorKind.OVERLOAD_SET and constructor.overload is None:
            return (self._diagnostic(surface.owner_path, "missing-constructor-overload", constructor),)
        return ()

    def _class_graph_diagnostics(self, plan: ModulePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require every base class to exist before its derived class."""
        seen = set()
        diagnostics = []
        for namespace in plan.namespaces:
            for surface in namespace.classes:
                diagnostics.extend(
                    self._diagnostic(surface.owner_path, "missing-or-late-class-base", base)
                    for base in surface.base_identities
                    if base not in seen
                )
                if surface.type_identity in seen:
                    diagnostics.append(
                        self._diagnostic(surface.owner_path, "duplicate-class-type-identity", surface.type_identity)
                    )
                seen.add(surface.type_identity)
        return tuple(diagnostics)

    # Derived-type definition, field, and module validation.
    def _derived_type_diagnostics(self, plan: NamespacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate namespace-owned opaque type and field identities."""
        return (
            *self._duplicate_derived_type_diagnostics(plan),
            *(item for derived in plan.derived_types for item in self._one_derived_type_diagnostics(derived)),
        )

    def _duplicate_derived_type_diagnostics(self, plan: NamespacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject duplicate exported derived runtime names."""
        counts = Counter(name for derived in plan.derived_types for name in derived.python_names)
        return tuple(
            self._diagnostic(plan.owner_path, "duplicate-derived-python-name", name)
            for name, count in counts.items()
            if count > 1
        )

    def _one_derived_type_diagnostics(self, derived) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate identity and unique fields for one derived type."""
        identity = (
            (self._diagnostic(derived.owner_path, "incomplete-derived-type-identity", derived),)
            if (
                not derived.type_name
                or not derived.native_type_name
                or not derived.native_scope
                or derived.type_identity != (derived.native_scope, derived.native_type_name)
            )
            else ()
        )
        field_counts = Counter(field.name for field in derived.fields)
        duplicate_fields = tuple(
            self._diagnostic(derived.owner_path, "duplicate-derived-field", name)
            for name, count in field_counts.items()
            if count > 1
        )
        field_diagnostics = tuple(
            diagnostic for field in derived.fields for diagnostic in self._derived_field_diagnostics(field)
        )
        return (*identity, *duplicate_fields, *field_diagnostics)

    def _derived_field_diagnostics(self, field) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one typed field handoff before either backend emits it."""
        diagnostics = []
        if not field.owner_path or not field.name or not field.native_name or not field.getter_role:
            diagnostics.append(self._diagnostic(field.owner_path, "incomplete-derived-field-identity", field))
        expected_retention = (
            DerivedOwnerRetention.PARENT_WRAPPER
            if field.access
            in {
                DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR,
                DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE,
                DerivedFieldAccessMechanism.NESTED_OBJECT,
            }
            else DerivedOwnerRetention.NONE
        )
        if field.owner_retention is not expected_retention:
            diagnostics.append(
                self._diagnostic(field.owner_path, "invalid-derived-field-owner-retention", field.owner_retention)
            )
        diagnostics.extend(self._derived_field_setter_diagnostics(field))
        diagnostics.extend(self._derived_field_family_diagnostics(field))
        return tuple(diagnostics)

    def _derived_field_setter_diagnostics(self, field) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate Python setter exposure against the native assignment role."""
        if field.setter_action is SetterAction.WRITE_THROUGH:
            diagnostics = []
            if field.setter_role is None:
                diagnostics.append(self._diagnostic(field.owner_path, "missing-derived-field-setter-role", None))
            if field.native_assignment not in {AssignmentMode.VALUE_COPY, AssignmentMode.ALIAS}:
                diagnostics.append(
                    self._diagnostic(field.owner_path, "invalid-derived-field-assignment", field.native_assignment)
                )
            return tuple(diagnostics)
        if field.setter_role is not None:
            return (self._diagnostic(field.owner_path, "unexpected-derived-field-setter-role", field.setter_role),)
        return ()

    def _derived_field_family_diagnostics(self, field) -> tuple[WrapperPlanDiagnostic, ...]:
        """Dispatch field-facet consistency from its completed object kind."""
        match field.object_kind:
            case ObjectKind.SCALAR:
                valid = self._valid_scalar_derived_field(field)
            case ObjectKind.STRING:
                valid = self._valid_string_derived_field(field)
            case ObjectKind.NUMPY_ARRAY:
                valid = self._valid_array_derived_field(field)
            case ObjectKind.DERIVED_TYPE:
                valid = self._valid_nested_derived_field(field)
            case _:
                valid = False
        if not valid:
            return (self._diagnostic(field.owner_path, "inconsistent-derived-field-family", field.object_kind),)
        if field.native_array_handle is None:
            return ()
        return tuple(self._native_array_handle_shape_diagnostics(field.owner_path, field.native_array_handle))

    @staticmethod
    def _valid_scalar_derived_field(field) -> bool:
        """Return whether one field is the completed scalar-value field variant.

        The helper reads only the field's planned access, action, and rank.  A
        false result lets the caller report the field's existing object-kind
        mismatch without choosing a replacement representation.
        """
        return (
            field.access is DerivedFieldAccessMechanism.SCALAR_VALUE
            and field.getter_action is CodegenAction.DIRECT_VALUE
            and field.rank == 0
        )

    @staticmethod
    def _valid_string_derived_field(field) -> bool:
        """Return whether one field is the completed fixed-string copy variant.

        A valid string field has scalar rank, a positive fixed length, and the
        precise access and copy-out action already selected by policy.
        """
        return (
            field.access is DerivedFieldAccessMechanism.FIXED_STRING_COPY
            and field.getter_action is CodegenAction.COPY_OUT
            and field.rank == 0
            and field.character_length is not None
            and field.character_length > 0
        )

    @staticmethod
    def _valid_array_derived_field(field) -> bool:
        """Return whether one field uses its selected ordinary-array mechanism.

        Native-handle fields require the handle access mechanism; other array
        fields require the ordinary descriptor mechanism.  Both retain the
        planned borrowed-view action and array facet.
        """
        expected_access = (
            DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE
            if field.native_array_handle is not None
            else DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR
        )
        return (
            field.access is expected_access
            and field.getter_action is CodegenAction.BORROWED_VIEW
            and field.array is not None
        )

    @staticmethod
    def _valid_nested_derived_field(field) -> bool:
        """Return whether one field is a borrowed nested-derived-object view.

        The check preserves the completed parent-retention and reference
        handoff facts.  It does not resolve nested types or create ownership
        policy; callers turn a false result into one field diagnostic.
        """
        handoff = field.derived
        return bool(
            field.access is DerivedFieldAccessMechanism.NESTED_OBJECT
            and field.getter_action is CodegenAction.BORROWED_VIEW
            and field.rank == 0
            and handoff is not None
            and handoff.origin is DerivedObjectOrigin.BORROWED_FIELD
            and handoff.owner_retention is DerivedOwnerRetention.PARENT_WRAPPER
            and handoff.release is DerivedRelease.NONE
            and handoff.type_identity == (handoff.native_scope, handoff.native_type_name)
            and handoff.native_handoff is DerivedNativeHandoff.REFERENCE
        )

    def _python_export_name_diagnostics(self, plan: NamespacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return duplicate local export-name diagnostics."""
        names = [function.binding.python_name for function in plan.functions]
        names.extend(name for variable in plan.variables for name in variable.binding.python_names)
        names.extend(name for derived in plan.derived_types for name in derived.python_names)
        names.extend(overload.python_name for overload in plan.overloads)
        return tuple(
            self._diagnostic(plan.owner_path, "duplicate-python-export", name)
            for name, count in Counter(names).items()
            if count > 1
        )

    def _export_owner_diagnostics(self, plan: NamespacePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return exported child-owner diagnostics."""
        diagnostics = []
        for function in plan.functions:
            expected_owner = f"{plan.owner_path}.{function.binding.python_name}"
            if function.owner_path != expected_owner:
                diagnostics.append(
                    self._diagnostic(function.owner_path, "inconsistent-function-export-owner", expected_owner)
                )
        for variable in plan.variables:
            if not variable.binding.python_names:
                continue
            expected_owner = f"{plan.owner_path}.{variable.binding.python_names[0]}"
            if variable.owner_path != expected_owner:
                diagnostics.append(
                    self._diagnostic(variable.owner_path, "inconsistent-variable-export-owner", expected_owner)
                )
        for overload in plan.overloads:
            expected_owner = f"{plan.owner_path}.{overload.python_name}"
            if overload.owner_path != expected_owner:
                diagnostics.append(
                    self._diagnostic(overload.owner_path, "inconsistent-overload-export-owner", expected_owner)
                )
        return tuple(diagnostics)

    def _generated_symbol_diagnostics(self, plan: ModulePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject missing or colliding C/Fortran symbol stems before lowering."""
        owners_by_symbol: dict[str, list[str]] = {}
        diagnostics = list(self._namespace_symbol_diagnostics(plan))
        for namespace in plan.namespaces:
            for item in (*namespace.functions, *namespace.variables):
                if not item.symbol_name or not item.symbol_name.isidentifier():
                    diagnostics.append(self._diagnostic(item.owner_path, "invalid-generated-symbol", item.symbol_name))
                    continue
                owners_by_symbol.setdefault(item.symbol_name.casefold(), []).append(item.owner_path)
        diagnostics.extend(
            self._diagnostic(plan.owner_path, "duplicate-generated-symbol", f"{symbol}:{','.join(owners)}")
            for symbol, owners in owners_by_symbol.items()
            if len(owners) > 1
        )
        return tuple(diagnostics)

    def _namespace_symbol_diagnostics(self, plan: ModulePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject namespace paths that collapse to one generated C symbol."""
        owners_by_symbol: dict[str, list[str]] = {}
        for namespace in plan.namespaces:
            symbol = "_".join(namespace.python_path).casefold() if namespace.python_path else "root"
            owners_by_symbol.setdefault(symbol, []).append(namespace.owner_path)
        return tuple(
            self._diagnostic(plan.owner_path, "duplicate-generated-namespace-symbol", f"{symbol}:{','.join(owners)}")
            for symbol, owners in owners_by_symbol.items()
            if len(owners) > 1
        )

    def _module_variable_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return getter, setter, and initialization consistency diagnostics."""
        diagnostics = []
        if not plan.binding.python_names:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-module-python-name", plan.owner_path))
        diagnostics.extend(self._module_variable_entrypoint_diagnostics(plan))
        diagnostics.extend(self._module_getter_diagnostics(plan))
        if plan.binding.getter_action is ModuleGetterAction.DERIVED_OBJECT:
            diagnostics.extend(self._derived_module_object_diagnostics(plan))
        diagnostics.extend(self._module_setter_diagnostics(plan))
        if plan.binding.initializer is not None and plan.binding.setter_action is not SetterAction.WRITE_THROUGH:
            diagnostics.append(self._diagnostic(plan.owner_path, "initializer-without-native-setter", plan.owner_path))
        return tuple(diagnostics)

    def _module_variable_entrypoint_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate module-variable roles before support-procedure lookup."""
        diagnostics = []
        for label, role in (
            ("getter", plan.entrypoint.getter_role),
            ("setter", plan.entrypoint.setter_role),
        ):
            if role is not None and not role:
                diagnostics.append(self._diagnostic(plan.owner_path, f"invalid-module-{label}-role", role))
        return tuple(diagnostics)

    def _derived_module_object_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one live direct-address or typed-member module object."""
        derived = plan.derived
        if derived is None:
            return (self._diagnostic(plan.owner_path, "missing-derived-module-object", None),)
        handoff = derived.handoff
        expected = self._derived_module_expected_facts(plan)
        diagnostics = [
            self._diagnostic(plan.owner_path, f"invalid-derived-module-{name}", actual)
            for name, actual, required in expected
            if actual is not required
        ]
        if derived.access not in {
            ModuleObjectAccessMechanism.DIRECT_ADDRESS,
            ModuleObjectAccessMechanism.MEMBER_PROXY,
            ModuleObjectAccessMechanism.VALUE_COPY,
        }:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-module-access", derived.access))
        if (
            not handoff.type_name
            or not handoff.native_type_name
            or not handoff.native_scope
            or handoff.type_identity != (handoff.native_scope, handoff.native_type_name)
        ):
            diagnostics.append(self._diagnostic(plan.owner_path, "incomplete-derived-module-type", handoff))
        if plan.native_array_handle is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "derived-module-has-array-handle", None))
        diagnostics.extend(self._derived_module_member_path_diagnostics(plan))
        return tuple(diagnostics)

    @staticmethod
    def _derived_module_expected_facts(plan: ModuleVariablePlan) -> tuple[tuple[str, object, object], ...]:
        """Return origin/lifetime facts selected by the completed access mechanism."""
        derived = plan.derived
        handoff = derived.handoff
        if derived.access is ModuleObjectAccessMechanism.VALUE_COPY:
            return (
                ("family", plan.datatype_family, DatatypeFamily.DERIVED),
                ("origin", handoff.origin, DerivedObjectOrigin.CONSTANT_VALUE),
                ("owner-retention", handoff.owner_retention, DerivedOwnerRetention.WRAPPER_INSTANCE),
                ("release", handoff.release, DerivedRelease.WRAPPER_DESTROY),
                ("native-handoff", handoff.native_handoff, DerivedNativeHandoff.REFERENCE),
                ("replacement", derived.replacement, SetterAction.REJECT_REPLACEMENT),
            )
        return (
            ("family", plan.datatype_family, DatatypeFamily.DERIVED),
            ("origin", handoff.origin, DerivedObjectOrigin.NATIVE_MODULE),
            ("owner-retention", handoff.owner_retention, DerivedOwnerRetention.NATIVE_MODULE),
            ("release", handoff.release, DerivedRelease.NATIVE_OWNER),
            ("native-handoff", handoff.native_handoff, DerivedNativeHandoff.REFERENCE),
            ("replacement", derived.replacement, SetterAction.REJECT_REPLACEMENT),
        )

    def _derived_module_member_path_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate finite module-proxy operations and shared field records."""
        derived = plan.derived
        if derived is None:
            return ()
        if derived.access is ModuleObjectAccessMechanism.VALUE_COPY:
            return ()
        if not derived.member_paths:
            return (self._diagnostic(plan.owner_path, "missing-derived-module-member-paths", None),)
        counts = Counter(member.path for member in derived.member_paths)
        diagnostics = [
            self._diagnostic(plan.owner_path, "duplicate-derived-module-member-path", ".".join(path))
            for path, count in counts.items()
            if count > 1
        ]
        diagnostics.extend(
            self._diagnostic(plan.owner_path, "incomplete-derived-module-member-path", member)
            for member in derived.member_paths
            if self._invalid_derived_member_path(member)
        )
        return tuple(diagnostics)

    @staticmethod
    def _invalid_derived_member_path(member) -> bool:
        """Return whether one finite path lacks matching native/type identity."""
        return bool(
            not member.path or len(member.path) != len(member.native_path) or not all(member.declaring_type_identity)
        )

    def _module_getter_diagnostics(self, plan: ModuleVariablePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return module getter handoff diagnostics."""
        action = plan.binding.getter_action
        if action is ModuleGetterAction.NATIVE_ARRAY_HANDLE:
            return self._module_native_array_handle_diagnostics(plan)
        if action is ModuleGetterAction.BORROWED_ARRAY_VIEW:
            return self._module_borrowed_array_view_diagnostics(plan)
        if action is ModuleGetterAction.CONSTANT_VALUE:
            return self._binding_constant_getter_diagnostics(plan)
        if action is ModuleGetterAction.NATIVE_CONSTANT_VALUE:
            return self._native_constant_getter_diagnostics(plan)
        if action is ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE:
            return self._native_constant_array_getter_diagnostics(plan)
        if action is ModuleGetterAction.DERIVED_OBJECT:
            return self._derived_module_getter_role_diagnostics(plan)
        if plan.entrypoint.getter_role is None:
            return (self._diagnostic(plan.owner_path, "missing-module-getter-role", action.value),)
        if action is ModuleGetterAction.NULLABLE_SNAPSHOT and plan.entrypoint.descriptor_kind not in {
            "allocatable",
            "pointer",
        }:
            return (self._diagnostic(plan.owner_path, "missing-module-descriptor-kind", action.value),)
        return ()

    def _binding_constant_getter_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one binding-materialized module constant."""
        diagnostics = []
        if plan.entrypoint.getter_role is not None:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "constant-has-bridge-getter", plan.entrypoint.getter_role)
            )
        if plan.binding.constant_value is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-module-constant-value", plan.owner_path))
        return tuple(diagnostics)

    def _native_constant_getter_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one compiler-evaluated module constant."""
        diagnostics = []
        if plan.entrypoint.getter_role is None:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "missing-module-getter-role",
                    plan.binding.getter_action.value,
                )
            )
        if plan.binding.constant_value is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "native-constant-has-binding-value", plan.owner_path))
        return tuple(diagnostics)

    def _native_constant_array_getter_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one compiler-evaluated immutable parameter-array snapshot."""
        diagnostics = []
        if plan.array is None or plan.array.rank is None or plan.array.rank <= 0:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-module-constant-array", plan.array))
        if plan.entrypoint.getter_role is None:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "missing-module-getter-role",
                    plan.binding.getter_action.value,
                )
            )
        if plan.binding.constant_value is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "native-constant-has-binding-value", plan.owner_path))
        return tuple(diagnostics)

    def _module_borrowed_array_view_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one native-owned fixed array view and its pointer/shape ABI."""
        diagnostics = []
        array = plan.array
        if array is None or array.rank is None or array.rank <= 0:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-module-array-view", array))
        if plan.native_array_handle is not None or plan.derived is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "module-array-view-has-unrelated-facet", None))
        if plan.entrypoint.getter_role is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-module-array-getter-role", None))
        if plan.bridge.native_assignment is not AssignmentMode.NONE:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path, "module-array-view-has-native-assignment", plan.bridge.native_assignment
                )
            )
        return tuple(diagnostics)

    def _derived_module_getter_role_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate whole-address roles only on the completed direct mechanism."""
        derived = plan.derived
        if derived is None:
            return ()
        if derived.access in {
            ModuleObjectAccessMechanism.DIRECT_ADDRESS,
            ModuleObjectAccessMechanism.VALUE_COPY,
        }:
            if plan.entrypoint.getter_role is None:
                return (self._diagnostic(plan.owner_path, "missing-derived-module-getter-role", None),)
            return ()
        if plan.entrypoint.getter_role is not None:
            return (
                self._diagnostic(
                    plan.owner_path, "module-proxy-fabricates-whole-address-role", plan.entrypoint.getter_role
                ),
            )
        return ()

    def _module_native_array_handle_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one stable borrowed module descriptor handle."""
        handle = plan.native_array_handle
        if handle is None:
            return (self._diagnostic(plan.owner_path, "missing-module-native-array-handle", None),)
        expected = (
            ("kind", handle.handle_kind, NativeArrayHandleKind.BORROWED_MODULE_DESCRIPTOR),
            ("origin", handle.origin, NativeArrayHandleOrigin.MODULE_VARIABLE),
            ("owner-retention", handle.owner_retention, NativeArrayOwnerRetention.NATIVE_MODULE),
            ("descriptor-ownership", handle.descriptor_ownership, NativeArrayDescriptorOwnership.BORROWED),
            ("output-projection", handle.output_projection, NativeArrayOutputProjection.NONE),
            ("release", handle.release, NativeArrayRelease.NATIVE_OWNER),
            ("destroy", handle.destroy_behavior, NativeArrayDestroyBehavior.NONE),
        )
        diagnostics = [
            self._diagnostic(plan.owner_path, f"invalid-module-handle-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        ]
        if not handle.borrowed:
            diagnostics.append(self._diagnostic(plan.owner_path, "module-handle-not-borrowed", handle.borrowed))
        if plan.binding.setter_action is not SetterAction.REJECT_REPLACEMENT:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "module-handle-replacement-not-rejected", plan.binding.setter_action)
            )
        diagnostics.extend(self._native_array_handle_shape_diagnostics(plan.owner_path, handle))
        diagnostics.extend(self._native_descriptor_handoff_diagnostics(plan.owner_path, handle, None))
        return tuple(diagnostics)

    def _module_setter_diagnostics(self, plan: ModuleVariablePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return module setter exposure and native-assignment diagnostics."""
        if plan.native_array_handle is not None:
            return self._module_handle_setter_diagnostics(plan)
        if plan.binding.setter_action is SetterAction.WRITE_THROUGH:
            return self._module_write_through_setter_diagnostics(plan)
        return self._module_nonwriting_setter_diagnostics(plan)

    def _module_handle_setter_diagnostics(self, plan: ModuleVariablePlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate stable module-handle replacement policy."""
        handle = plan.native_array_handle
        if handle is None:
            return ()
        diagnostics = []
        if plan.binding.setter_action is not handle.setter_action:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-module-handle-setter", plan.binding.setter_action)
            )
        if plan.bridge.native_assignment is not handle.native_assignment:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-module-handle-assignment",
                    plan.bridge.native_assignment,
                )
            )
        if plan.entrypoint.setter_role is not None:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "module-handle-has-replacement-role", plan.entrypoint.setter_role)
            )
        return tuple(diagnostics)

    def _module_write_through_setter_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one scalar module write-through setter."""
        diagnostics = []
        # A character write copies a byte buffer rather than a value, but it is
        # the same write-through contract; every other mechanism is rejected.
        if plan.bridge.native_assignment not in {AssignmentMode.VALUE_COPY, AssignmentMode.CHARACTER_COPY}:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-module-native-assignment", plan.bridge.native_assignment)
            )
        if plan.entrypoint.setter_role is None:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "missing-module-setter-role", plan.binding.setter_action.value)
            )
        return tuple(diagnostics)

    def _module_nonwriting_setter_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate an omitted or replacement-rejecting module setter."""
        diagnostics = []
        if plan.bridge.native_assignment is not AssignmentMode.NONE:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-module-native-assignment", plan.bridge.native_assignment)
            )
        if plan.entrypoint.setter_role is not None:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "setter-role-without-write-through", plan.entrypoint.setter_role)
            )
        diagnostics.extend(self._module_nonwriting_action_diagnostics(plan))
        return tuple(diagnostics)

    def _module_nonwriting_action_diagnostics(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate descriptor rejection and constant omission choices."""
        action = plan.binding.setter_action
        if action is SetterAction.REJECT_REPLACEMENT and (
            plan.derived is not None or plan.binding.getter_action is ModuleGetterAction.BORROWED_ARRAY_VIEW
        ):
            return ()
        if action is SetterAction.REJECT_REPLACEMENT and plan.entrypoint.descriptor_kind not in {
            "allocatable",
            "pointer",
        }:
            return (self._diagnostic(plan.owner_path, "rejected-module-setter-without-descriptor", action.value),)
        if action is SetterAction.OMIT and plan.binding.getter_action not in {
            ModuleGetterAction.CONSTANT_VALUE,
            ModuleGetterAction.NATIVE_CONSTANT_VALUE,
            ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE,
        }:
            return (self._diagnostic(plan.owner_path, "omitted-nonconstant-module-setter", action.value),)
        return ()

    # Function, declaration-callable, and argument diagnostics.
    def _function_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Collect one function's ordered graph and typed-transfer diagnostics.

        Function-wide ordering, role, output, invocation, and status checks
        run before individual slots, arguments, results, and lifecycle actions.
        This preserves diagnostic order and lets each typed helper validate the
        lowest record that contains its compared binding and bridge facts.
        """
        if plan.entrypoint.action is NativeEntrypointAction.DIRECT_C_ABI:
            return self._direct_function_diagnostics(plan)

        projected_slots = tuple(sorted(plan.entrypoint.projected_slots, key=lambda item: item.native_position))
        adapter_slots = self._adapter_slots(plan)
        # Check the function-wide producer/consumer graph before its individual records.
        diagnostics = [
            *self._entrypoint_diagnostics(plan),
            *self._sequence_diagnostics(
                plan.owner_path,
                "python",
                tuple(argument.python_position for argument in plan.arguments),
                len(plan.arguments),
            ),
            *self._sequence_diagnostics(
                plan.owner_path,
                "native",
                tuple(slot.native_position for slot in projected_slots),
                len(projected_slots),
            ),
            *self._duplicate_role_diagnostics(plan),
            *self._available_role_diagnostics(plan),
            *self._argument_update_diagnostics(plan),
            *self._binding_conversion_order_diagnostics(plan),
            *self._function_output_diagnostics(plan),
            *self._string_result_aggregation_diagnostics(plan),
            *self._status_error_diagnostics(plan),
            *self._class_call_diagnostics(plan),
            *self._native_invocation_diagnostics(plan),
        ]

        # Validate shared slots and their typed consumers in native/result order.
        slots = {slot.native_position: slot for slot in projected_slots}
        for slot in adapter_slots:
            diagnostics.extend(self._native_slot_diagnostics(slot))
        for argument in plan.arguments:
            diagnostics.extend(self._argument_diagnostics(argument, slots, plan.available_roles))
        for result in plan.results:
            diagnostics.extend(self._result_diagnostics(result, slots, plan.available_roles))
        for action in (*plan.writeback_actions, *plan.cleanup_actions, *plan.release_actions):
            diagnostics.extend(self._lifecycle_diagnostics(action, plan.available_roles))
        for declaration in plan.declaration_callables:
            diagnostics.extend(self._declaration_callable_diagnostics(declaration))

        # Validate function-wide lifecycle coverage after every producer is known.
        diagnostics.extend(self._writeback_phase_diagnostics(plan))
        diagnostics.extend(self._string_writeback_diagnostics(plan))
        return tuple(diagnostics)

    def _argument_update_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require every argument-update result to pair with a descriptor string input.

        The replaced value is read back from the adapter local its argument
        converts, so that pairing must exist and must be the completed
        allocatable or pointer character-buffer input.  A result without it
        would publish whichever storage the adapter happened to declare, which
        compiles and imports while returning the pre-call value.
        """
        arguments = {argument.owner_path: argument for argument in plan.arguments}
        diagnostics = []
        for result in plan.results:
            if not result.updates_argument:
                continue
            argument = arguments.get(result.owner_path)
            if argument is None:
                diagnostics.append(self._diagnostic(result.owner_path, "missing-update-result-argument", None))
                continue
            if not argument.projects_character_descriptor_update:
                diagnostics.append(
                    self._diagnostic(result.owner_path, "invalid-update-result-argument", argument.owner_path)
                )
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                diagnostics.append(
                    self._diagnostic(
                        result.owner_path,
                        "invalid-update-result-argument-handoff",
                        argument.entrypoint.handoff_mode.value,
                    )
                )
            if any(action.owner_path == result.owner_path for action in plan.writeback_actions):
                diagnostics.append(
                    self._diagnostic(result.owner_path, "unexpected-update-result-writeback", result.result_position)
                )
        return tuple(diagnostics)

    @staticmethod
    def _adapter_slots(plan: FunctionPlan) -> tuple[NativeEntrypointProjectedSlotPlan, ...]:
        """Return ordered projected slots that carry an adapter facet."""
        return tuple(
            slot
            for slot in sorted(plan.entrypoint.projected_slots, key=lambda item: item.native_position)
            if slot.adapter is not None
        )

    def _direct_function_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate a binding-to-native C ABI route without adapter assumptions."""
        slots = plan.entrypoint.projected_slots
        diagnostics = [
            *self._entrypoint_diagnostics(plan),
            *self._sequence_diagnostics(
                plan.owner_path,
                "python",
                tuple(argument.python_position for argument in plan.arguments),
                len(plan.arguments),
            ),
            *self._sequence_diagnostics(
                plan.owner_path,
                "native",
                tuple(slot.native_position for slot in slots),
                len(slots),
            ),
            *self._duplicate_role_diagnostics(plan),
            *self._available_role_diagnostics(plan),
            *self._binding_conversion_order_diagnostics(plan),
            *self._binding_result_diagnostics(plan),
        ]
        if plan.bridge is not None or self._adapter_slots(plan):
            diagnostics.append(self._diagnostic(plan.owner_path, "direct-route-has-fortran-adapter", plan.bridge))
        for slot in slots:
            if slot.adapter is not None:
                diagnostics.append(self._diagnostic(slot.owner_path, "direct-slot-has-adapter-facet", slot.adapter))
        indexed_slots = {slot.native_position: slot for slot in slots}
        for argument in plan.arguments:
            slot = argument.projected_call_slot
            if argument.bridge is not None or slot.adapter is not None:
                diagnostics.append(
                    self._diagnostic(argument.owner_path, "direct-argument-has-adapter-facet", argument.bridge)
                )
            if indexed_slots.get(argument.native_position) is not slot:
                diagnostics.append(
                    self._diagnostic(
                        argument.owner_path, "unregistered-direct-projected-slot", argument.native_position
                    )
                )
            expected_callback_parameter = argument.callback is not None
            if argument.entrypoint.pass_callback_parameter is not expected_callback_parameter:
                diagnostics.append(
                    self._diagnostic(
                        argument.owner_path,
                        "inconsistent-callback-entrypoint-parameter",
                        argument.entrypoint.pass_callback_parameter,
                    )
                )
            if argument.entrypoint.optionality is not slot.optionality:
                diagnostics.append(
                    self._diagnostic(
                        argument.owner_path,
                        "inconsistent-direct-optionality",
                        argument.entrypoint.optionality,
                    )
                )
        for result in plan.results:
            if result.bridge is not None or (
                result.projected_call_slot is not None and result.projected_call_slot.adapter is not None
            ):
                diagnostics.append(
                    self._diagnostic(result.owner_path, "direct-result-has-adapter-facet", result.bridge)
                )
        return tuple(diagnostics)

    def _entrypoint_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the complete shared C-ABI symbol and parameter-group index."""
        diagnostics = []
        if not plan.entrypoint.symbol_name or not plan.entrypoint.symbol_name.isidentifier():
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-native-entrypoint-symbol", plan.entrypoint.symbol_name)
            )
        parameters = tuple(sorted(plan.entrypoint.parameters, key=lambda item: item.position))
        diagnostics.extend(
            self._sequence_diagnostics(
                plan.owner_path,
                "entrypoint-parameter",
                tuple(parameter.position for parameter in parameters),
                len(parameters),
            )
        )
        expected = self._expected_entrypoint_parameter_groups(plan)
        actual = tuple((parameter.owner_path, parameter.source_kind) for parameter in parameters)
        if actual != expected:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-entrypoint-parameters", actual))
        diagnostics.extend(self._entrypoint_parameter_name_diagnostics(plan))
        diagnostics.extend(self._entrypoint_result_diagnostics(plan))
        return tuple(diagnostics)

    @staticmethod
    def _expected_entrypoint_parameter_groups(plan: FunctionPlan) -> tuple[tuple[str, str], ...]:
        """Return the C-ABI parameter groups required by completed transfer facts."""
        argument_owners = {argument.owner_path for argument in plan.arguments}
        updated_owners = {result.owner_path for result in plan.results if result.updates_argument}
        groups: list[tuple[str, str]] = []
        for slot in sorted(plan.entrypoint.projected_slots, key=lambda item: item.native_position):
            if slot.source_kind == "result":
                groups.append((slot.owner_path, "hidden_result"))
            elif slot.owner_path in argument_owners:
                groups.append((slot.owner_path, "argument"))
                if slot.owner_path in updated_owners:
                    groups.append((slot.owner_path, "hidden_result"))
            else:
                groups.append((slot.owner_path, "projected_slot"))
        groups.extend(
            (result.owner_path, "direct_result")
            for result in plan.results
            if result.source_kind == "direct_return"
            and (
                result.scalar_descriptor is not None
                or (
                    result.native_array_handle is not None
                    and result.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
                )
            )
        )
        groups.extend(
            (result.owner_path, "declaration_extent")
            for result in plan.results
            if result.array is not None and "bridge" in result.array.extent_evaluation
        )
        return tuple(groups)

    def _entrypoint_parameter_name_diagnostics(
        self,
        plan: FunctionPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require every C-visible argument and hidden result to have a valid name."""
        diagnostics = []
        for argument in plan.arguments:
            name = argument.entrypoint.parameter_name
            if not name or not name.isidentifier():
                diagnostics.append(self._diagnostic(argument.owner_path, "invalid-entrypoint-argument-name", name))
        for result in plan.entrypoint.results:
            name = result.parameter_name
            if result.source_kind == "hidden_output" and (not name or not name.isidentifier()):
                diagnostics.append(self._diagnostic(result.owner_path, "invalid-entrypoint-result-name", name))
        for slot in plan.entrypoint.projected_slots:
            if slot.owner_path in {argument.owner_path for argument in plan.arguments} or slot.source_kind == "result":
                continue
            if not slot.native_name or not slot.native_name.isidentifier():
                diagnostics.append(
                    self._diagnostic(slot.owner_path, "invalid-projected-entrypoint-name", slot.native_name)
                )
        return tuple(diagnostics)

    def _entrypoint_result_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate every direct and binding-private result at the shared C ABI."""
        diagnostics = []
        by_owner = {result.owner_path: result for result in plan.entrypoint.results}
        if len(by_owner) != len(plan.entrypoint.results):
            diagnostics.append(
                self._diagnostic(plan.owner_path, "duplicate-entrypoint-result-owner", plan.entrypoint.results)
            )
        for result in plan.results:
            if by_owner.get(result.owner_path) is not result.entrypoint:
                diagnostics.append(
                    self._diagnostic(result.owner_path, "unregistered-public-entrypoint-result", result.owner_path)
                )
        for slot in plan.entrypoint.projected_slots:
            if slot.source_kind != "result":
                continue
            result = by_owner.get(slot.owner_path)
            if result is None:
                diagnostics.append(
                    self._diagnostic(slot.owner_path, "missing-hidden-entrypoint-result", slot.owner_path)
                )
                continue
            expected = (
                slot.symbolic_role,
                slot.semantic_type_name,
                slot.datatype_family,
                slot.object_kind,
                slot.character_length,
                slot.array,
                slot.native_array_handle,
                slot.scalar_descriptor,
            )
            actual = (
                result.native_result_role,
                result.semantic_type_name,
                result.datatype_family,
                result.object_kind,
                result.character_length,
                result.array,
                result.native_array_handle,
                result.scalar_descriptor,
            )
            if actual != expected:
                diagnostics.append(self._diagnostic(slot.owner_path, "inconsistent-hidden-entrypoint-result", actual))
        expected_owners = {
            *(slot.owner_path for slot in plan.entrypoint.projected_slots if slot.source_kind == "result"),
            *(result.owner_path for result in plan.results if result.source_kind == "direct_return"),
            *(result.owner_path for result in plan.results if result.updates_argument),
        }
        extra = tuple(
            result.owner_path for result in plan.entrypoint.results if result.owner_path not in expected_owners
        )
        if extra:
            diagnostics.append(self._diagnostic(plan.owner_path, "unexpected-entrypoint-results", extra))
        return tuple(diagnostics)

    def _binding_conversion_order_diagnostics(
        self,
        plan: FunctionPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require complete dependency-safe binding conversion ownership."""
        order = plan.binding.argument_conversion_order
        owners = tuple(argument.owner_path for argument in plan.arguments)
        diagnostics = []
        if Counter(order) != Counter(owners):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-binding-conversion-order", order))
            return tuple(diagnostics)

        positions = {owner: position for position, owner in enumerate(order)}
        role_owners = {argument.entrypoint.handoff_role: argument.owner_path for argument in plan.arguments}
        role_owners.update(
            {
                role: argument.owner_path
                for argument in plan.arguments
                if argument.array is not None
                for role in argument.array.extent_roles
            }
        )
        diagnostics.extend(self._late_binding_extent_conversion_diagnostics(plan, positions, role_owners))
        return tuple(diagnostics)

    def _declaration_callable_diagnostics(
        self,
        declaration: DeclarationCallablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one already-selected declaration-function lowering action."""
        diagnostics = []
        if not declaration.symbolic_role or not declaration.expression_token or not declaration.backend_symbol:
            diagnostics.append(
                self._diagnostic(declaration.owner_path, "incomplete-declaration-callable-role", declaration)
            )
        if declaration.action is DeclarationCallableAction.MODULE_IMPORT:
            diagnostics.extend(self._module_declaration_callable_diagnostics(declaration))
            return tuple(diagnostics)
        if declaration.action is DeclarationCallableAction.STANDALONE_PROCEDURE:
            diagnostics.extend(self._standalone_declaration_callable_diagnostics(declaration))
            return tuple(diagnostics)
        diagnostics.append(
            self._diagnostic(declaration.owner_path, "unknown-declaration-callable-action", declaration.action)
        )
        return tuple(diagnostics)

    def _module_declaration_callable_diagnostics(
        self,
        declaration: DeclarationCallablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate a completed module-import declaration dependency."""
        diagnostics = []
        if declaration.native_scope is None:
            diagnostics.append(
                self._diagnostic(declaration.owner_path, "module-declaration-callable-missing-scope", None)
            )
        if declaration.prototype is not None:
            diagnostics.append(
                self._diagnostic(declaration.owner_path, "module-declaration-callable-has-prototype", None)
            )
        return tuple(diagnostics)

    def _standalone_declaration_callable_diagnostics(
        self,
        declaration: DeclarationCallablePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate a completed standalone-procedure declaration dependency."""
        diagnostics = []
        if declaration.native_scope is not None:
            diagnostics.append(
                self._diagnostic(
                    declaration.owner_path,
                    "standalone-declaration-callable-has-scope",
                    declaration.native_scope,
                )
            )
        prototype = declaration.prototype
        if prototype is None or not prototype.pure or prototype.result is None:
            diagnostics.append(
                self._diagnostic(
                    declaration.owner_path,
                    "incomplete-standalone-declaration-callable-prototype",
                    declaration.native_name,
                )
            )
        else:
            diagnostics.extend(self._procedure_prototype_diagnostics(prototype))
        return tuple(diagnostics)

    def _procedure_prototype_diagnostics(
        self,
        prototype: ProcedurePrototypePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the shared signature and generated abstract-interface symbol."""
        diagnostics = []
        symbol = prototype.interface_symbol
        if not symbol or not symbol.isidentifier() or not symbol.casefold().startswith("prik_"):
            diagnostics.append(self._diagnostic(prototype.owner_path, "invalid-prototype-interface-symbol", symbol))
        if not prototype.name or not prototype.identity:
            diagnostics.append(self._diagnostic(prototype.owner_path, "incomplete-prototype-identity", prototype.name))
        if any(not argument.owner_path or not argument.name for argument in prototype.arguments):
            diagnostics.append(
                self._diagnostic(prototype.owner_path, "incomplete-prototype-arguments", prototype.arguments)
            )
        return tuple(diagnostics)

    def _late_binding_extent_conversion_diagnostics(
        self,
        plan: FunctionPlan,
        positions: dict[str, int],
        role_owners: dict[str, str],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject a planned array conversion scheduled before a used extent."""
        diagnostics = []
        for argument in plan.arguments:
            for dependency in self._binding_extent_dependency_owners(argument, role_owners):
                if dependency != argument.owner_path and positions[dependency] > positions[argument.owner_path]:
                    diagnostics.append(
                        self._diagnostic(
                            argument.owner_path,
                            "late-binding-extent-conversion",
                            dependency,
                        )
                    )
        return tuple(diagnostics)

    @staticmethod
    def _binding_extent_dependency_owners(
        argument: ArgumentTransferPlan,
        role_owners: dict[str, str],
    ) -> tuple[str, ...]:
        """Return planned owners referenced by one array's extent roles."""
        if argument.array is None:
            return ()
        return tuple(
            role_owners[role]
            for axis_roles in argument.array.extent_reference_roles
            for role in axis_roles
            if role in role_owners
        )

    def _native_invocation_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one internally consistent completed native call syntax."""
        invocation = plan.bridge.native_invocation
        validator = {
            NativeInvocationKind.PROCEDURE: self._procedure_invocation_diagnostics,
            NativeInvocationKind.DEFINED_OPERATOR: self._defined_operator_diagnostics,
            NativeInvocationKind.DEFINED_ASSIGNMENT: self._defined_assignment_diagnostics,
        }.get(invocation)
        if validator is None:
            return (self._diagnostic(plan.owner_path, "unknown-native-invocation", invocation),)
        return validator(plan)

    def _procedure_invocation_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject an operator token on an ordinary procedure call."""
        operator = plan.bridge.native_operator
        if operator is None:
            return ()
        return (self._diagnostic(plan.owner_path, "unexpected-native-operator", operator),)

    def _defined_operator_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the canonical native spelling for a defined operator."""
        operator = plan.bridge.native_operator
        expected = f"operator({operator})" if operator else None
        compact_name = "".join(plan.bridge.native_name.split()).casefold()
        if expected is not None and compact_name == expected:
            return ()
        return (self._diagnostic(plan.owner_path, "invalid-defined-operator", plan.bridge),)

    def _defined_assignment_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require subroutine form and canonical spelling for defined assignment."""
        compact_name = "".join(plan.bridge.native_name.split()).casefold()
        valid = (
            compact_name == "assignment(=)" and plan.bridge.native_operator == "=" and plan.bridge.native_is_subroutine
        )
        if valid:
            return ()
        return (self._diagnostic(plan.owner_path, "invalid-defined-assignment", plan.bridge),)

    def _class_call_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate receiver selection before either backend sees a class call."""
        call = plan.class_call
        if call is None:
            return ()
        positions = {argument.native_position for argument in plan.arguments}
        if call.passed_object_position is not None and call.passed_object_position not in positions:
            return (
                self._diagnostic(
                    plan.owner_path,
                    "missing-class-passed-object",
                    call.passed_object_position,
                ),
            )
        if call.invocation is ClassInvocationKind.TYPE_BOUND:
            if call.passed_object_position is None or not call.type_bound_name:
                return (self._diagnostic(plan.owner_path, "incomplete-type-bound-call", call),)
        elif call.type_bound_name is not None:
            return (self._diagnostic(plan.owner_path, "unexpected-type-bound-name", call.type_bound_name),)
        return ()

    def _argument_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        function_slots: dict[int, NativeEntrypointProjectedSlotPlan],
        available_roles: tuple[str, ...],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return binding-to-entrypoint handoff and bridge-call-slot diagnostics."""
        diagnostics = [
            *self._argument_policy_consistency_diagnostics(plan),
            *self._argument_slot_consistency_diagnostics(plan, function_slots),
            *self._optional_argument_diagnostics(plan),
            *self._argument_family_diagnostics(plan, available_roles),
            *self._argument_transformation_diagnostics(plan),
            *self._array_writeback_abi_diagnostics(plan),
            *self._argument_data_action_diagnostics(plan),
            *self._bridge_data_diagnostics(
                plan.owner_path,
                plan.bridge.data_action,
                plan.bridge.copy_reason,
            ),
        ]
        return tuple(diagnostics)

    def _array_writeback_abi_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed mutable-array normalization without selecting it."""
        expected = ArrayWritebackABI.NOT_APPLICABLE
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER and (
            plan.mutates_native or self._publishes_array_replacement(plan)
        ):
            if plan.array_logical_abi is ArrayLogicalABI.NATIVE_KIND_COPY:
                expected = ArrayWritebackABI.NOT_APPLICABLE
            elif plan.datatype_family is DatatypeFamily.BOOL:
                expected = ArrayWritebackABI.LOGICAL_LOW_BIT_INT8
            else:
                expected = ArrayWritebackABI.NATIVE_ARRAY
        if plan.array_writeback_abi is expected:
            return ()
        return (
            self._diagnostic(
                plan.owner_path,
                "invalid-array-writeback-abi",
                f"{plan.array_writeback_abi.value}; expected {expected.value}",
            ),
        )

    # Layer-owned representation transformation validation.
    def _argument_transformation_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate layer ownership and lifecycle for explicit representation copies."""
        replacement = self._publishes_array_replacement(plan)
        if plan.array is None or (plan.array.native_order == plan.array.order and not replacement):
            return (
                (self._diagnostic(plan.owner_path, "unexpected-transformations", plan.transformations),)
                if plan.transformations
                else ()
            )
        if not replacement:
            representation = self._array_representation_transformation_diagnostics(plan)
            if representation:
                return representation
        return (
            *self._transformation_phase_diagnostics(plan),
            *(
                diagnostic
                for transformation in plan.transformations
                for diagnostic in self._one_transformation_diagnostics(plan, transformation)
            ),
        )

    def _array_representation_transformation_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate whether an argument requires the supported representation pair."""
        array = plan.array
        if array is None:
            return (self._diagnostic(plan.owner_path, "missing-transformation-array", None),)
        if array.order != "ORDER_C" or array.native_order != "ORDER_F":
            return (
                self._diagnostic(
                    plan.owner_path,
                    "unsupported-array-representation-transform",
                    f"{array.order}:{array.native_order}",
                ),
            )
        return ()

    def _transformation_phase_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the lifecycle phases implied by completed ownership."""
        expected_phases = []
        if plan.binding.codegen_action is not CodegenAction.IDENTITY_OUTPUT:
            expected_phases.append(WritebackPhase.COPY_IN)
        if plan.mutates_native or self._publishes_array_replacement(plan):
            expected_phases.append(WritebackPhase.COPY_OUT)
        expected_phases.append(WritebackPhase.CLEANUP)
        if tuple(item.phase for item in plan.transformations) == tuple(expected_phases):
            return ()
        return (
            self._diagnostic(
                plan.owner_path,
                "invalid-transformation-phases",
                tuple(item.phase.value for item in plan.transformations),
            ),
        )

    def _one_transformation_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        transformation,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one transformation's layer and action vocabulary."""
        diagnostics = []
        if transformation.layer is not TransformationLayer.BINDING:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-transformation-layer", transformation.layer.value)
            )
        expected_action = {
            WritebackPhase.COPY_IN: TransformationAction.COPY_ARRAY_REPRESENTATION,
            WritebackPhase.COPY_OUT: (
                TransformationAction.PUBLISH_ARRAY_REPLACEMENT
                if self._publishes_array_replacement(plan)
                else TransformationAction.COPY_ARRAY_REPRESENTATION
            ),
            WritebackPhase.CLEANUP: TransformationAction.RELEASE_TEMPORARY,
        }[transformation.phase]
        if transformation.action is not expected_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-transformation-action",
                    transformation.action.value,
                )
            )
        return tuple(diagnostics)

    @staticmethod
    def _publishes_array_replacement(plan: ArgumentTransferPlan) -> bool:
        """Return whether COPY_OUT transfers a mutable NumPy replacement."""
        return any(
            transformation.phase is WritebackPhase.COPY_OUT
            and transformation.action is TransformationAction.PUBLISH_ARRAY_REPLACEMENT
            for transformation in plan.transformations
        )

    def _argument_family_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        available_roles: tuple[str, ...],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Dispatch one argument from its completed object-kind decision."""
        if plan.callback is not None or plan.datatype_family is DatatypeFamily.CALLBACK:
            return self._callback_argument_diagnostics(plan)
        match plan.object_kind:
            case ObjectKind.SCALAR:
                diagnostics = list(self._scalar_boundary_diagnostics(plan))
                if plan.array is not None:
                    diagnostics.append(self._diagnostic(plan.owner_path, "unexpected-scalar-array-handoff", None))
                if plan.datatype_family is DatatypeFamily.STRING:
                    diagnostics.append(
                        self._diagnostic(
                            plan.owner_path,
                            "invalid-scalar-datatype-family",
                            plan.datatype_family.value,
                        )
                    )
                return tuple(diagnostics)
            case ObjectKind.STRING:
                diagnostics = list(self._string_boundary_diagnostics(plan))
                if plan.array is not None:
                    diagnostics.append(self._diagnostic(plan.owner_path, "unexpected-string-array-handoff", None))
                return tuple(diagnostics)
            case ObjectKind.NUMPY_ARRAY:
                return (
                    *self._array_boundary_diagnostics(plan),
                    *self._array_extent_reference_diagnostics(plan, available_roles),
                )
            case ObjectKind.DERIVED_TYPE:
                return self._derived_argument_diagnostics(plan)
            case _:
                return (
                    self._diagnostic(
                        plan.owner_path,
                        "unsupported-argument-object-kind",
                        plan.object_kind.value,
                    ),
                )

    def _callback_argument_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one balanced callback role graph before backend emission."""
        callback = plan.callback
        if callback is None:
            return (self._diagnostic(plan.owner_path, "missing-callback-handoff", None),)
        return (
            *self._callback_outer_handoff_diagnostics(plan),
            *self._callback_runtime_diagnostics(plan.owner_path, callback),
            *self._callback_symbol_diagnostics(plan.owner_path, callback),
            *self._procedure_prototype_diagnostics(callback.prototype),
            *self._callback_prototype_alignment_diagnostics(callback),
            *(
                diagnostic
                for position, transfer in enumerate(callback.arguments)
                for diagnostic in self._callback_transfer_diagnostics(transfer, position)
            ),
            *self._callback_result_diagnostics(callback),
        )

    def _callback_prototype_alignment_diagnostics(
        self,
        callback: CallbackHandoffPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require callback actions to remain subordinate to the one shared signature."""
        prototype = callback.prototype
        if len(prototype.arguments) != len(callback.arguments):
            return (self._diagnostic(callback.owner_path, "inconsistent-callback-prototype-arguments", prototype.name),)
        if any(
            not self._prototype_argument_matches_transfer(argument, transfer)
            for argument, transfer in zip(prototype.arguments, callback.arguments, strict=True)
        ):
            return (self._diagnostic(callback.owner_path, "inconsistent-callback-prototype-arguments", prototype.name),)
        prototype_result = prototype.result
        transfer = callback.result.transfer
        if (prototype_result is None) != (transfer is None):
            return (self._diagnostic(callback.owner_path, "inconsistent-callback-prototype-result", prototype.name),)
        if (
            prototype_result is not None
            and transfer is not None
            and not self._prototype_result_matches_transfer(prototype_result, transfer)
        ):
            return (self._diagnostic(callback.owner_path, "inconsistent-callback-prototype-result", prototype.name),)
        return ()

    @staticmethod
    def _prototype_argument_matches_transfer(
        argument: ProcedurePrototypeArgumentPlan,
        transfer: CallbackTransferPlan,
    ) -> bool:
        """Compare signature characteristics without callback conversion actions."""
        return (
            argument.name,
            argument.semantic_type_name,
            argument.rank,
            argument.passed_by_value,
            argument.intent,
            argument.character_length,
            WrapperGenerator._prototype_array_shape(argument.array),
            argument.derived_type_identity,
            argument.derived_backend_symbol,
        ) == (
            transfer.name,
            transfer.semantic_type_name,
            transfer.rank,
            transfer.passed_by_value,
            transfer.intent,
            transfer.character_length,
            WrapperGenerator._prototype_array_shape(transfer.array),
            transfer.derived_type_identity,
            transfer.derived_backend_symbol,
        )

    @staticmethod
    def _prototype_result_matches_transfer(
        result: ProcedurePrototypeResultPlan,
        transfer: CallbackTransferPlan,
    ) -> bool:
        """Compare function-result characteristics without conversion actions."""
        return (
            result.semantic_type_name,
            result.rank,
            result.character_length,
            WrapperGenerator._prototype_array_shape(result.array),
            result.derived_type_identity,
            result.derived_backend_symbol,
        ) == (
            transfer.semantic_type_name,
            transfer.rank,
            transfer.character_length,
            WrapperGenerator._prototype_array_shape(transfer.array),
            transfer.derived_type_identity,
            transfer.derived_backend_symbol,
        )

    @staticmethod
    def _prototype_array_shape(array: ArrayHandoffPlan | None) -> tuple[str, ...] | None:
        """Return signature-relevant shape text without comparing ABI roles."""
        return array.shape if array is not None else None

    def _callback_outer_handoff_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Keep callback outer arguments separate from array and derived handoffs."""
        diagnostics = []
        if plan.datatype_family is not DatatypeFamily.CALLBACK:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-callback-datatype-family", plan.datatype_family)
            )
        if plan.derived is not None or plan.derived_call is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "callback-has-derived-call-handoff", None))
        if plan.array is not None or plan.native_array_handle is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "callback-has-outer-array-handoff", None))
        return tuple(diagnostics)

    def _callback_runtime_diagnostics(
        self,
        owner_path: str,
        callback: CallbackHandoffPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the documented lifecycle, thread, GIL, and fatal envelope."""
        candidates = (
            (callback.lifecycle != tuple(CallbackLifecycleAction), "unbalanced-callback-lifecycle", callback.lifecycle),
            (
                callback.thread_action is not CallbackThreadAction.REQUIRE_ENTERING_THREAD,
                "invalid-callback-thread-action",
                callback.thread_action,
            ),
            (
                callback.gil_actions != (CallbackGILAction.ACQUIRE_GIL, CallbackGILAction.RELEASE_GIL),
                "unbalanced-callback-gil-actions",
                callback.gil_actions,
            ),
            (
                callback.fatal_action is not CallbackFatalAction.ABORT_WITH_PYTHON_ERROR,
                "invalid-callback-fatal-action",
                callback.fatal_action,
            ),
        )
        return tuple(self._diagnostic(owner_path, code, value) for invalid, code, value in candidates if invalid)

    def _callback_symbol_diagnostics(
        self,
        owner_path: str,
        callback: CallbackHandoffPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require five distinct valid generated identifiers for one site."""
        symbols = (
            callback.binding.context_type_symbol,
            callback.binding.context_current_symbol,
            callback.bridge.adapter_symbol,
            callback.entrypoint.support_procedure.symbol_name,
            callback.binding.abort_symbol,
        )
        if any(not symbol or not symbol.isidentifier() for symbol in symbols) or len(set(symbols)) != len(symbols):
            return (self._diagnostic(owner_path, "invalid-callback-symbols", symbols),)
        return ()

    def _callback_transfer_diagnostics(
        self,
        transfer: CallbackTransferPlan,
        position: int,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one ordered callback ABI transfer and its subordinate roles."""
        diagnostics = []
        if not transfer.owner_path or not transfer.name:
            diagnostics.append(self._diagnostic(transfer.owner_path, "incomplete-callback-transfer", position))
        diagnostics.extend(self._callback_array_role_diagnostics(transfer, position))
        diagnostics.extend(self._callback_string_role_diagnostics(transfer, position))
        diagnostics.extend(self._callback_derived_role_diagnostics(transfer, position))
        diagnostics.extend(self._callback_scalar_projection_diagnostics(transfer, position))
        return tuple(diagnostics)

    def _callback_scalar_projection_diagnostics(
        self,
        transfer: CallbackTransferPlan,
        position: int,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require every primitive scalar callback transfer to use its value projection."""
        if position < 0 or transfer.object_kind is not ObjectKind.SCALAR or transfer.rank != 0:
            return ()
        valid = (
            transfer.python_action is PythonBarrierAction.SCALAR_VALUE
            and transfer.abi in {CallbackABIKind.VALUE, CallbackABIKind.REFERENCE}
            and transfer.adapter_action
            in {
                CallbackTransferAction.COPY_IN,
                CallbackTransferAction.COPY_OUT,
                CallbackTransferAction.COPY_IN_OUT,
            }
        )
        return (
            ()
            if valid
            else (self._diagnostic(transfer.owner_path, "inconsistent-callback-scalar-value-projection", position),)
        )

    def _callback_array_role_diagnostics(
        self,
        transfer: CallbackTransferPlan,
        position: int,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require shape roles exactly for data-and-shape ABI transfers."""
        if transfer.abi is CallbackABIKind.DATA_AND_SHAPE:
            if transfer.array is None or transfer.rank <= 0 or len(transfer.extent_roles) != transfer.rank:
                return (self._diagnostic(transfer.owner_path, "incomplete-callback-array-roles", position),)
            return ()
        if transfer.array is not None or transfer.extent_roles:
            return (self._diagnostic(transfer.owner_path, "unexpected-callback-array-roles", position),)
        return ()

    def _callback_string_role_diagnostics(
        self,
        transfer: CallbackTransferPlan,
        position: int,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require a fixed length role exactly for data-and-length transfers."""
        if transfer.abi is CallbackABIKind.DATA_AND_LENGTH:
            if transfer.character_length is None or transfer.length_role is None:
                return (self._diagnostic(transfer.owner_path, "incomplete-callback-string-roles", position),)
            return ()
        if transfer.length_role is not None:
            return (self._diagnostic(transfer.owner_path, "unexpected-callback-length-role", position),)
        return ()

    def _callback_derived_role_diagnostics(
        self,
        transfer: CallbackTransferPlan,
        position: int,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Keep derived ABI selection and type symbols exactly paired."""
        derived = transfer.abi is CallbackABIKind.DERIVED_ADDRESS
        if derived != bool(transfer.derived_type_identity and transfer.derived_backend_symbol):
            return (self._diagnostic(transfer.owner_path, "inconsistent-callback-derived-identity", position),)
        return ()

    def _callback_result_diagnostics(
        self,
        callback: CallbackHandoffPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the callback result action to agree with its typed transfer."""
        result = callback.result
        if result.action is CallbackResultAction.RETURN_VOID:
            return (
                (self._diagnostic(callback.owner_path, "callback-void-has-transfer", result.transfer),)
                if result.transfer is not None
                else ()
            )
        if result.transfer is None:
            return (self._diagnostic(callback.owner_path, "callback-result-missing-transfer", result.action),)
        expected_abi = {
            CallbackResultAction.RETURN_SCALAR: CallbackABIKind.VALUE,
            CallbackResultAction.RETURN_ARRAY_ADDRESS: CallbackABIKind.DATA_AND_SHAPE,
            CallbackResultAction.RETURN_DERIVED_ADDRESS: CallbackABIKind.DERIVED_ADDRESS,
        }.get(result.action)
        if expected_abi is None or result.transfer.abi is not expected_abi:
            return (self._diagnostic(callback.owner_path, "inconsistent-callback-result-action", result.action),)
        return self._callback_transfer_diagnostics(result.transfer, -1)

    # Derived-type argument validation.
    def _derived_argument_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one wrapper-address handoff and shared derived facet."""
        diagnostics = []
        if plan.datatype_family is not DatatypeFamily.DERIVED:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-derived-datatype-family", plan.datatype_family)
            )
        if plan.derived is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-derived-handoff", None))
        elif plan.projected_call_slot.derived is not plan.derived:
            diagnostics.append(self._diagnostic(plan.owner_path, "unshared-derived-handoff", None))
        else:
            diagnostics.extend(self._derived_handoff_identity_diagnostics(plan.owner_path, plan.derived))
            if plan.derived.origin is not DerivedObjectOrigin.CALLER_WRAPPER:
                diagnostics.append(
                    self._diagnostic(plan.owner_path, "invalid-derived-argument-origin", plan.derived.origin)
                )
        diagnostics.extend(self._derived_call_diagnostics(plan))
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.OPAQUE_ADDRESS:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-derived-handoff-mode", plan.entrypoint.handoff_mode)
            )
        if plan.array is not None or plan.native_array_handle is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "derived-handoff-has-array-policy", None))
        return tuple(diagnostics)

    def _derived_call_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the completed dummy/storage dispatch without re-deriving policy."""
        call = plan.derived_call
        if call is None:
            return (self._diagnostic(plan.owner_path, "missing-derived-call-policy", None),)
        diagnostics = [
            *self._derived_call_case_diagnostics(plan),
            *self._derived_call_writeback_diagnostics(plan),
        ]
        expected_handoff = (
            DerivedNativeHandoff.TYPED_VALUE
            if call.dummy_category is DerivedDummyCategory.VALUE
            else DerivedNativeHandoff.REFERENCE
        )
        if plan.derived is not None and plan.derived.native_handoff is not expected_handoff:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-derived-native-handoff",
                    plan.derived.native_handoff,
                )
            )
        if not call.status_role or not call.origin_identity_role:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-derived-call-runtime-role", None))
        if call.acquisition_order != plan.native_position or call.cleanup_order != -plan.native_position:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-call-order", call))
        return tuple(diagnostics)

    def _derived_call_case_diagnostics(self, plan: ArgumentTransferPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the complete actual-storage matrix for one derived dummy.

        The completed call policy must name each ``DerivedObjectStorage``
        exactly once.  Each case's compatibility, access, failure, and ABI
        code fields are checked mechanically; no dummy-category behavior is
        inferred or changed here.
        """
        call = plan.derived_call
        diagnostics = []
        storages = tuple(case.actual_storage for case in call.cases)
        if set(storages) != set(DerivedObjectStorage) or len(storages) != len(DerivedObjectStorage):
            diagnostics.append(self._diagnostic(plan.owner_path, "incomplete-derived-call-matrix", storages))
        for case in call.cases:
            incompatible = case.action is DerivedCallAction.INCOMPATIBLE
            if incompatible != (case.access is DerivedActualAccess.NONE):
                diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-call-access", case))
            if incompatible != bool(case.failure_kind and case.failure_message):
                diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-call-failure", case))
            if incompatible == bool(case.abi_code):
                diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-call-abi-code", case))
        return tuple(diagnostics)

    def _derived_call_writeback_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the completed derived writeback selected for one dummy.

        The expected value is derived solely from the stored dummy category and
        mutability fact so this validator can detect projection drift.  It
        returns diagnostics without modifying lifecycle policy.
        """
        call = plan.derived_call
        diagnostics = []
        expected_writeback = (
            DerivedWriteback.NONE
            if call.dummy_category is DerivedDummyCategory.VALUE
            else DerivedWriteback.ALLOCATION_STATE
            if call.dummy_category in {DerivedDummyCategory.ALLOCATABLE, DerivedDummyCategory.ALLOCATABLE_TARGET}
            else DerivedWriteback.POINTER_ASSOCIATION
            if call.dummy_category is DerivedDummyCategory.POINTER
            else DerivedWriteback.OBJECT_MUTATION
            if plan.mutates_native
            else DerivedWriteback.NONE
        )
        if call.writeback is not expected_writeback:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-writeback", call.writeback.value))
        return tuple(diagnostics)

    def _derived_handoff_identity_diagnostics(self, owner_path, handoff) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed native identity, storage, and lifetime facts.

        ``handoff`` is a plan-projected derived-object record.  The method
        checks its canonical type identity, origin-compatible storage, owner
        retention/release pair, and pointer-target lifetime in that order.  It
        emits diagnostics only and never supplies a missing lifetime policy.
        """
        diagnostics = []

        # Check the canonical native identity and origin-specific storage first.
        if handoff.type_identity != (handoff.native_scope, handoff.native_type_name):
            diagnostics.append(self._diagnostic(owner_path, "inconsistent-derived-type-identity", handoff))
        allowed_storage = {
            DerivedObjectOrigin.CALLER_WRAPPER: {DerivedObjectStorage.DIRECT},
            DerivedObjectOrigin.WRAPPER_RESULT: {
                DerivedObjectStorage.DIRECT,
                DerivedObjectStorage.ALLOCATABLE_HOLDER,
                DerivedObjectStorage.POINTER_HOLDER,
            },
            DerivedObjectOrigin.NATIVE_MODULE: {
                DerivedObjectStorage.MODULE_PROXY,
                DerivedObjectStorage.MODULE_TARGET,
                DerivedObjectStorage.MODULE_ALLOCATABLE,
                DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
                DerivedObjectStorage.MODULE_POINTER,
            },
            DerivedObjectOrigin.BORROWED_FIELD: {DerivedObjectStorage.DIRECT},
            DerivedObjectOrigin.CONSTANT_VALUE: {DerivedObjectStorage.DIRECT},
        }.get(handoff.origin, set())
        if handoff.storage not in allowed_storage:
            diagnostics.append(self._diagnostic(owner_path, "invalid-derived-storage", handoff.storage))

        # Then check the primary retention/release pair required by that origin.
        expected_lifetime = {
            DerivedObjectOrigin.CALLER_WRAPPER: (
                DerivedOwnerRetention.CALLER_WRAPPER,
                DerivedRelease.NONE,
            ),
            DerivedObjectOrigin.WRAPPER_RESULT: (
                DerivedOwnerRetention.WRAPPER_INSTANCE,
                DerivedRelease.WRAPPER_DESTROY,
            ),
            DerivedObjectOrigin.NATIVE_MODULE: (
                DerivedOwnerRetention.NATIVE_MODULE,
                DerivedRelease.NATIVE_OWNER,
            ),
            DerivedObjectOrigin.BORROWED_FIELD: (
                DerivedOwnerRetention.PARENT_WRAPPER,
                DerivedRelease.NONE,
            ),
            DerivedObjectOrigin.CONSTANT_VALUE: (
                DerivedOwnerRetention.WRAPPER_INSTANCE,
                DerivedRelease.WRAPPER_DESTROY,
            ),
        }.get(handoff.origin)
        if expected_lifetime is None:
            diagnostics.append(self._diagnostic(owner_path, "invalid-derived-origin", handoff.origin))
            return tuple(diagnostics)
        expected_retention, expected_release = expected_lifetime
        if handoff.owner_retention is not expected_retention:
            diagnostics.append(self._diagnostic(owner_path, "invalid-derived-owner-retention", handoff.owner_retention))
        if handoff.release is not expected_release:
            diagnostics.append(self._diagnostic(owner_path, "invalid-derived-release", handoff.release))

        # Finally validate the separate target lifetime, including pointer storage.
        target_lifetime = (handoff.target_owner_retention, handoff.target_release)
        allowed_target_lifetimes = {
            (DerivedOwnerRetention.NONE, DerivedRelease.NONE),
            (DerivedOwnerRetention.NATIVE_MODULE, DerivedRelease.NATIVE_OWNER),
        }
        if target_lifetime not in allowed_target_lifetimes:
            diagnostics.append(self._diagnostic(owner_path, "invalid-derived-target-lifetime", target_lifetime))
        if handoff.storage in {
            DerivedObjectStorage.POINTER_HOLDER,
            DerivedObjectStorage.MODULE_POINTER,
        } and target_lifetime != (DerivedOwnerRetention.NATIVE_MODULE, DerivedRelease.NATIVE_OWNER):
            diagnostics.append(self._diagnostic(owner_path, "missing-derived-pointer-target-owner", target_lifetime))
        return tuple(diagnostics)

    def _array_extent_reference_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        available_roles: tuple[str, ...],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require every planned extent dependency to name a function role."""
        if plan.array is None:
            return ()
        return tuple(
            self._diagnostic(plan.owner_path, "unavailable-array-extent-reference", role)
            for axis_roles in plan.array.extent_reference_roles
            for role in axis_roles
            if role not in available_roles
        ) + tuple(
            self._diagnostic(plan.owner_path, "unavailable-array-extent-callable", role)
            for axis_roles in plan.array.extent_callable_roles
            for role in axis_roles
            if role not in available_roles
        )

    def _argument_policy_consistency_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return cross-view role and completed-action diagnostics."""
        diagnostics = []
        role = plan.entrypoint.handoff_role
        slot = plan.projected_call_slot
        adapter = slot.adapter
        if adapter is None:
            return (self._diagnostic(plan.owner_path, "missing-argument-adapter-facet", None),)
        if plan.entrypoint.pass_callback_parameter:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-callback-entrypoint-parameter",
                    plan.entrypoint.pass_callback_parameter,
                )
            )
        if slot.symbolic_role != role:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-native-handoff", role))
        if plan.bridge.native_action is not adapter.native_action:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-native-action", plan.bridge.native_action.value)
            )
        if plan.bridge.data_action is not adapter.bridge_data_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-bridge-data-action",
                    adapter.bridge_data_action.value,
                )
            )
        if plan.array is not slot.array:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-array-handoff", plan.array))
        if plan.native_array_handle is not slot.native_array_handle:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-native-array-handle", plan.native_array_handle)
            )
        diagnostics.extend(self._argument_completed_fact_diagnostics(plan))
        if plan.bridge.copy_reason != adapter.bridge_copy_reason:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-bridge-copy-reason",
                    adapter.bridge_copy_reason,
                )
            )
        return tuple(diagnostics)

    def _argument_completed_fact_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return projected action, length, mutability, and nullability drift."""
        diagnostics = []
        slot = plan.projected_call_slot
        adapter = slot.adapter
        if adapter is None:
            return (self._diagnostic(plan.owner_path, "missing-argument-adapter-facet", None),)
        if plan.binding.codegen_action is not plan.bridge.codegen_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path, "inconsistent-argument-codegen-action", plan.bridge.codegen_action.value
                )
            )
        if plan.binding.codegen_action is not adapter.codegen_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-native-slot-codegen-action",
                    adapter.codegen_action.value,
                )
            )
        if plan.character_length != slot.character_length:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-argument-character-length",
                    slot.character_length,
                )
            )
        if plan.binding.writable != plan.mutates_native:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-argument-mutability", plan.binding.writable)
            )
        if plan.binding.nullable != plan.nullable:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-argument-nullability", plan.binding.nullable)
            )
        if slot.object_kind is not plan.object_kind:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-argument-object-kind",
                    slot.object_kind,
                )
            )
        diagnostics.extend(self._logical_argument_slot_diagnostics(plan))
        return tuple(diagnostics)

    def _logical_argument_slot_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return scalar and array logical-policy drift from the native slot.

        The helper consumes one completed transfer plan and returns diagnostics
        without changing it.  It compares only copied plan facts; it does not
        infer an ABI from the semantic datatype.
        """
        diagnostics = []
        slot = plan.projected_call_slot
        if slot.scalar_logical_abi is not plan.scalar_logical_abi:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-scalar-logical-abi",
                    slot.scalar_logical_abi.value,
                )
            )
        if slot.scalar_native_type != plan.scalar_native_type:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-scalar-native-type",
                    slot.scalar_native_type,
                )
            )
        if slot.array_logical_abi is not plan.array_logical_abi:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-array-logical-abi",
                    slot.array_logical_abi.value,
                )
            )
        if slot.array_native_type != plan.array_native_type:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-array-native-type",
                    slot.array_native_type,
                )
            )
        if slot.array_copy_in != plan.array_copy_in:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-array-copy-in", slot.array_copy_in))
        if slot.array_copy_out != plan.array_copy_out:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-array-copy-out",
                    slot.array_copy_out,
                )
            )
        return tuple(diagnostics)

    def _argument_slot_consistency_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        function_slots: dict[int, NativeEntrypointProjectedSlotPlan],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return argument position and native-slot graph diagnostics."""
        diagnostics = []
        slot = plan.projected_call_slot
        if slot.native_position != plan.native_position:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-native-position", plan.native_position))
        if slot.python_position != plan.python_position:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-python-position", plan.python_position))
        if function_slots.get(plan.native_position) is not slot:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-function-native-slot", plan.native_position)
            )
        if slot.source_kind not in {"implicit", "projection"}:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-argument-native-slot", slot.source_kind))
        return tuple(diagnostics)

    def _argument_data_action_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the completed data action to match the selected scalar path."""
        expected = self._expected_argument_data_action(plan)
        if plan.bridge.data_action is expected:
            return ()
        return (
            self._diagnostic(
                plan.owner_path,
                "invalid-bridge-data-action",
                f"{plan.bridge.data_action.value}:{expected.value}",
            ),
        )

    def _expected_argument_data_action(self, plan: ArgumentTransferPlan) -> BridgeDataAction:
        """Return the data action implied by completed orthogonal selectors."""
        if plan.callback is not None:
            return BridgeDataAction.DIRECT_TRANSFER
        if plan.array_logical_abi is ArrayLogicalABI.NATIVE_KIND_COPY:
            return BridgeDataAction.COPY_REPRESENTATION
        if plan.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY:
            return BridgeDataAction.COPY_REPRESENTATION
        if self._uses_typed_derived_value(plan):
            return BridgeDataAction.COPY_REPRESENTATION
        return self._expected_handoff_data_action(plan)

    def _expected_handoff_data_action(self, plan: ArgumentTransferPlan) -> BridgeDataAction:
        """Dispatch descriptor, buffer, and scalar/address handoff actions."""
        mode = plan.entrypoint.handoff_mode
        if mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            return self._expected_native_descriptor_data_action(plan)
        buffer_actions = {
            ArgumentHandoffMode.ARRAY_BUFFER: BridgeDataAction.ASSOCIATE_VIEW,
            ArgumentHandoffMode.CHARACTER_BUFFER: BridgeDataAction.COPY_REPRESENTATION,
        }
        if mode in buffer_actions:
            return buffer_actions[mode]
        return self._expected_scalar_or_address_data_action(plan)

    def _expected_scalar_or_address_data_action(self, plan: ArgumentTransferPlan) -> BridgeDataAction:
        """Select remaining scalar, string, optional, and opaque-address actions."""
        mode = plan.entrypoint.handoff_mode
        if plan.object_kind is ObjectKind.STRING and mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            return BridgeDataAction.COPY_REPRESENTATION
        if plan.entrypoint.optional_mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
            return self._expected_optional_descriptor_data_action(plan)
        if plan.entrypoint.optional_mode is OptionalMode.NULLABLE_VALUE or mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            return BridgeDataAction.ASSOCIATE_VIEW
        return BridgeDataAction.DIRECT_TRANSFER

    @staticmethod
    def _uses_typed_derived_value(plan: ArgumentTransferPlan) -> bool:
        """Return whether policy selects the exact typed-value path."""
        return bool(plan.derived is not None and plan.derived.native_handoff is DerivedNativeHandoff.TYPED_VALUE)

    def _expected_native_descriptor_data_action(self, plan: ArgumentTransferPlan) -> BridgeDataAction:
        """Distinguish call-local facts from persistent projected descriptors."""
        handle = plan.native_array_handle
        if handle is not None and handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR:
            return BridgeDataAction.DIRECT_TRANSFER
        return BridgeDataAction.ASSOCIATE_VIEW

    def _expected_optional_descriptor_data_action(self, plan: ArgumentTransferPlan) -> BridgeDataAction:
        """Return the scalar optional descriptor view/copy selection."""
        if plan.derived_call is not None:
            return BridgeDataAction.ASSOCIATE_VIEW
        if plan.projected_call_slot.value_kind == "allocatable":
            return BridgeDataAction.COPY_REPRESENTATION
        return BridgeDataAction.ASSOCIATE_VIEW

    # Scalar argument validation.
    def _scalar_boundary_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return completed Python/native scalar boundary consistency diagnostics."""
        action = plan.binding.python_action
        if action not in {
            PythonBarrierAction.SCALAR_VALUE,
            PythonBarrierAction.SCALAR_STORAGE,
            PythonBarrierAction.RAW_ADDRESS,
        }:
            return (self._diagnostic(plan.owner_path, "invalid-scalar-python-action", action.value),)
        expected = {
            PythonBarrierAction.SCALAR_STORAGE: NativeBarrierAction.PASS_STORAGE_ADDRESS,
            PythonBarrierAction.RAW_ADDRESS: NativeBarrierAction.PASS_RAW_ADDRESS,
        }.get(action)
        if expected is None:
            if plan.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
                return (self._diagnostic(plan.owner_path, "unexpected-opaque-address-handoff", action.value),)
            return ()
        diagnostics = []
        if plan.bridge.native_action is not expected:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-address-action", plan.bridge.native_action.value)
            )
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.OPAQUE_ADDRESS:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-address-handoff", plan.entrypoint.handoff_mode.value)
            )
        if plan.bridge.data_action is not BridgeDataAction.ASSOCIATE_VIEW:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-address-data-action", plan.bridge.data_action.value)
            )
        if plan.binding.optional_mode is not OptionalMode.REQUIRED and action is PythonBarrierAction.RAW_ADDRESS:
            diagnostics.append(self._diagnostic(plan.owner_path, "optional-scalar-address-boundary", action.value))
        return tuple(diagnostics)

    # Ordinary-array and native-array-handle argument validation.
    def _array_boundary_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one ordinary-array transfer selected by object kind."""
        array = plan.array
        if array is None:
            return (self._diagnostic(plan.owner_path, "missing-array-handoff", None),)
        if plan.native_array_handle is not None:
            return self._native_array_handle_argument_diagnostics(plan)
        diagnostics = [
            *self._array_ownership_diagnostics(plan),
            *self._array_action_diagnostics(plan),
            *self._array_scope_diagnostics(plan),
            *self._array_shape_diagnostics(plan),
            *self._native_array_actual_diagnostics(plan),
        ]
        return tuple(diagnostics)

    def _native_array_handle_argument_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one typed descriptor handle and its shared native slot."""
        handle = plan.native_array_handle
        if handle is None:
            return ()
        diagnostics = [
            *self._native_array_handle_argument_action_diagnostics(plan, handle),
            *self._native_array_handle_argument_ownership_diagnostics(plan, handle),
            *self._native_array_handle_shape_diagnostics(plan.owner_path, handle),
            *self._native_descriptor_handoff_diagnostics(plan.owner_path, handle, plan),
            *self._native_array_default_handle_diagnostics(plan.owner_path, handle),
        ]
        if plan.array is not handle.array:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-handle-array-facet", plan.array))
        if plan.native_array_actual is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "descriptor-has-array-actual-policy", None))
        return tuple(diagnostics)

    def _native_array_handle_argument_action_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the shared action vocabulary for descriptor inputs."""
        diagnostics = []
        expected = (
            ("python-action", plan.binding.python_action, PythonBarrierAction.WRAPPER_INSTANCE),
            ("native-action", plan.bridge.native_action, NativeBarrierAction.PASS_NATIVE_DESCRIPTOR),
            ("handoff-mode", plan.entrypoint.handoff_mode, ArgumentHandoffMode.NATIVE_DESCRIPTOR),
        )
        diagnostics.extend(
            self._diagnostic(plan.owner_path, f"invalid-handle-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        )
        projected = handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
        expected_codegen = CodegenAction.IN_PLACE_ARGUMENT if projected else CodegenAction.CALL_LOCAL_INPUT
        if plan.binding.codegen_action is not expected_codegen:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-handle-codegen-action", plan.binding.codegen_action.value)
            )
        return tuple(diagnostics)

    def _native_array_handle_argument_ownership_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate caller ownership and absence semantics for descriptor inputs."""
        diagnostics = []
        if plan.ownership_owner is not OwnershipOwner.CALLER or handle.owner is not OwnershipOwner.CALLER:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-handle-argument-owner", plan.ownership_owner))
        if plan.transfer_mode not in {TransferMode.CALL_LOCAL, TransferMode.IN_PLACE}:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-handle-argument-transfer", plan.transfer_mode.value)
            )
        expected_destruction = (
            DestructionPolicy.CALLER
            if handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
            else DestructionPolicy.NONE
        )
        if plan.destruction_policy is not expected_destruction:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-handle-argument-destruction", plan.destruction_policy.value)
            )
        expected_optional = OptionalMode.DESCRIPTOR if handle.optional_absent else OptionalMode.REQUIRED
        if plan.binding.optional_mode is not expected_optional:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-handle-presence-mode", plan.binding.optional_mode.value)
            )
        return tuple(diagnostics)

    def _native_array_default_handle_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate caller-construction ownership, lifecycle, and named roles."""
        default = handle.default_handle
        if default.construction is NativeArrayDefaultConstruction.NONE:
            return self._disabled_native_array_default_handle_diagnostics(owner_path, handle)
        return (
            *self._native_array_default_handle_lifecycle_diagnostics(owner_path, handle),
            *self._native_array_default_handle_operation_diagnostics(owner_path, handle),
            *self._native_array_default_handle_storage_diagnostics(owner_path, handle),
        )

    def _disabled_native_array_default_handle_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require an omitted lifecycle when caller construction is disabled."""
        default = handle.default_handle
        actual = (
            default.descriptor_ownership,
            default.release,
            default.destroy_behavior,
            default.operations,
            default.operation_roles,
            default.owner_storage_role,
        )
        expected = (
            None,
            NativeArrayRelease.NONE,
            NativeArrayDestroyBehavior.NONE,
            (),
            (),
            None,
        )
        if actual == expected:
            return ()
        return (self._diagnostic(owner_path, "invalid-disabled-default-handle-policy", default),)

    def _native_array_default_handle_lifecycle_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require owned descriptor storage and finalizer release."""
        default = handle.default_handle
        diagnostics = []
        if default.descriptor_ownership is not NativeArrayDescriptorOwnership.OWNED:
            diagnostics.append(
                self._diagnostic(
                    owner_path,
                    "invalid-default-handle-descriptor-ownership",
                    default.descriptor_ownership,
                )
            )
        lifecycle = default.release, default.destroy_behavior
        expected = NativeArrayRelease.WRAPPER_DEALLOC, NativeArrayDestroyBehavior.HANDLE_FINALIZER
        if lifecycle != expected:
            diagnostics.append(self._diagnostic(owner_path, "invalid-default-handle-lifecycle", default.release))
        return tuple(diagnostics)

    def _native_array_default_handle_operation_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require complete unique operation names and matching roles."""
        operations = handle.default_handle.operations
        roles = handle.default_handle.operation_roles
        required = {
            NativeArrayOperation.SHAPE,
            NativeArrayOperation.ARRAY_ACTUAL,
            NativeArrayOperation.DESCRIPTOR,
            NativeArrayOperation.DESTROY,
        }
        if handle.descriptor_kind is NativeArrayDescriptorKind.POINTER:
            required.add(NativeArrayOperation.ASSOCIATE)
        diagnostics = []
        complete = len(set(operations)) == len(operations) and required.issubset(operations)
        if not complete:
            diagnostics.append(self._diagnostic(owner_path, "incomplete-default-handle-operations", operations))
        named_operations = tuple(operation for operation, _role in roles)
        roles_complete = named_operations == operations and all(role for _operation, role in roles)
        if not roles_complete:
            diagnostics.append(self._diagnostic(owner_path, "inconsistent-default-handle-operation-roles", roles))
        return tuple(diagnostics)

    def _native_array_default_handle_storage_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Match persistent owner storage and descriptor ABI to construction."""
        default = handle.default_handle
        expected_owner_role = {
            NativeArrayDefaultConstruction.FACT_PACKED_EMPTY: None,
            NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR: True,
        }[default.construction]
        owner_role = True if default.owner_storage_role is not None else None
        diagnostics = []
        if owner_role is not expected_owner_role:
            diagnostics.append(
                self._diagnostic(
                    owner_path, "inconsistent-default-handle-owner-storage-role", default.owner_storage_role
                )
            )
        expected_abi = {
            NativeArrayDefaultConstruction.FACT_PACKED_EMPTY: NativeDescriptorHandoffABI.FACT_PACKED_CALL_LOCAL,
            NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR: NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR,
        }[default.construction]
        if handle.handoff.abi is not expected_abi:
            diagnostics.append(
                self._diagnostic(owner_path, "inconsistent-default-handle-descriptor-abi", handle.handoff.abi)
            )
        return tuple(diagnostics)

    def _array_ownership_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate caller-owned ordinary-array lifetime facts."""
        diagnostics = []
        replacement = plan.transfer_mode is TransferMode.COPY_RETURN
        expected = (
            ("object-kind", plan.object_kind, ObjectKind.NUMPY_ARRAY),
            ("owner", plan.ownership_owner, OwnershipOwner.PYTHON if replacement else OwnershipOwner.CALLER),
            ("storage", plan.storage_mode, StorageMode.STACK),
            ("boundary-storage", plan.boundary_storage_mode, StorageMode.STACK),
        )
        diagnostics.extend(
            self._diagnostic(plan.owner_path, f"invalid-array-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        )
        expected_transfer = (
            TransferMode.COPY_RETURN
            if replacement
            else (TransferMode.IN_PLACE if plan.mutates_native else TransferMode.CALL_LOCAL)
        )
        expected_destruction = (
            DestructionPolicy.PYTHON_REFCOUNT
            if replacement
            else (DestructionPolicy.CALLER if plan.mutates_native else DestructionPolicy.NONE)
        )
        if plan.transfer_mode is not expected_transfer:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-array-transfer", plan.transfer_mode.value))
        if plan.destruction_policy is not expected_destruction:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-destruction", plan.destruction_policy.value)
            )
        return tuple(diagnostics)

    def _native_array_actual_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate accepted native-handle sources on the ordinary buffer ABI."""
        actual = plan.native_array_actual
        if actual is None:
            return ()
        array = plan.array
        expected_sources = (
            NativeArraySourceKind.NDARRAY,
            NativeArraySourceKind.ALLOCATABLE_HANDLE,
            NativeArraySourceKind.POINTER_HANDLE,
        )
        diagnostics = [
            *self._native_array_actual_source_diagnostics(plan, expected_sources),
            *self._native_array_actual_shape_diagnostics(plan),
            *self._native_array_actual_validation_diagnostics(plan),
        ]
        expected_order = None if array is None or array.rank == 1 else ("C" if array.order == "ORDER_C" else "F")
        if actual.order != expected_order:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-array-actual-order", actual.order))
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER:
            diagnostics.append(self._diagnostic(plan.owner_path, "array-actual-not-buffer-handoff", None))
        return tuple(diagnostics)

    def _native_array_actual_source_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        expected_sources: tuple[NativeArraySourceKind, ...],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the explicit ndarray/handle accepted-source set."""
        actual = plan.native_array_actual
        if actual is None or actual.accepted_sources == expected_sources:
            return ()
        return (self._diagnostic(plan.owner_path, "invalid-array-actual-sources", actual.accepted_sources),)

    def _native_array_actual_shape_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate handle-actual rank and shape against the shared array facet."""
        actual = plan.native_array_actual
        array = plan.array
        if actual is None or (
            array is not None
            and actual.rank == array.rank
            and actual.shape == array.shape
            and actual.flatten_storage == array.flatten_python_storage
            and actual.flat_axis == array.flat_axis
        ):
            return ()
        return (self._diagnostic(plan.owner_path, "inconsistent-array-actual-shape", actual.shape),)

    def _native_array_actual_validation_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate writeability, native byte order, and alignment flags."""
        actual = plan.native_array_actual
        if actual is None:
            return ()
        diagnostics = []
        expected_writable = plan.mutates_native or self._publishes_array_replacement(plan)
        if actual.writable != expected_writable:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-array-actual-writeability", actual.writable)
            )
        array = plan.array
        expected_contiguous = bool(array is not None and array.contiguous is True)
        if (
            not actual.require_native_byte_order
            or not actual.require_aligned
            or actual.require_contiguous != expected_contiguous
        ):
            diagnostics.append(self._diagnostic(plan.owner_path, "incomplete-array-actual-validation", None))
        return tuple(diagnostics)

    def _native_array_handle_shape_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one concrete descriptor data facet."""
        return (
            *self._native_array_handle_rank_diagnostics(owner_path, handle),
            *self._native_array_handle_buffer_role_diagnostics(owner_path, handle),
            *self._native_array_handle_header_diagnostics(owner_path, handle),
            *self._native_array_handle_extraction_diagnostics(owner_path, handle),
        )

    def _native_array_handle_extraction_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed live-view action and descriptor mechanism together."""
        if handle.descriptor_interop is NativeArrayDescriptorInterop.MODULE_ALLOCATABLE_C_DESCRIPTOR:
            valid = (
                handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
                and handle.handle_kind is NativeArrayHandleKind.BORROWED_MODULE_DESCRIPTOR
                and handle.extraction_action is NativeArrayExtractionAction.DESCRIPTOR_VIEW
            )
            if not valid:
                return (
                    self._diagnostic(
                        owner_path,
                        "invalid-module-allocatable-descriptor-extraction",
                        handle.extraction_action,
                    ),
                )
        if (
            handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
            and handle.handle_kind is NativeArrayHandleKind.BORROWED_MODULE_DESCRIPTOR
            and handle.extraction_action is NativeArrayExtractionAction.DESCRIPTOR_VIEW
            and handle.descriptor_interop is not NativeArrayDescriptorInterop.MODULE_ALLOCATABLE_C_DESCRIPTOR
        ):
            return (
                self._diagnostic(
                    owner_path,
                    "missing-module-allocatable-descriptor-interop",
                    handle.descriptor_interop,
                ),
            )
        return ()

    def _native_array_handle_rank_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate concrete descriptor rank, shape, and axes."""
        array = handle.array
        if array.rank is None or not 1 <= array.rank <= 15:
            return (self._diagnostic(owner_path, "invalid-native-array-handle-rank", array.rank),)
        if len(array.shape) != array.rank or len(array.axes) != array.rank:
            return (self._diagnostic(owner_path, "inconsistent-native-array-handle-shape", array.shape),)
        return ()

    def _native_array_handle_buffer_role_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject ordinary array-buffer ABI roles on a descriptor facet."""
        array = handle.array
        packed_roles = (
            *array.extent_roles,
            *array.upper_bound_roles,
            *array.stride_roles,
            array.dense_actual_role,
            array.runtime_rank_role,
            array.itemsize_role,
        )
        if any(role is not None for role in packed_roles):
            return (self._diagnostic(owner_path, "descriptor-has-array-buffer-roles", None),)
        return ()

    def _native_array_handle_header_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the build header selected by completed descriptor interop."""
        needs_cfi = handle.descriptor_interop is not NativeArrayDescriptorInterop.NONE or handle.handle_kind in {
            NativeArrayHandleKind.ARGUMENT_DESCRIPTOR,
            NativeArrayHandleKind.OPTIONAL_ABSENT_HANDLE,
            NativeArrayHandleKind.OWNED_RESULT_DESCRIPTOR,
        }
        expected_headers = (NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER,) if needs_cfi else ()
        if handle.required_headers == expected_headers:
            return ()
        return (self._diagnostic(owner_path, "incomplete-native-array-build-requirements", handle.required_headers),)

    def _native_descriptor_handoff_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
        argument: ArgumentTransferPlan | None,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate descriptor ABI roles without reconstructing its policy."""
        handoff = handle.handoff
        rank = handle.array.rank
        diagnostics = []
        if rank is None:
            return (self._diagnostic(owner_path, "missing-native-descriptor-rank", None),)
        expected_counts = (
            len(handoff.lower_bound_roles),
            len(handoff.extent_roles),
            len(handoff.stride_multiplier_roles),
        )
        diagnostics.extend(self._native_descriptor_abi_diagnostics(owner_path, handle, expected_counts))
        diagnostics.extend(self._native_descriptor_presence_diagnostics(owner_path, handle, argument))
        diagnostics.extend(self._native_array_operation_diagnostics(owner_path, handle))
        return tuple(diagnostics)

    def _native_descriptor_abi_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
        expected_counts: tuple[int, int, int],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Dispatch exact role validation by typed descriptor ABI."""
        handlers = {
            NativeDescriptorHandoffABI.FACT_PACKED_CALL_LOCAL: self._fact_packed_descriptor_diagnostics,
            NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR: self._direct_descriptor_diagnostics,
            NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE: self._owned_descriptor_diagnostics,
        }
        try:
            handler = handlers[handle.handoff.abi]
        except KeyError:
            return (self._diagnostic(owner_path, "unknown-native-descriptor-handoff", handle.handoff.abi),)
        return handler(owner_path, handle, expected_counts)

    def _fact_packed_descriptor_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
        expected_counts: tuple[int, int, int],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate every call-local descriptor fact role."""
        handoff = handle.handoff
        diagnostics = []
        expected_rank = handle.array.rank
        if expected_counts != (expected_rank, expected_rank, expected_rank):
            diagnostics.append(
                self._diagnostic(owner_path, "inconsistent-native-descriptor-axis-roles", expected_counts)
            )
        if None in {
            handoff.descriptor_pointer_role,
            handoff.base_addr_role,
            handoff.elem_len_role,
            handoff.rank_role,
        }:
            diagnostics.append(self._diagnostic(owner_path, "missing-native-descriptor-fact-role", None))
        if handoff.owner_storage_role is not None:
            diagnostics.append(self._diagnostic(owner_path, "fact-packed-has-owner-storage", None))
        return tuple(diagnostics)

    def _direct_descriptor_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
        expected_counts: tuple[int, int, int],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one persistent projected standard-descriptor pointer."""
        diagnostics = []
        if handle.handoff.descriptor_pointer_role is None or any(expected_counts):
            diagnostics.append(self._diagnostic(owner_path, "invalid-direct-native-descriptor-roles", None))
        if handle.output_projection is not NativeArrayOutputProjection.PROJECTED_HANDLE:
            diagnostics.append(self._diagnostic(owner_path, "direct-descriptor-without-projection", None))
        return tuple(diagnostics)

    def _owned_descriptor_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
        expected_counts: tuple[int, int, int],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate persistent wrapper-owned result descriptor storage roles."""
        handoff = handle.handoff
        invalid = handoff.owner_storage_role is None or handoff.descriptor_pointer_role is not None
        if invalid or any(expected_counts):
            return (self._diagnostic(owner_path, "invalid-owned-native-descriptor-roles", None),)
        return ()

    def _native_descriptor_presence_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
        argument: ArgumentTransferPlan | None,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Keep Python absence distinct from descriptor allocation state."""
        presence = handle.handoff.presence_role
        if handle.optional_absent != (presence is not None):
            return (self._diagnostic(owner_path, "inconsistent-native-descriptor-presence", presence),)
        if argument is None:
            return ()
        if handle.optional_absent and argument.entrypoint.presence_role != presence:
            return (self._diagnostic(owner_path, "inconsistent-native-descriptor-presence-role", presence),)
        if not handle.optional_absent and argument.entrypoint.presence_role is not None:
            return (self._diagnostic(owner_path, "required-native-descriptor-has-presence", None),)
        return ()

    def _native_array_operation_diagnostics(
        self,
        owner_path: str,
        handle: NativeArrayHandlePlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require every handle to expose its common runtime operations exactly once."""
        operations = handle.operations
        required = self._required_native_array_operations(handle)
        diagnostics = []
        if len(set(operations)) != len(operations) or not required.issubset(operations):
            diagnostics.append(self._diagnostic(owner_path, "incomplete-native-array-operations", operations))
        roles = handle.handoff.operation_roles
        if tuple(operation for operation, _role in roles) != operations or any(not role for _operation, role in roles):
            diagnostics.append(self._diagnostic(owner_path, "inconsistent-native-array-operation-roles", roles))
        if handle.destroy_behavior is NativeArrayDestroyBehavior.HANDLE_FINALIZER:
            if NativeArrayOperation.DESTROY not in operations:
                diagnostics.append(self._diagnostic(owner_path, "missing-native-array-destroy-operation", None))
        elif NativeArrayOperation.DESTROY in operations:
            diagnostics.append(self._diagnostic(owner_path, "borrowed-native-array-has-destroy-operation", None))
        return tuple(diagnostics)

    @staticmethod
    def _required_native_array_operations(
        handle: NativeArrayHandlePlan,
    ) -> set[NativeArrayOperation]:
        """Return common operations required by the completed descriptor kind."""
        required = {
            NativeArrayOperation.SHAPE,
            NativeArrayOperation.ARRAY_ACTUAL,
            NativeArrayOperation.DESCRIPTOR,
        }
        if handle.descriptor_kind is NativeArrayDescriptorKind.POINTER:
            required.add(NativeArrayOperation.ASSOCIATE)
        return required

    def _array_action_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Dispatch completed buffer or raw-address array actions."""
        action = plan.binding.python_action
        if action is PythonBarrierAction.SCALAR_STORAGE:
            return self._scalar_storage_array_action_diagnostics(plan)
        if action is PythonBarrierAction.ARRAY_STORAGE:
            return self._array_buffer_action_diagnostics(plan)
        if action is PythonBarrierAction.RAW_ADDRESS:
            return self._raw_array_action_diagnostics(plan)
        return (self._diagnostic(plan.owner_path, "invalid-array-python-action", action.value),)

    def _scalar_storage_array_action_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate rank-zero NumPy storage passed as a scalar native address."""
        diagnostics = []
        if plan.bridge.native_action is not NativeBarrierAction.PASS_STORAGE_ADDRESS:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path, "invalid-scalar-storage-native-action", plan.bridge.native_action.value
                )
            )
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.OPAQUE_ADDRESS:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path, "invalid-scalar-storage-handoff-mode", plan.entrypoint.handoff_mode.value
                )
            )
        if plan.bridge.data_action is not BridgeDataAction.ASSOCIATE_VIEW:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-storage-data-action", plan.bridge.data_action.value)
            )
        if plan.binding.codegen_action not in {
            CodegenAction.CALL_LOCAL_INPUT,
            CodegenAction.IN_PLACE_ARGUMENT,
            CodegenAction.IDENTITY_OUTPUT,
        }:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-scalar-storage-codegen-action",
                    plan.binding.codegen_action.value,
                )
            )
        if not self._is_scalar_storage_array(plan.array):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-scalar-storage-array", plan.array))
        return tuple(diagnostics)

    def _array_buffer_action_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed NumPy-buffer binding and bridge actions."""
        diagnostics = []
        if plan.bridge.native_action is not NativeBarrierAction.PASS_ARRAY_BUFFER:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-native-action", plan.bridge.native_action.value)
            )
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-handoff-mode", plan.entrypoint.handoff_mode.value)
            )
        expected_data_action = (
            BridgeDataAction.COPY_REPRESENTATION
            if plan.array_logical_abi is ArrayLogicalABI.NATIVE_KIND_COPY
            else BridgeDataAction.ASSOCIATE_VIEW
        )
        if plan.bridge.data_action is not expected_data_action:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-data-action", plan.bridge.data_action.value)
            )
        if plan.binding.codegen_action not in {
            CodegenAction.CALL_LOCAL_INPUT,
            CodegenAction.COPY_IN_OUT,
            CodegenAction.IN_PLACE_ARGUMENT,
            CodegenAction.IDENTITY_OUTPUT,
        }:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-codegen-action", plan.binding.codegen_action.value)
            )
        return tuple(diagnostics)

    def _raw_array_action_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one raw array address through the shared action vocabulary."""
        diagnostics = []
        if plan.bridge.native_action is not NativeBarrierAction.PASS_RAW_ADDRESS:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-raw-array-native-action", plan.bridge.native_action.value)
            )
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.OPAQUE_ADDRESS:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-raw-array-handoff-mode", plan.entrypoint.handoff_mode.value)
            )
        if plan.bridge.data_action is not BridgeDataAction.ASSOCIATE_VIEW:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-raw-array-data-action", plan.bridge.data_action.value)
            )
        if plan.binding.codegen_action not in {CodegenAction.CALL_LOCAL_INPUT, CodegenAction.IN_PLACE_ARGUMENT}:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-raw-array-codegen-action", plan.binding.codegen_action.value)
            )
        return tuple(diagnostics)

    def _array_scope_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Keep array buffers and raw addresses on their completed scopes."""
        if plan.binding.python_action is PythonBarrierAction.RAW_ADDRESS:
            return self._raw_array_scope_diagnostics(plan)
        diagnostics = []
        if plan.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.NULLABLE_VALUE}:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-optional-mode", plan.binding.optional_mode.value)
            )
        if plan.binding.descriptor_boundary:
            diagnostics.append(self._diagnostic(plan.owner_path, "descriptor-backed-ordinary-array", plan.nullable))
        if plan.nullable and plan.binding.optional_mode is OptionalMode.REQUIRED:
            diagnostics.append(self._diagnostic(plan.owner_path, "nullable-required-ordinary-array", True))
        if plan.projects_result and plan.result_position is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-array-result-position", None))
        return tuple(diagnostics)

    def _raw_array_scope_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one non-optional, non-projecting raw array address."""
        diagnostics = []
        if plan.binding.optional_mode is not OptionalMode.REQUIRED:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "optional-raw-array-address", plan.binding.optional_mode.value)
            )
        if plan.nullable or plan.binding.descriptor_boundary:
            diagnostics.append(self._diagnostic(plan.owner_path, "descriptor-backed-raw-array", plan.nullable))
        if plan.projects_result or plan.result_position is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "projected-raw-array-address", plan.result_position))
        return tuple(diagnostics)

    def _array_shape_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Dispatch buffer or raw-pointee shape and ABI-role validation."""
        array = plan.array
        if array is None:
            return ()
        if plan.binding.python_action is PythonBarrierAction.RAW_ADDRESS:
            return self._raw_array_shape_diagnostics(plan)
        diagnostics = []
        if array.rank is None:
            diagnostics.extend(self._assumed_rank_array_diagnostics(plan))
        else:
            diagnostics.extend(self._concrete_rank_array_diagnostics(plan))
        diagnostics.extend(self._array_layout_role_diagnostics(plan))
        diagnostics.extend(self._array_handoff_role_diagnostics(plan))
        diagnostics.extend(self._array_itemsize_diagnostics(plan))
        return tuple(diagnostics)

    def _raw_array_shape_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate concrete dense pointee facts without packed buffer roles."""
        return (
            *self._raw_array_rank_diagnostics(plan),
            *self._raw_array_layout_diagnostics(plan),
            *self._raw_array_buffer_role_diagnostics(plan),
            *self._array_handoff_role_diagnostics(plan),
            *self._raw_array_itemsize_diagnostics(plan),
        )

    def _raw_array_rank_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one concrete supported raw-pointee rank and shape."""
        array = plan.array
        if array is None:
            return ()
        if array.rank is None or not 1 <= array.rank <= 15:
            return (self._diagnostic(plan.owner_path, "invalid-raw-array-rank", array.rank),)
        if len(array.shape) != array.rank or len(array.axes) != array.rank:
            return (self._diagnostic(plan.owner_path, "inconsistent-raw-array-rank", array.rank),)
        return ()

    def _raw_array_layout_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the completed dense raw-address category and orientation."""
        array = plan.array
        if array is None:
            return ()
        diagnostics = []
        if array.category != "raw_address":
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-raw-array-category", array.category))
        if array.order not in {None, "ORDER_F", "ORDER_C"}:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-raw-array-order", array.order))
        if array.contiguous is not True or any(axis != "dense" for axis in array.axes):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-raw-array-layout", array.axes))
        return tuple(diagnostics)

    def _raw_array_buffer_role_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Forbid NumPy-buffer ABI roles on an opaque raw address."""
        array = plan.array
        if array is None:
            return ()
        buffer_roles = (
            *array.extent_roles,
            *array.upper_bound_roles,
            *array.stride_roles,
            array.dense_actual_role,
            array.runtime_rank_role,
            array.itemsize_role,
        )
        if any(role is not None for role in buffer_roles):
            return (self._diagnostic(plan.owner_path, "unexpected-raw-array-buffer-roles", None),)
        return ()

    def _raw_array_itemsize_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require fixed itemsize only for raw character-array pointees."""
        array = plan.array
        if array is None:
            return ()
        if plan.datatype_family is DatatypeFamily.STRING:
            if array.itemsize is None or array.itemsize <= 0:
                return (self._diagnostic(plan.owner_path, "invalid-raw-character-array-itemsize", None),)
            return ()
        if array.itemsize is not None:
            return (self._diagnostic(plan.owner_path, "unexpected-raw-array-itemsize", array.itemsize),)
        return ()

    def _array_handoff_role_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate ordinary-array data, extent, and shape-reference roles."""
        array = plan.array
        if array is None:
            return ()
        return (
            *self._array_data_role_diagnostics(plan, array),
            *self._array_axis_role_diagnostics(
                plan.owner_path,
                array,
                array.extent_reference_tokens,
                array.extent_reference_roles,
                "invalid-array-extent-token-count",
                "invalid-array-extent-reference-count",
                "inconsistent-array-extent-references",
            ),
            *self._array_axis_role_diagnostics(
                plan.owner_path,
                array,
                array.extent_callable_tokens,
                array.extent_callable_roles,
                "invalid-array-extent-callable-token-count",
                "invalid-array-extent-callable-count",
                "inconsistent-array-extent-callables",
            ),
            *self._array_extent_evaluation_diagnostics(plan.owner_path, array),
        )

    def _array_data_role_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        array: ArrayHandoffPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the primary data role and nonempty extent producers."""
        diagnostics = []
        if array.data_role != plan.entrypoint.handoff_role:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-array-data-role", array.data_role))
        if any(not role for role in array.extent_roles):
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-array-extent-role", array.extent_roles))
        return tuple(diagnostics)

    def _array_axis_role_diagnostics(
        self,
        owner_path: str,
        array: ArrayHandoffPlan,
        tokens: tuple[tuple[str, ...], ...],
        roles: tuple[tuple[str, ...], ...],
        token_count_code: str,
        role_count_code: str,
        alignment_code: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one per-axis token and symbolic-role mapping."""
        diagnostics = []
        axis_count = len(array.shape)
        if len(roles) != axis_count:
            diagnostics.append(self._diagnostic(owner_path, role_count_code, roles))
        if len(tokens) != axis_count:
            diagnostics.append(self._diagnostic(owner_path, token_count_code, tokens))
        elif len(roles) == axis_count and not self._array_axis_roles_align(tokens, roles, axis_count):
            diagnostics.append(self._diagnostic(owner_path, alignment_code, tokens))
        return tuple(diagnostics)

    def _array_extent_evaluation_diagnostics(
        self,
        owner_path: str,
        array: ArrayHandoffPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require each axis to name the backend that can evaluate its extent."""
        if len(array.extent_evaluation) != len(array.shape) or any(
            evaluation not in {"binding", "bridge"} for evaluation in array.extent_evaluation
        ):
            return (self._diagnostic(owner_path, "invalid-array-extent-evaluation", array.extent_evaluation),)
        if len(array.extent_callable_roles) == len(array.shape) and any(
            (evaluation == "bridge") != bool(callables)
            for evaluation, callables in zip(array.extent_evaluation, array.extent_callable_roles, strict=True)
        ):
            return (self._diagnostic(owner_path, "inconsistent-array-extent-evaluation", array.extent_evaluation),)
        return ()

    @staticmethod
    def _array_axis_roles_align(
        tokens: tuple[tuple[str, ...], ...],
        roles: tuple[tuple[str, ...], ...],
        axis_count: int,
    ) -> bool:
        """Return whether every axis has aligned expression tokens and roles."""
        if len(tokens) != axis_count or len(roles) != axis_count:
            return False
        return all(len(axis_tokens) == len(axis_roles) for axis_tokens, axis_roles in zip(tokens, roles, strict=True))

    def _array_itemsize_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate fixed-width character itemsize fields only on character arrays."""
        array = plan.array
        if array is None:
            return ()
        if plan.datatype_family is DatatypeFamily.STRING:
            # The role is mandatory because the runtime width always crosses;
            # the literal is optional, because a contract may leave it assumed.
            if array.itemsize_role is None or (array.itemsize is not None and array.itemsize <= 0):
                return (self._diagnostic(plan.owner_path, "invalid-array-itemsize", array.itemsize),)
            return ()
        if array.itemsize is not None or array.itemsize_role is not None:
            return (self._diagnostic(plan.owner_path, "unexpected-array-itemsize", array.itemsize),)
        return ()

    def _concrete_rank_array_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate fixed-rank shape and layout facts."""
        array = plan.array
        if array is None or array.rank is None:
            return ()
        diagnostics = []
        if not 1 <= array.rank <= 15 and not self._is_scalar_storage_array(array):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-array-rank", array.rank))
        if len(array.shape) != array.rank or len(array.axes) != array.rank:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-array-rank", array.rank))
        if len(array.extent_roles) != array.rank or array.runtime_rank_role is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-array-rank-roles", array.extent_roles))
        return tuple(diagnostics)

    def _assumed_rank_array_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the one-through-fifteen runtime-rank ABI."""
        array = plan.array
        if array is None or array.rank is not None:
            return ()
        diagnostics = []
        if array.category != "assumed_rank" or array.shape != ("...",):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-assumed-rank-array", array.shape))
        if len(array.extent_roles) != 15 or array.runtime_rank_role is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-assumed-rank-roles", array.extent_roles))
        return tuple(diagnostics)

    def _array_layout_role_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate dense versus stride-aware ABI fields."""
        array = plan.array
        if array is None:
            return ()
        return (
            *self._array_order_diagnostics(plan),
            *self._array_axis_mode_diagnostics(plan),
            *self._array_stride_role_diagnostics(plan),
            *self._array_dense_actual_role_diagnostics(plan),
        )

    def _array_dense_actual_role_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the planned runtime selector exactly on concrete strided inputs."""
        array = plan.array
        if array is None:
            return ()
        expected = f"{plan.owner_path}:dense-actual" if array.contiguous is False and array.rank is not None else None
        if array.dense_actual_role != expected:
            return (self._diagnostic(plan.owner_path, "invalid-array-dense-actual-role", array.dense_actual_role),)
        return ()

    def _array_order_diagnostics(self, plan: ArgumentTransferPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the completed ordinary-array order marker."""
        array = plan.array
        if array is None:
            return ()
        diagnostics = []
        if array.order not in {None, "ORDER_F", "ORDER_C"}:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-array-order", array.order))
        if array.native_order not in {None, "ORDER_F", "ORDER_C"}:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-native-array-order", array.native_order))
        return tuple(diagnostics)

    def _array_axis_mode_diagnostics(self, plan: ArgumentTransferPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate dense versus stride-aware axis markers."""
        array = plan.array
        if array is None:
            return ()
        if array.order not in {None, "ORDER_F", "ORDER_C"}:
            return ()
        if array.contiguous not in {True, False}:
            return (self._diagnostic(plan.owner_path, "invalid-array-contiguity", array.contiguous),)
        if array.contiguous is True and any(axis != "dense" for axis in array.axes):
            return (self._diagnostic(plan.owner_path, "invalid-array-axis-modes", array.axes),)
        if array.contiguous is False and "strided" not in array.axes:
            return (self._diagnostic(plan.owner_path, "invalid-array-axis-modes", array.axes),)
        return ()

    def _array_stride_role_diagnostics(self, plan: ArgumentTransferPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate stride metadata presence or absence from completed contiguity."""
        array = plan.array
        if array is None:
            return ()
        if array.contiguous is False:
            return (
                *self._required_array_stride_role_diagnostics(plan),
                *self._array_stride_role_count_diagnostics(plan),
            )
        if array.upper_bound_roles or array.stride_roles:
            return (self._diagnostic(plan.owner_path, "unexpected-dense-array-stride-roles", None),)
        return ()

    def _required_array_stride_role_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require positive-stride metadata and a Fortran-oriented layout."""
        array = plan.array
        if array is not None and (array.order == "ORDER_C" or not array.upper_bound_roles or not array.stride_roles):
            return (self._diagnostic(plan.owner_path, "invalid-strided-array-layout", array.order),)
        return ()

    def _array_stride_role_count_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one upper bound and element stride per array extent."""
        array = plan.array
        if array is None:
            return ()
        diagnostics = []
        if len(array.upper_bound_roles) != len(array.extent_roles):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-array-upper-bound-roles", None))
        if len(array.stride_roles) != len(array.extent_roles):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-array-stride-roles", None))
        return tuple(diagnostics)

    # String argument validation.
    def _string_boundary_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Dispatch completed string-value, storage, or raw-address validation."""
        if plan.datatype_family is not DatatypeFamily.STRING:
            return (
                self._diagnostic(
                    plan.owner_path,
                    "invalid-string-datatype-family",
                    plan.datatype_family.value,
                ),
            )
        action = plan.binding.python_action
        if action is PythonBarrierAction.STRING_VALUE:
            return (*self._string_value_action_diagnostics(plan), *self._string_length_diagnostics(plan))
        if action is PythonBarrierAction.STRING_STORAGE:
            return self._string_address_diagnostics(
                plan,
                native_action=NativeBarrierAction.PASS_STORAGE_ADDRESS,
                storage_mode=StorageMode.ALIAS,
                copy_reason=STRING_STORAGE_COPY_REASON,
                label="storage",
            )
        if action is PythonBarrierAction.RAW_ADDRESS:
            return self._string_address_diagnostics(
                plan,
                native_action=NativeBarrierAction.PASS_RAW_ADDRESS,
                storage_mode=StorageMode.STACK,
                copy_reason=RAW_STRING_ADDRESS_COPY_REASON,
                label="raw-address",
            )
        return (self._diagnostic(plan.owner_path, "invalid-string-python-action", action.value),)

    def _string_value_action_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return action, handoff, and presence diagnostics for one string input."""
        diagnostics = []
        if plan.binding.python_action is not PythonBarrierAction.STRING_VALUE:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-string-python-action", plan.binding.python_action.value)
            )
        if plan.bridge.native_action is not NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-string-native-action", plan.bridge.native_action.value)
            )
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-string-handoff", plan.entrypoint.handoff_mode.value)
            )
        if plan.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-string-data-action", plan.bridge.data_action.value)
            )
        if plan.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.NULLABLE_VALUE}:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-string-optional-mode",
                    plan.binding.optional_mode.value,
                )
            )
        diagnostics.extend(self._string_codegen_diagnostics(plan))
        return tuple(diagnostics)

    def _string_address_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        *,
        native_action: NativeBarrierAction,
        storage_mode: StorageMode,
        copy_reason: str,
        label: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one fixed string storage/raw address plan."""
        diagnostics = list(
            self._string_address_ownership_diagnostics(
                plan,
                storage_mode=storage_mode,
                label=label,
            )
        )
        if plan.bridge.native_action is not native_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path, f"invalid-string-{label}-native-action", plan.bridge.native_action.value
                )
            )
        if plan.entrypoint.handoff_mode is not ArgumentHandoffMode.OPAQUE_ADDRESS:
            diagnostics.append(
                self._diagnostic(plan.owner_path, f"invalid-string-{label}-handoff", plan.entrypoint.handoff_mode.value)
            )
        if plan.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
            diagnostics.append(
                self._diagnostic(plan.owner_path, f"invalid-string-{label}-data-action", plan.bridge.data_action.value)
            )
        if plan.bridge.copy_reason != copy_reason:
            diagnostics.append(
                self._diagnostic(plan.owner_path, f"invalid-string-{label}-copy-reason", plan.bridge.copy_reason)
            )
        diagnostics.extend(self._string_address_length_diagnostics(plan, label))
        return tuple(diagnostics)

    def _string_address_ownership_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        *,
        storage_mode: StorageMode,
        label: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed caller-owned in-place string address facts."""
        expected = (
            ("object-kind", plan.object_kind, ObjectKind.STRING),
            ("owner", plan.ownership_owner, OwnershipOwner.CALLER),
            ("transfer", plan.transfer_mode, TransferMode.IN_PLACE),
            ("destruction", plan.destruction_policy, DestructionPolicy.CALLER),
            ("storage", plan.storage_mode, storage_mode),
            ("boundary-storage", plan.boundary_storage_mode, storage_mode),
        )
        diagnostics = [
            self._diagnostic(plan.owner_path, f"invalid-string-{label}-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        ]
        if plan.binding.codegen_action is not CodegenAction.IN_PLACE_ARGUMENT:
            diagnostics.append(
                self._diagnostic(plan.owner_path, f"invalid-string-{label}-action", plan.binding.codegen_action.value)
            )
        if not plan.mutates_native:
            diagnostics.append(self._diagnostic(plan.owner_path, f"string-{label}-without-mutation", False))
        if plan.projects_result:
            diagnostics.append(
                self._diagnostic(plan.owner_path, f"string-{label}-projects-result", plan.result_position)
            )
        if plan.nullable or plan.binding.optional_mode is not OptionalMode.REQUIRED:
            diagnostics.append(
                self._diagnostic(plan.owner_path, f"optional-string-{label}", plan.binding.optional_mode.value)
            )
        return tuple(diagnostics)

    def _string_address_length_diagnostics(
        self,
        plan: ArgumentTransferPlan,
        label: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require a plan length and prohibit a runtime length ABI role.

        Assumed-capacity rank-zero storage states no width, so the plan instead
        records that the caller's itemsize travels beside the address.
        """
        diagnostics = []
        assumed_capacity = plan.character_length is None and plan.entrypoint.pass_character_length
        if not assumed_capacity and (plan.character_length is None or plan.character_length <= 0):
            diagnostics.append(
                self._diagnostic(plan.owner_path, f"invalid-string-{label}-length", plan.character_length)
            )
        if plan.entrypoint.length_handoff_role is not None:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    f"unexpected-string-{label}-length-handoff",
                    plan.entrypoint.length_handoff_role,
                )
            )
        return tuple(diagnostics)

    def _string_codegen_diagnostics(self, plan: ArgumentTransferPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return string action, copy-reason, and replacement diagnostics."""
        diagnostics = []
        action = plan.binding.codegen_action
        if action not in {CodegenAction.CALL_LOCAL_INPUT, CodegenAction.COPY_IN_OUT}:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-string-codegen-action", action.value))
        expected_reason = (
            STRING_REPLACEMENT_COPY_REASON if action is CodegenAction.COPY_IN_OUT else STRING_INPUT_COPY_REASON
        )
        if plan.bridge.copy_reason != expected_reason:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-string-copy-reason", plan.bridge.copy_reason))
        if action is CodegenAction.COPY_IN_OUT:
            diagnostics.extend(self._string_replacement_diagnostics(plan))
        elif plan.projects_result and not plan.projects_character_descriptor_update:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "call-local-string-projects-result", plan.result_position)
            )
        return tuple(diagnostics)

    def _string_replacement_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed ownership and projection for one string replacement."""
        expected = (
            ("object-kind", plan.object_kind, ObjectKind.STRING),
            ("owner", plan.ownership_owner, OwnershipOwner.PYTHON),
            ("transfer", plan.transfer_mode, TransferMode.COPY_RETURN),
            ("destruction", plan.destruction_policy, DestructionPolicy.PYTHON_REFCOUNT),
            ("storage", plan.storage_mode, StorageMode.STACK),
            ("boundary-storage", plan.boundary_storage_mode, StorageMode.STACK),
        )
        diagnostics = [
            self._diagnostic(plan.owner_path, f"invalid-string-replacement-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        ]
        if not plan.projects_result or plan.result_position is None:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "string-replacement-without-result", plan.result_position)
            )
        if plan.nullable and plan.binding.optional_mode is OptionalMode.REQUIRED:
            diagnostics.append(self._diagnostic(plan.owner_path, "nullable-string-replacement", True))
        return tuple(diagnostics)

    def _string_length_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return payload-length handoff and fixed-length diagnostics."""
        diagnostics = []
        length_role = plan.entrypoint.length_handoff_role
        if length_role is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-string-length-handoff", None))
        if plan.projected_call_slot.character_length is not None and plan.projected_call_slot.character_length <= 0:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-string-character-length",
                    plan.projected_call_slot.character_length,
                )
            )
        if plan.character_length is not None and plan.character_length <= 0:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-argument-character-length", plan.character_length)
            )
        return tuple(diagnostics)

    def _optional_argument_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return presence-mode and descriptor handoff diagnostics."""
        return (
            *self._optional_presence_diagnostics(plan),
            *self._optional_native_diagnostics(plan),
            *self._descriptor_output_role_diagnostics(plan),
        )

    def _descriptor_output_role_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require copy-out roles exactly for projected required descriptors."""
        roles = (plan.entrypoint.descriptor_output_role, plan.entrypoint.descriptor_output_presence_role)
        expected = plan.binding.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR and plan.projects_result
        if expected and any(role is None for role in roles):
            return (self._diagnostic(plan.owner_path, "missing-required-descriptor-output-role", roles),)
        if not expected and any(role is not None for role in roles):
            return (self._diagnostic(plan.owner_path, "unexpected-descriptor-output-role", roles),)
        return ()

    def _optional_presence_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return cross-view presence and descriptor diagnostics."""
        diagnostics = []
        mode = plan.binding.optional_mode
        if plan.entrypoint.optional_mode is not mode:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-optional-mode", mode.value))
        if plan.native_array_handle is not None:
            if not plan.binding.descriptor_boundary:
                diagnostics.append(self._diagnostic(plan.owner_path, "missing-native-descriptor-boundary", mode.value))
            expected_presence = plan.native_array_handle.handoff.presence_role
            if plan.entrypoint.presence_role != expected_presence:
                diagnostics.append(
                    self._diagnostic(plan.owner_path, "inconsistent-native-descriptor-presence-role", expected_presence)
                )
            return tuple(diagnostics)
        descriptor_mode = mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}
        if plan.binding.descriptor_boundary != descriptor_mode:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-descriptor-boundary", mode.value))
        if mode is OptionalMode.DESCRIPTOR and plan.entrypoint.presence_role is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-descriptor-presence-role", mode.value))
        if mode is not OptionalMode.DESCRIPTOR and plan.entrypoint.presence_role is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "unexpected-descriptor-presence-role", mode.value))
        return tuple(diagnostics)

    def _optional_native_diagnostics(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return optional native-action and descriptor-kind diagnostics."""
        diagnostics = []
        mode = plan.binding.optional_mode
        descriptor_mode = mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}
        if mode is not OptionalMode.REQUIRED and plan.bridge.native_action not in {
            NativeBarrierAction.PASS_VALUE,
            NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
            NativeBarrierAction.PASS_STORAGE_ADDRESS,
            NativeBarrierAction.PASS_ARRAY_BUFFER,
            NativeBarrierAction.PASS_NATIVE_DESCRIPTOR,
            NativeBarrierAction.PASS_WRAPPER_ADDRESS,
        }:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-optional-native-action", plan.bridge.native_action.value)
            )
        if descriptor_mode and plan.projected_call_slot.value_kind not in {"allocatable", "pointer"}:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-descriptor-value-kind", plan.projected_call_slot.value_kind)
            )
        return tuple(diagnostics)

    # Result validation: general result graph, then typed result families.
    def _result_diagnostics(
        self,
        plan: ResultPlan,
        function_slots: dict[int, NativeEntrypointProjectedSlotPlan],
        available_roles: tuple[str, ...],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return direct or hidden result producer/consumer diagnostics."""
        diagnostics = list(self._result_role_diagnostics(plan, available_roles))
        diagnostics.extend(
            self._bridge_data_diagnostics(
                plan.owner_path,
                plan.bridge.data_action,
                plan.bridge.copy_reason,
            )
        )
        if plan.bridge.codegen_action is not plan.binding.codegen_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-result-codegen-action",
                    plan.bridge.codegen_action,
                )
            )
        if plan.updates_argument:
            diagnostics.extend(self._update_result_diagnostics(plan, function_slots))
        elif plan.source_kind == "direct_return":
            diagnostics.extend(self._direct_result_diagnostics(plan))
        elif plan.source_kind == "hidden_output":
            diagnostics.extend(self._hidden_result_diagnostics(plan, function_slots))
        else:
            diagnostics.append(self._diagnostic(plan.owner_path, "unknown-result-source", plan.source_kind))
        diagnostics.extend(self._direct_result_abi_diagnostics(plan))
        diagnostics.extend(self._result_family_diagnostics(plan))
        if plan.array is not None:
            diagnostics.extend(self._array_extent_reference_diagnostics(plan, available_roles))
        return tuple(diagnostics)

    def _direct_result_abi_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the completed direct scalar ABI without selecting lowering."""
        expected = DirectResultABI.NOT_APPLICABLE
        if (
            plan.source_kind == "direct_return"
            and plan.object_kind is ObjectKind.SCALAR
            and plan.scalar_descriptor is None
        ):
            expected = (
                DirectResultABI.LOGICAL_LOW_BIT_INT8
                if plan.datatype_family is DatatypeFamily.BOOL
                else DirectResultABI.NATIVE_SCALAR
            )
        if plan.entrypoint.direct_result_abi is expected:
            return ()
        return (
            self._diagnostic(
                plan.owner_path,
                "invalid-direct-result-abi",
                f"{plan.entrypoint.direct_result_abi.value}; expected {expected.value}",
            ),
        )

    def _result_family_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Dispatch one result from its completed object-kind decision."""
        if plan.scalar_descriptor is not None:
            return self._scalar_descriptor_result_diagnostics(plan)
        match plan.object_kind:
            case ObjectKind.SCALAR:
                diagnostics = list(self._nonstring_result_length_diagnostics(plan))
                if plan.array is not None:
                    diagnostics.append(self._diagnostic(plan.owner_path, "unexpected-scalar-result-array", None))
                if plan.datatype_family is DatatypeFamily.STRING:
                    diagnostics.append(
                        self._diagnostic(
                            plan.owner_path,
                            "invalid-scalar-result-datatype-family",
                            plan.datatype_family.value,
                        )
                    )
                return tuple(diagnostics)
            case ObjectKind.STRING:
                if plan.array is not None:
                    return (self._diagnostic(plan.owner_path, "unexpected-string-result-array", None),)
                return self._string_result_diagnostics(plan)
            case ObjectKind.NUMPY_ARRAY:
                return self._array_result_diagnostics(plan)
            case ObjectKind.DERIVED_TYPE:
                return self._derived_result_diagnostics(plan)
            case _:
                return (
                    self._diagnostic(
                        plan.owner_path,
                        "unsupported-result-object-kind",
                        plan.object_kind.value,
                    ),
                )

    # Derived-type result validation.
    def _derived_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate persistent wrapper-owned derived result policy."""
        diagnostics = []
        if plan.datatype_family is not DatatypeFamily.DERIVED:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-result-family", plan.datatype_family))
        if plan.derived is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-derived-result-handoff", None))
        else:
            diagnostics.extend(self._derived_handoff_identity_diagnostics(plan.owner_path, plan.derived))
            if plan.derived.origin is not DerivedObjectOrigin.WRAPPER_RESULT:
                diagnostics.append(
                    self._diagnostic(plan.owner_path, "invalid-derived-result-origin", plan.derived.origin)
                )
        if plan.binding.codegen_action is not CodegenAction.WRAPPER_INSTANCE:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-derived-result-action", plan.binding.codegen_action)
            )
        if plan.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-derived-result-data-action", plan.bridge.data_action)
            )
        if plan.array is not None or plan.native_array_handle is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "derived-result-has-array-policy", None))
        if plan.projected_call_slot is not None and plan.projected_call_slot.derived is not plan.derived:
            diagnostics.append(self._diagnostic(plan.owner_path, "unshared-derived-result-handoff", None))
        return tuple(diagnostics)

    # Rank-zero scalar/string descriptor result validation.
    def _scalar_descriptor_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one nullable rank-zero descriptor copy contract."""
        descriptor = plan.scalar_descriptor
        if descriptor is None:
            return ()
        return (
            *self._scalar_descriptor_family_diagnostics(plan),
            *self._scalar_descriptor_ownership_diagnostics(plan),
            *self._scalar_descriptor_copy_diagnostics(plan),
            *self._scalar_descriptor_source_diagnostics(plan),
        )

    def _scalar_descriptor_family_diagnostics(
        self,
        plan: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate scalar/string family and runtime-length selection."""
        descriptor = plan.scalar_descriptor
        if descriptor is None:
            return ()
        diagnostics = []
        if plan.object_kind not in {ObjectKind.SCALAR, ObjectKind.STRING}:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-descriptor-object-kind", plan.object_kind)
            )
        if plan.array is not None or plan.native_array_handle is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "scalar-descriptor-has-array-policy", None))
        if descriptor.runtime_length != (plan.object_kind is ObjectKind.STRING):
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-descriptor-runtime-length", descriptor.runtime_length)
            )
        return tuple(diagnostics)

    def _scalar_descriptor_ownership_diagnostics(
        self,
        plan: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate nullability, Python release, and presence role."""
        descriptor = plan.scalar_descriptor
        if descriptor is None:
            return ()
        diagnostics = []
        if not descriptor.nullable or not plan.nullable:
            diagnostics.append(self._diagnostic(plan.owner_path, "nonnullable-scalar-descriptor-result", None))
        if descriptor.release_owner is not OwnershipOwner.PYTHON:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-descriptor-release-owner", descriptor.release_owner)
            )
        if descriptor.presence_role != f"{plan.owner_path}:present":
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-descriptor-presence-role", descriptor.presence_role)
            )
        return tuple(diagnostics)

    def _scalar_descriptor_copy_diagnostics(
        self,
        plan: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the one explicit representation-copy reason and action."""
        descriptor = plan.scalar_descriptor
        if descriptor is None:
            return ()
        diagnostics = []
        if descriptor.copy_reason != SCALAR_DESCRIPTOR_RESULT_COPY_REASON:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-descriptor-copy-reason", descriptor.copy_reason)
            )
        if plan.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-scalar-descriptor-data-action", plan.bridge.data_action)
            )
        if plan.bridge.copy_reason != descriptor.copy_reason:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-scalar-descriptor-copy-reason", plan.bridge.copy_reason)
            )
        return tuple(diagnostics)

    def _scalar_descriptor_source_diagnostics(
        self,
        plan: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate exact hidden-slot sharing or direct-result independence.

        An argument update shares the Python-visible input's slot, which carries
        that input's own handoff rather than a descriptor, so its descriptor is
        owned by the result record alone.
        """
        descriptor = plan.scalar_descriptor
        if descriptor is None:
            return ()
        if plan.updates_argument:
            if plan.projected_call_slot is None or plan.projected_call_slot.scalar_descriptor is not None:
                return (self._diagnostic(plan.owner_path, "inconsistent-update-descriptor-native-slot", None),)
            return ()
        if plan.source_kind == "hidden_output":
            if plan.projected_call_slot is None or plan.projected_call_slot.scalar_descriptor is not descriptor:
                return (self._diagnostic(plan.owner_path, "inconsistent-scalar-descriptor-native-slot", None),)
        elif plan.projected_call_slot is not None:
            return (self._diagnostic(plan.owner_path, "direct-scalar-descriptor-has-slot", None),)
        return ()

    # Fixed-string result validation.
    def _string_result_aggregation_diagnostics(
        self,
        plan: FunctionPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Mixed fixed strings use the same ordered output aggregation path."""
        return ()

    def _string_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the fixed string result contract before either backend."""
        if plan.datatype_family is not DatatypeFamily.STRING:
            return (
                self._diagnostic(
                    plan.owner_path,
                    "invalid-string-result-datatype-family",
                    plan.datatype_family.value,
                ),
            )
        diagnostics = []
        if plan.character_length is None or plan.character_length <= 0:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-result-character-length", plan.character_length)
            )
        diagnostics.extend(self._string_result_ownership_diagnostics(plan))
        if plan.binding.python_action is not PythonBarrierAction.NONE:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path, "invalid-string-result-python-action", plan.binding.python_action.value
                )
            )
        if plan.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-string-result-data-action", plan.bridge.data_action.value)
            )
        if plan.bridge.copy_reason != FIXED_STRING_RESULT_COPY_REASON:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-string-result-copy-reason", plan.bridge.copy_reason)
            )
        if plan.source_kind == "direct_return":
            diagnostics.extend(self._direct_string_result_diagnostics(plan))
        elif plan.source_kind == "hidden_output":
            diagnostics.extend(self._hidden_string_result_diagnostics(plan))
        return tuple(diagnostics)

    def _string_result_ownership_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed fixed-string ownership projected into the plan."""
        expected = (
            ("object-kind", plan.object_kind, ObjectKind.STRING),
            ("owner", plan.ownership_owner, OwnershipOwner.PYTHON),
            ("transfer", plan.transfer_mode, TransferMode.COPY_RETURN),
            ("destruction", plan.destruction_policy, DestructionPolicy.PYTHON_REFCOUNT),
            ("storage", plan.storage_mode, StorageMode.STACK),
            ("boundary-storage", plan.boundary_storage_mode, StorageMode.STACK),
        )
        diagnostics = [
            self._diagnostic(plan.owner_path, f"invalid-string-result-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        ]
        if plan.nullable and plan.source_kind != "hidden_output":
            diagnostics.append(self._diagnostic(plan.owner_path, "nullable-fixed-string-result", plan.nullable))
        return tuple(diagnostics)

    def _nonstring_result_length_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject a character length copied onto a non-string result plan.

        ``None`` is the only valid non-string value.  The returned diagnostic
        captures projection drift without reclassifying the result family.
        """
        if plan.character_length is None:
            return ()
        return (
            self._diagnostic(
                plan.owner_path,
                "nonstring-result-character-length",
                plan.character_length,
            ),
        )

    def _direct_string_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the direct-return fixed-string actions already in the plan.

        Direct strings copy into Python without a native output address.  This
        helper only compares those two stored actions and returns diagnostics
        in the function result's established order.
        """
        diagnostics = []
        if plan.binding.codegen_action is not CodegenAction.COPY_OUT:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-direct-string-result-action",
                    plan.binding.codegen_action.value,
                )
            )
        if plan.bridge.native_action is not NativeBarrierAction.NONE:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-direct-string-native-action",
                    plan.bridge.native_action.value,
                )
            )
        return tuple(diagnostics)

    def _hidden_string_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the hidden-output fixed-string actions already in the plan.

        Hidden strings copy into Python and cross the native boundary through
        their call-local address.  The helper reports mismatches but does not
        allocate or replace the missing slot.
        """
        diagnostics = []
        if plan.binding.codegen_action is not CodegenAction.COPY_OUT:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-hidden-string-result-action",
                    plan.binding.codegen_action.value,
                )
            )
        if plan.bridge.native_action is not NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-hidden-string-native-action",
                    plan.bridge.native_action.value,
                )
            )
        return tuple(diagnostics)

    def _result_role_diagnostics(
        self,
        plan: ResultPlan,
        available_roles: tuple[str, ...],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require a result's native producer role to be advertised by its function.

        ``available_roles`` is the function-wide role list already projected
        by planning.  The returned diagnostic identifies a consumer whose
        stored producer is unavailable; no role is added here.
        """
        if plan.entrypoint.native_result_role not in available_roles:
            return (self._diagnostic(plan.owner_path, "unavailable-result-role", plan.entrypoint.native_result_role),)
        return ()

    def _direct_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate a direct result's absence of slots and data-action choice.

        Direct results must not own a native call slot or ABI position.  Their
        stored object kind and descriptor state determine the required
        completed bridge action, which is compared without altering the plan.
        """
        diagnostics = []
        if plan.projected_call_slot is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "direct-result-has-native-slot", plan.source_kind))
        expected_data_action = (
            BridgeDataAction.COPY_REPRESENTATION
            if plan.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}
            or plan.scalar_descriptor is not None
            else BridgeDataAction.DIRECT_TRANSFER
        )
        if plan.bridge.data_action is not expected_data_action:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-direct-result-data-action", plan.bridge.data_action.value)
            )
        return tuple(diagnostics)

    def _update_result_diagnostics(
        self,
        plan: ResultPlan,
        function_slots: dict[int, NativeEntrypointProjectedSlotPlan],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one result that returns a Python-visible argument's new value.

        Unlike a hidden output, this result has no native slot of its own: it
        shares the input slot of the argument it updates, and that slot describes
        the input handoff.  The checks therefore require the shared slot to be
        that Python argument's slot at the same result position, and require the
        descriptor that carries the reallocated storage to be present.  Its
        pairing with a descriptor character input is validated once per
        function by :meth:`_argument_update_diagnostics`.
        """
        slot = plan.projected_call_slot
        if slot is None:
            return (self._diagnostic(plan.owner_path, "missing-update-result-native-slot", None),)
        diagnostics = []
        if slot.source_kind == "result" or slot.python_position is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-update-result-native-slot", slot.source_kind))
        if slot.result_position != plan.result_position:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-result-position", slot.result_position))
        if function_slots.get(slot.native_position) is not slot:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-function-result-slot", slot.native_position)
            )
        if plan.scalar_descriptor is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-update-result-descriptor", None))
        if plan.bridge is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-update-result-adapter-facet", None))
        return tuple(diagnostics)

    def _hidden_result_diagnostics(
        self,
        plan: ResultPlan,
        function_slots: dict[int, NativeEntrypointProjectedSlotPlan],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate a hidden result's shared slot and function-wide registration.

        ``function_slots`` indexes the function's native slots by ABI position.
        A hidden result must reference the exact indexed slot and then satisfy
        its shape and completed-action checks.  Missing or mismatched records
        become diagnostics rather than replacement slots.
        """
        if plan.projected_call_slot is None:
            return (self._diagnostic(plan.owner_path, "missing-result-native-slot", plan.bridge.native_name),)
        slot = plan.projected_call_slot
        diagnostics = [
            *self._hidden_result_shape_diagnostics(plan, slot),
            *self._hidden_result_policy_consistency_diagnostics(plan, slot),
        ]
        if function_slots.get(slot.native_position) is not slot:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-function-result-slot", slot.native_position)
            )
        return tuple(diagnostics)

    def _hidden_result_shape_diagnostics(
        self,
        plan: ResultPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return hidden-result native-slot shape diagnostics."""
        diagnostics = []
        if slot.source_kind != "result":
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-result-native-slot", slot.source_kind))
        if slot.result_position != plan.result_position:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-result-position", slot.result_position))
        if slot.symbolic_role != plan.entrypoint.native_result_role:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-result-role", slot.symbolic_role))
        return tuple(diagnostics)

    def _hidden_result_policy_consistency_diagnostics(
        self,
        plan: ResultPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return hidden-result completed-action consistency diagnostics."""
        diagnostics = []
        adapter = slot.adapter
        if adapter is None:
            return (self._diagnostic(plan.owner_path, "missing-result-adapter-facet", None),)
        if adapter.native_action is not plan.bridge.native_action:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-result-native-action", adapter.native_action.value)
            )
        if adapter.codegen_action is not plan.bridge.codegen_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-result-slot-codegen-action",
                    adapter.codegen_action.value,
                )
            )
        if adapter.bridge_data_action is not plan.bridge.data_action:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-result-data-action",
                    adapter.bridge_data_action.value,
                )
            )
        if adapter.bridge_copy_reason != plan.bridge.copy_reason:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-result-copy-reason", adapter.bridge_copy_reason)
            )
        if slot.character_length != plan.character_length:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-result-character-length", slot.character_length)
            )
        if slot.array is not plan.array:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-result-array-handoff", slot.array))
        if slot.native_array_handle is not plan.native_array_handle:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-result-native-array-handle", slot.native_array_handle)
            )
        if slot.scalar_descriptor is not plan.scalar_descriptor:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "inconsistent-result-scalar-descriptor", slot.scalar_descriptor)
            )
        if slot.object_kind is not plan.object_kind:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "inconsistent-result-object-kind",
                    slot.object_kind,
                )
            )
        return tuple(diagnostics)

    # Ordinary-array result validation.
    def _array_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one fixed-shape ordinary array producer and copy consumer."""
        if plan.native_array_handle is not None:
            return self._native_array_handle_result_diagnostics(plan)
        array = plan.array
        if array is None:
            return (self._diagnostic(plan.owner_path, "missing-array-result-handoff", None),)
        diagnostics = [
            *self._array_result_ownership_diagnostics(plan),
            *self._array_result_shape_diagnostics(plan),
            *self._array_result_itemsize_diagnostics(plan),
            *self._array_result_copy_diagnostics(plan),
        ]
        if plan.nullable:
            diagnostics.append(self._diagnostic(plan.owner_path, "nullable-ordinary-array-result", plan.nullable))
        diagnostics.extend(self._array_result_source_diagnostics(plan))
        return tuple(diagnostics)

    # Native-array-handle result validation.
    def _native_array_handle_result_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one wrapper-owned native descriptor result."""
        handle = plan.native_array_handle
        if handle is None:
            return ()
        return (
            *self._native_array_handle_shape_diagnostics(plan.owner_path, handle),
            *self._native_descriptor_handoff_diagnostics(plan.owner_path, handle, None),
            *self._native_array_result_ownership_diagnostics(plan),
            *self._native_array_result_handle_diagnostics(plan),
            *self._native_array_result_copy_diagnostics(plan),
        )

    def _native_array_result_ownership_diagnostics(
        self,
        plan: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate wrapper ownership, storage, and public result actions."""
        expected = (
            ("owner", plan.ownership_owner, OwnershipOwner.WRAPPER),
            ("transfer", plan.transfer_mode, TransferMode.WRAPPER_INSTANCE),
            ("destruction", plan.destruction_policy, DestructionPolicy.WRAPPER_DEALLOC),
            ("storage", plan.storage_mode, StorageMode.HEAP),
            ("boundary-storage", plan.boundary_storage_mode, StorageMode.ALIAS),
            ("codegen-action", plan.binding.codegen_action, CodegenAction.WRAPPER_INSTANCE),
            ("python-action", plan.binding.python_action, PythonBarrierAction.NONE),
        )
        return tuple(
            self._diagnostic(plan.owner_path, f"invalid-native-array-result-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        )

    def _native_array_result_handle_diagnostics(
        self,
        plan: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate owned native descriptor handle identity and release policy."""
        handle = plan.native_array_handle
        if handle is None:
            return ()
        diagnostics = []
        if handle.handle_kind is not NativeArrayHandleKind.OWNED_RESULT_DESCRIPTOR:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-native-array-result-kind", handle.handle_kind)
            )
        if handle.descriptor_ownership is not NativeArrayDescriptorOwnership.OWNED or handle.borrowed:
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-native-array-result-ownership", None))
        if handle.release is not NativeArrayRelease.WRAPPER_DEALLOC:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-native-array-result-release", None))
        if plan.array is not handle.array:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-native-array-result-facet", plan.array))
        return tuple(diagnostics)

    def _native_array_result_copy_diagnostics(
        self,
        plan: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the ownership-transfer representation copy action."""
        diagnostics = []
        if plan.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-native-array-result-data-action", plan.bridge.data_action)
            )
        if plan.bridge.copy_reason != OWNED_NATIVE_ARRAY_HANDLE_COPY_REASON:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-native-array-result-copy-reason", plan.bridge.copy_reason)
            )
        return tuple(diagnostics)

    def _array_result_ownership_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate ordinary array result ownership and storage decisions."""
        expected = (
            ("object-kind", plan.object_kind, ObjectKind.NUMPY_ARRAY),
            ("owner", plan.ownership_owner, OwnershipOwner.PYTHON),
            ("transfer", plan.transfer_mode, TransferMode.COPY_RETURN),
            ("destruction", plan.destruction_policy, DestructionPolicy.PYTHON_REFCOUNT),
            ("storage", plan.storage_mode, StorageMode.STACK),
            ("boundary-storage", plan.boundary_storage_mode, StorageMode.STACK),
        )
        return tuple(
            self._diagnostic(plan.owner_path, f"invalid-array-result-{name}", actual.value)
            for name, actual, required in expected
            if actual is not required
        )

    def _array_result_itemsize_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate fixed-width character itemsize only inside the array family."""
        array = plan.array
        if array is None:
            return ()
        if plan.datatype_family is DatatypeFamily.STRING:
            if (
                array.itemsize is None
                or array.itemsize <= 0
                or array.itemsize_role is None
                or plan.character_length != array.itemsize
            ):
                return (self._diagnostic(plan.owner_path, "invalid-array-result-itemsize", array.itemsize),)
            return ()
        if array.itemsize is not None or array.itemsize_role is not None or plan.character_length is not None:
            return (self._diagnostic(plan.owner_path, "unexpected-array-result-itemsize", array.itemsize),)
        return ()

    def _array_result_shape_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate a fully resolved fixed-rank ordinary array result shape."""
        return (
            *self._array_result_rank_diagnostics(plan),
            *self._array_result_shape_count_diagnostics(plan),
            *self._array_result_extent_diagnostics(plan),
            *self._array_result_order_diagnostics(plan),
        )

    def _array_result_rank_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require a supported concrete ordinary array result rank."""
        array = plan.array
        if array is not None and (
            array.rank is None or (not 1 <= array.rank <= 15 and not self._is_scalar_storage_array(array))
        ):
            return (self._diagnostic(plan.owner_path, "invalid-array-result-rank", array.rank),)
        return ()

    def _array_result_shape_count_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one shape and extent role per result axis."""
        array = plan.array
        if array is None or array.rank is None:
            return ()
        if len(array.shape) != array.rank or len(array.extent_roles) != array.rank:
            return (self._diagnostic(plan.owner_path, "inconsistent-array-result-shape", array.shape),)
        if not self._array_axis_roles_align(
            array.extent_reference_tokens,
            array.extent_reference_roles,
            array.rank,
        ):
            return (self._diagnostic(plan.owner_path, "inconsistent-array-result-shape", array.shape),)
        if not self._array_axis_roles_align(
            array.extent_callable_tokens,
            array.extent_callable_roles,
            array.rank,
        ):
            return (self._diagnostic(plan.owner_path, "inconsistent-array-result-shape", array.shape),)
        if not self._array_extent_evaluation_is_consistent(array):
            return (self._diagnostic(plan.owner_path, "inconsistent-array-result-shape", array.shape),)
        return ()

    @staticmethod
    def _array_extent_evaluation_is_consistent(array: ArrayHandoffPlan) -> bool:
        """Return whether every axis uses bridge evaluation exactly for native calls."""
        if len(array.extent_evaluation) != len(array.shape):
            return False
        return all(
            evaluation in {"binding", "bridge"} and ((evaluation == "bridge") == bool(callables))
            for evaluation, callables in zip(
                array.extent_evaluation,
                array.extent_callable_roles,
                strict=True,
            )
        )

    def _array_result_extent_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject unresolved ordinary array result extent spellings."""
        array = plan.array
        if array is not None and any(shape in {":", "::Strided", "...", "Flat"} for shape in array.shape):
            return (self._diagnostic(plan.owner_path, "unresolved-array-result-shape", array.shape),)
        return ()

    def _array_result_order_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject multidimensional C-oriented native result copies."""
        array = plan.array
        if array is not None and array.order == "ORDER_C" and array.rank is not None and array.rank > 1:
            return (self._diagnostic(plan.owner_path, "invalid-array-result-order", array.order),)
        return ()

    def _array_result_copy_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the explicit ordinary array representation-copy decision."""
        diagnostics = []
        if plan.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-result-data-action", plan.bridge.data_action.value)
            )
        if plan.bridge.copy_reason != ORDINARY_ARRAY_RESULT_COPY_REASON:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-result-copy-reason", plan.bridge.copy_reason)
            )
        return tuple(diagnostics)

    def _array_result_source_diagnostics(self, plan: ResultPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate direct versus hidden ordinary array producer actions."""
        if plan.source_kind == "direct_return":
            expected_action = CodegenAction.COPY_OUT
            expected_native = NativeBarrierAction.NONE
        else:
            expected_action = CodegenAction.COPY_OUT
            expected_native = (
                NativeBarrierAction.PASS_STORAGE_ADDRESS
                if self._is_scalar_storage_array(plan.array)
                else NativeBarrierAction.PASS_ARRAY_BUFFER
            )
        diagnostics = []
        if plan.binding.codegen_action is not expected_action:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-result-action", plan.binding.codegen_action.value)
            )
        if plan.bridge.native_action is not expected_native:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-array-result-native-action", plan.bridge.native_action.value)
            )
        return tuple(diagnostics)

    @staticmethod
    def _is_scalar_storage_array(array) -> bool:
        """Return whether an array facet denotes rank-zero scalar storage.

        The predicate is shared by argument and result validation to select
        only already-planned scalar-storage rules.  ``None`` and all other
        array categories return ``False`` without mutation.
        """
        return bool(array is not None and array.rank == 0 and array.category == SCALAR_STORAGE_CATEGORY)

    # Native-call-slot and generic lifecycle validation.
    def _native_slot_diagnostics(
        self,
        plan: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return hidden literal and hidden result slot diagnostics."""
        adapter = plan.adapter
        if adapter is None:
            return (self._diagnostic(plan.owner_path, "missing-native-slot-adapter-facet", None),)
        diagnostics = list(
            self._bridge_data_diagnostics(
                plan.owner_path,
                adapter.bridge_data_action,
                adapter.bridge_copy_reason,
            )
        )
        if plan.source_kind not in {"implicit", "projection", "literal", "computed", "work", "result"}:
            diagnostics.append(self._diagnostic(plan.owner_path, "unknown-native-slot-source", plan.source_kind))
        if plan.source_kind == "literal":
            diagnostics.extend(self._literal_slot_diagnostics(plan))
        elif plan.source_kind in {"computed", "work"}:
            if plan.semantic_type_name is None:
                diagnostics.append(self._diagnostic(plan.owner_path, "missing-computed-slot-type", None))
        elif plan.object_kind is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-native-slot-object-kind", None))
        if plan.source_kind == "result":
            diagnostics.extend(self._result_slot_diagnostics(plan))
        return tuple(diagnostics)

    def _bridge_data_diagnostics(
        self,
        owner_path: str,
        action: BridgeDataAction,
        copy_reason: str | None,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Reject uncompleted or unjustified bridge-side data movement."""
        if action is BridgeDataAction.BLOCKED:
            return (self._diagnostic(owner_path, "blocked-bridge-data-action", action.value),)
        if action is BridgeDataAction.COPY_REPRESENTATION:
            if not copy_reason or not copy_reason.strip():
                return (self._diagnostic(owner_path, "missing-bridge-copy-reason", action.value),)
            return ()
        if copy_reason is not None:
            return (self._diagnostic(owner_path, "unexpected-bridge-copy-reason", action.value),)
        return ()

    def _literal_slot_diagnostics(
        self,
        plan: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return diagnostics for one hidden literal slot."""
        diagnostics = []
        adapter = plan.adapter
        if adapter is None:
            return (self._diagnostic(plan.owner_path, "missing-literal-adapter-facet", None),)
        if plan.literal_type is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-literal-type", plan.native_position))
        if plan.literal_value is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-literal-value", plan.native_position))
        if plan.python_position is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "literal-python-position", plan.python_position))
        if plan.object_kind is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "literal-object-kind", plan.object_kind.value))
        if adapter.bridge_data_action is not BridgeDataAction.DIRECT_TRANSFER:
            diagnostics.append(
                self._diagnostic(
                    plan.owner_path,
                    "invalid-literal-data-action",
                    adapter.bridge_data_action.value,
                )
            )
        return tuple(diagnostics)

    def _result_slot_diagnostics(
        self,
        plan: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return diagnostics for one native result slot."""
        return (
            *self._result_slot_identity_diagnostics(plan),
            *self._result_slot_string_diagnostics(plan),
            *self._result_slot_data_action_diagnostics(plan),
        )

    def _result_slot_identity_diagnostics(
        self,
        plan: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate result/native positions and datatype identity."""
        diagnostics = []
        if plan.result_position is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-result-position", plan.native_position))
        if plan.python_position is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "result-python-position", plan.python_position))
        if plan.semantic_type_name is None or plan.datatype_family is None:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-result-datatype", plan.native_position))
        return tuple(diagnostics)

    def _result_slot_string_diagnostics(
        self,
        plan: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require fixed string length unless runtime descriptor length is planned."""
        if plan.object_kind is ObjectKind.STRING and plan.character_length is None and plan.scalar_descriptor is None:
            return (self._diagnostic(plan.owner_path, "missing-result-character-length", plan.native_position),)
        return ()

    def _result_slot_data_action_diagnostics(
        self,
        plan: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate direct versus representation-copy native output action."""
        expected = (
            BridgeDataAction.COPY_REPRESENTATION
            if plan.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}
            or plan.scalar_descriptor is not None
            or plan.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY
            else BridgeDataAction.DIRECT_TRANSFER
        )
        adapter = plan.adapter
        if adapter is None:
            return (self._diagnostic(plan.owner_path, "missing-result-adapter-facet", None),)
        if adapter.bridge_data_action is not expected:
            return (
                self._diagnostic(
                    plan.owner_path,
                    "invalid-result-data-action",
                    f"{adapter.bridge_data_action.value}:{expected.value}",
                ),
            )
        return ()

    def _lifecycle_diagnostics(
        self,
        plan: LifecycleActionPlan,
        available_roles: tuple[str, ...],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return lifecycle source-role and backend-owner diagnostics."""
        phase_name = plan.phase.value if isinstance(plan.phase, WritebackPhase) else str(plan.phase)
        diagnostics = [*self._lifecycle_role_diagnostics(plan, available_roles, phase_name)]
        diagnostics.extend(self._lifecycle_owner_diagnostics(plan, phase_name))
        if plan.binding is not None:
            diagnostics.extend(self._binding_lifecycle_diagnostics(plan, phase_name))
        if plan.bridge is not None and plan.bridge.source_role != plan.source_role:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-lifecycle-role", phase_name))
        return tuple(diagnostics)

    def _lifecycle_role_diagnostics(
        self,
        plan: LifecycleActionPlan,
        available_roles: tuple[str, ...],
        phase_name: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return lifecycle phase and source-handoff diagnostics."""
        diagnostics = []
        if plan.source_role not in available_roles:
            diagnostics.append(self._diagnostic(plan.owner_path, f"unavailable-{phase_name}-role", plan.source_role))
        if not isinstance(plan.phase, WritebackPhase):
            diagnostics.append(self._diagnostic(plan.owner_path, "unknown-writeback-phase", phase_name))
        return tuple(diagnostics)

    def _lifecycle_owner_diagnostics(
        self,
        plan: LifecycleActionPlan,
        phase_name: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return binding-versus-bridge lifecycle ownership diagnostics."""
        diagnostics = []
        if (plan.binding is None) == (plan.bridge is None):
            diagnostics.append(self._diagnostic(plan.owner_path, "lifecycle-backend-owner", phase_name))
        expected_bridge_owner = (
            plan.operation is LifecycleOperation.WRITEBACK and plan.phase is WritebackPhase.NATIVE_MUTATION
        )
        if expected_bridge_owner != (plan.bridge is not None):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-writeback-phase-owner", phase_name))
        return tuple(diagnostics)

    def _binding_lifecycle_diagnostics(
        self,
        plan: LifecycleActionPlan,
        phase_name: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return binding-owned writeback action and target diagnostics."""
        diagnostics = []
        binding = plan.binding
        if binding.source_role != plan.source_role:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-lifecycle-role", phase_name))
        diagnostics.extend(self._binding_lifecycle_fact_diagnostics(plan, phase_name))
        if plan.operation is LifecycleOperation.WRITEBACK:
            diagnostics.extend(self._binding_writeback_lifecycle_diagnostics(plan, phase_name))
        else:
            diagnostics.extend(self._binding_derived_lifecycle_diagnostics(plan, phase_name))
        return tuple(diagnostics)

    def _binding_writeback_lifecycle_diagnostics(
        self,
        plan: LifecycleActionPlan,
        phase_name: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate one existing input/writeback lifecycle record."""
        diagnostics = []
        if plan.binding.codegen_action not in {CodegenAction.COPY_IN_OUT, CodegenAction.IN_PLACE_ARGUMENT}:
            diagnostics.append(
                self._diagnostic(plan.owner_path, "invalid-writeback-action", plan.binding.codegen_action.value)
            )
        if plan.phase is WritebackPhase.COPY_OUT and not plan.binding.python_result_role:
            diagnostics.append(self._diagnostic(plan.owner_path, "missing-python-writeback-target", phase_name))
        if plan.phase is not WritebackPhase.COPY_OUT and plan.binding.python_result_role is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "unexpected-python-writeback-target", phase_name))
        return tuple(diagnostics)

    def _binding_derived_lifecycle_diagnostics(
        self,
        plan: LifecycleActionPlan,
        phase_name: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate failure cleanup or wrapper ownership transfer for one result."""
        diagnostics = []
        if plan.operation not in {
            LifecycleOperation.DESTROY_ON_FAILURE,
            LifecycleOperation.TRANSFER_TO_WRAPPER,
        }:
            diagnostics.append(self._diagnostic(plan.owner_path, "unsupported-lifecycle-operation", plan.operation))
        if (
            plan.phase is not WritebackPhase.CLEANUP
            or plan.object_kind is not ObjectKind.DERIVED_TYPE
            or plan.datatype_family is not DatatypeFamily.DERIVED
            or plan.codegen_action is not CodegenAction.WRAPPER_INSTANCE
        ):
            diagnostics.append(self._diagnostic(plan.owner_path, "invalid-derived-lifecycle", phase_name))
        if plan.binding.python_result_role is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "unexpected-python-writeback-target", phase_name))
        return tuple(diagnostics)

    def _binding_lifecycle_fact_diagnostics(
        self,
        plan: LifecycleActionPlan,
        phase_name: str,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return shared-versus-binding lifecycle fact drift."""
        diagnostics = []
        binding = plan.binding
        if binding.codegen_action is not plan.codegen_action:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-lifecycle-action", phase_name))
        if binding.semantic_type_name != plan.semantic_type_name:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-lifecycle-type", phase_name))
        if binding.datatype_family is not plan.datatype_family:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-lifecycle-family", phase_name))
        if binding.result_position != plan.result_position:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-lifecycle-position", phase_name))
        if binding.operation is not plan.operation:
            diagnostics.append(self._diagnostic(plan.owner_path, "inconsistent-lifecycle-operation", phase_name))
        return tuple(diagnostics)

    # String lifecycle validation.
    def _string_writeback_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the complete string replacement lifecycle and exclusions."""
        replacements = tuple(
            argument
            for argument in plan.arguments
            if argument.object_kind is ObjectKind.STRING
            and argument.binding.codegen_action is CodegenAction.COPY_IN_OUT
        )
        diagnostics = []
        if replacements and plan.binding.status_error is not None:
            diagnostics.append(self._diagnostic(plan.owner_path, "string-writeback-with-status-error", plan.owner_path))
        for argument in replacements:
            diagnostics.extend(self._one_string_writeback_diagnostics(plan, argument))
        return tuple(diagnostics)

    def _one_string_writeback_diagnostics(
        self,
        plan: FunctionPlan,
        argument: ArgumentTransferPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return lifecycle coverage and fact drift for one replacement."""
        actions = tuple(
            action for action in plan.writeback_actions if action.source_role == argument.entrypoint.handoff_role
        )
        diagnostics = []
        if {action.phase for action in actions} != set(WritebackPhase):
            diagnostics.append(
                self._diagnostic(plan.owner_path, "incomplete-string-writeback-lifecycle", argument.owner_path)
            )
        for action in actions:
            diagnostics.extend(self._one_string_writeback_action_diagnostics(plan, argument, action))
        return tuple(diagnostics)

    def _one_string_writeback_action_diagnostics(
        self,
        plan: FunctionPlan,
        argument: ArgumentTransferPlan,
        action: LifecycleActionPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return one lifecycle action's string replacement consistency."""
        if (
            action.codegen_action is CodegenAction.COPY_IN_OUT
            and action.object_kind is ObjectKind.STRING
            and action.semantic_type_name == "String"
            and action.datatype_family is DatatypeFamily.STRING
            and action.result_position == argument.result_position
        ):
            return ()
        return (self._diagnostic(plan.owner_path, "inconsistent-string-writeback-lifecycle", action.phase.value),)

    def _writeback_phase_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one complete ordered phase set for every writeback handoff."""
        diagnostics = []
        grouped: dict[str, list[LifecycleActionPlan]] = {}
        for action in plan.writeback_actions:
            grouped.setdefault(action.source_role, []).append(action)
        for source_role, actions in grouped.items():
            expected = (
                {WritebackPhase.COPY_OUT}
                if all(action.object_kind is ObjectKind.NUMPY_ARRAY for action in actions)
                else set(WritebackPhase)
            )
            phases = [action.phase for action in actions]
            counts = Counter(phases)
            for phase, occurrences in counts.items():
                if occurrences > 1:
                    diagnostics.append(self._diagnostic(plan.owner_path, "duplicate-writeback-phase", phase))
            for phase in sorted(expected - set(phases), key=lambda item: item.value):
                diagnostics.append(
                    self._diagnostic(plan.owner_path, "missing-writeback-phase", f"{source_role}:{phase.value}")
                )
        return tuple(diagnostics)

    def _function_output_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return output projection and native callable-kind diagnostics."""
        diagnostics = [*self._mixed_output_diagnostics(plan)]
        diagnostics.extend(self._binding_result_diagnostics(plan))
        diagnostics.extend(self._writeback_result_diagnostics(plan))
        diagnostics.extend(self._derived_result_lifecycle_coverage_diagnostics(plan))
        diagnostics.extend(self._native_callable_kind_diagnostics(plan))
        diagnostics.extend(self._unclaimed_result_diagnostics(plan))
        return tuple(diagnostics)

    # Derived-type lifecycle validation.
    def _derived_result_lifecycle_coverage_diagnostics(
        self,
        plan: FunctionPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require explicit failure and release records for every owned object result."""
        diagnostics = []
        for result in plan.results:
            if result.object_kind is not ObjectKind.DERIVED_TYPE:
                continue
            diagnostics.extend(self._one_derived_result_lifecycle_coverage_diagnostics(plan, result))
        return tuple(diagnostics)

    def _one_derived_result_lifecycle_coverage_diagnostics(
        self,
        plan: FunctionPlan,
        result: ResultPlan,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one failure cleanup and one ownership transfer for a result."""
        source_role = result.entrypoint.native_result_role
        cleanup_count = self._lifecycle_operation_count(
            plan.cleanup_actions,
            source_role,
            LifecycleOperation.DESTROY_ON_FAILURE,
        )
        release_count = self._lifecycle_operation_count(
            plan.release_actions,
            source_role,
            LifecycleOperation.TRANSFER_TO_WRAPPER,
        )
        diagnostics = []
        if cleanup_count != 1:
            diagnostics.append(self._diagnostic(result.owner_path, "derived-failure-cleanup-count", cleanup_count))
        if release_count != 1:
            diagnostics.append(self._diagnostic(result.owner_path, "derived-wrapper-release-count", release_count))
        return tuple(diagnostics)

    @staticmethod
    def _lifecycle_operation_count(actions, source_role, operation) -> int:
        """Count lifecycle records matching one result role and operation."""
        return sum(action.source_role == source_role and action.operation is operation for action in actions)

    def _mixed_output_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require one contiguous public order across results and writebacks."""
        if not plan.results or not plan.writeback_actions:
            return ()
        writebacks = self._projected_writebacks(plan)
        positions = tuple(result.result_position for result in plan.results) + tuple(
            action.binding.result_position for action in writebacks
        )
        return self._sequence_diagnostics(plan.owner_path, "mixed-output", positions, len(positions))

    @staticmethod
    def _projected_writebacks(plan: FunctionPlan) -> tuple:
        """Return concrete copy-out actions in their planned result order."""
        return tuple(
            action
            for action in plan.writeback_actions
            if action.phase is WritebackPhase.COPY_OUT and action.binding is not None
        )

    def _binding_result_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate ordered consumers and the sole direct native result."""
        diagnostics = []
        if not plan.writeback_actions:
            diagnostics.extend(
                self._sequence_diagnostics(
                    plan.owner_path,
                    "binding-result",
                    tuple(result.result_position for result in plan.results),
                    len(plan.results),
                )
            )
        direct_results = tuple(result for result in plan.results if result.source_kind == "direct_return")
        if len(direct_results) > 1:
            diagnostics.append(self._diagnostic(plan.owner_path, "multiple-direct-results", len(direct_results)))
        return tuple(diagnostics)

    def _writeback_result_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate contiguous Python result positions for copy-out actions."""
        result_positions = tuple(
            action.binding.result_position
            for action in plan.writeback_actions
            if action.phase is WritebackPhase.COPY_OUT and action.binding is not None
        )
        if plan.results:
            return ()
        return self._sequence_diagnostics(
            plan.owner_path,
            "writeback-result",
            result_positions,
            len(result_positions),
        )

    def _native_callable_kind_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require callable kind to agree with the public result representation."""
        requires_subroutine = not any(result.source_kind == "direct_return" for result in plan.results)
        if plan.bridge.native_is_subroutine != requires_subroutine:
            return (self._diagnostic(plan.owner_path, "inconsistent-native-callable-kind", requires_subroutine),)
        return ()

    def _unclaimed_result_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require exactly one binding or status consumer per native output."""
        claimed_roles = self._claimed_result_roles(plan)
        diagnostics = []
        for slot in plan.entrypoint.projected_slots:
            if slot.source_kind != "result":
                continue
            claim_count = claimed_roles[slot.symbolic_role]
            if claim_count == 0:
                diagnostics.append(self._diagnostic(plan.owner_path, "unclaimed-native-result", slot.symbolic_role))
            elif claim_count > 1:
                diagnostics.append(
                    self._diagnostic(plan.owner_path, "multiple-native-result-consumers", slot.symbolic_role)
                )
        return tuple(diagnostics)

    def _claimed_result_roles(self, plan: FunctionPlan) -> Counter[str]:
        """Return public and status-policy consumers of native result slots."""
        roles = Counter(
            result.entrypoint.native_result_role for result in plan.results if result.source_kind == "hidden_output"
        )
        if plan.binding.status_error is not None:
            roles[plan.binding.status_error.status_role] += 1
            if plan.binding.status_error.message_role is not None:
                roles[plan.binding.status_error.message_role] += 1
        return roles

    def _status_error_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate completed status/message roles before either backend emits."""
        policy = plan.binding.status_error
        if policy is None:
            return ()
        result_slots = {
            slot.symbolic_role: slot for slot in plan.entrypoint.projected_slots if slot.source_kind == "result"
        }
        diagnostics = [*self._status_role_diagnostics(plan, result_slots)]
        diagnostics.extend(self._message_role_diagnostics(plan, result_slots))
        diagnostics.extend(self._status_policy_diagnostics(plan))
        return tuple(diagnostics)

    def _status_role_diagnostics(
        self,
        plan: FunctionPlan,
        result_slots: dict[str, NativeEntrypointProjectedSlotPlan],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the completed integer status role."""
        policy = plan.binding.status_error
        status = result_slots.get(policy.status_role)
        if status is None:
            return (self._diagnostic(plan.owner_path, "missing-status-result-role", policy.status_role),)
        if status.object_kind is not ObjectKind.SCALAR or status.datatype_family is not DatatypeFamily.INTEGER:
            return (self._diagnostic(plan.owner_path, "incompatible-status-result-role", policy.status_role),)
        if status.semantic_type_name != "Int32":
            return (self._diagnostic(plan.owner_path, "incompatible-status-result-role", policy.status_role),)
        return ()

    def _message_role_diagnostics(
        self,
        plan: FunctionPlan,
        result_slots: dict[str, NativeEntrypointProjectedSlotPlan],
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate the optional fixed-length status message role."""
        policy = plan.binding.status_error
        if policy.message_role is None:
            return ()
        message = result_slots.get(policy.message_role)
        if message is None:
            return (self._diagnostic(plan.owner_path, "missing-message-result-role", policy.message_role),)
        if message.object_kind is not ObjectKind.STRING or message.datatype_family is not DatatypeFamily.STRING:
            return (self._diagnostic(plan.owner_path, "incompatible-message-result-role", policy.message_role),)
        if message.character_length is None:
            return (self._diagnostic(plan.owner_path, "incompatible-message-result-role", policy.message_role),)
        return ()

    def _status_policy_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Validate cross-role and exception facts for status handling."""
        policy = plan.binding.status_error
        diagnostics = []
        if policy.message_role == policy.status_role:
            diagnostics.append(self._diagnostic(plan.owner_path, "duplicate-status-message-role", policy.status_role))
        if policy.exception_kind is not PythonExceptionKind.RUNTIME_ERROR:
            diagnostics.append(self._diagnostic(plan.owner_path, "unsupported-status-exception", policy.exception_kind))
        return tuple(diagnostics)

    def _sequence_diagnostics(
        self,
        owner_path: str,
        label: str,
        positions: tuple[int, ...],
        count: int,
    ) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return contiguous-position coverage diagnostics."""
        diagnostics = []
        counts = Counter(positions)
        for position, occurrences in sorted(counts.items()):
            if occurrences > 1:
                diagnostics.append(self._diagnostic(owner_path, f"duplicate-{label}-position", position))
        expected = set(range(count))
        actual = set(positions)
        for position in sorted(expected - actual):
            diagnostics.append(self._diagnostic(owner_path, f"missing-{label}-position", position))
        for position in sorted(actual - expected):
            code = f"negative-{label}-position" if position < 0 else f"out-of-range-{label}-position"
            diagnostics.append(self._diagnostic(owner_path, code, position))
        return tuple(diagnostics)

    # Function-wide symbolic-role validation.
    def _duplicate_role_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Return duplicate symbolic producer/consumer role diagnostics."""
        roles = (
            *self._expected_available_roles(plan),
            *self._native_slot_roles(plan.entrypoint.projected_slots, "literal"),
        )
        return tuple(
            self._diagnostic(plan.owner_path, "duplicate-symbolic-role", role)
            for role, count in Counter(roles).items()
            if count > 1
        )

    def _available_role_diagnostics(self, plan: FunctionPlan) -> tuple[WrapperPlanDiagnostic, ...]:
        """Require the advertised roles to match argument and result producers."""
        expected = self._expected_available_roles(plan)
        if Counter(plan.available_roles) != Counter(expected):
            return (self._diagnostic(plan.owner_path, "inconsistent-available-roles", plan.available_roles),)
        return ()

    def _expected_available_roles(self, plan: FunctionPlan) -> tuple[str, ...]:
        """Return every role advertised after binding conversion or the native call."""
        return (
            *self._argument_handoff_roles(plan.arguments),
            *self._argument_extent_roles(plan.arguments),
            *self._argument_descriptor_output_roles(plan.arguments),
            *self._native_slot_roles(plan.entrypoint.projected_slots, "result"),
            *self._update_result_roles(plan.results),
            *self._direct_result_roles(plan.results),
            *self._declaration_callable_roles(plan.declaration_callables),
        )

    @staticmethod
    def _argument_handoff_roles(arguments: tuple[ArgumentTransferPlan, ...]) -> tuple[str, ...]:
        """Return the primary binding-produced role for every argument."""
        return tuple(argument.entrypoint.handoff_role for argument in arguments)

    @staticmethod
    def _argument_descriptor_output_roles(arguments: tuple[ArgumentTransferPlan, ...]) -> tuple[str, ...]:
        """Return optional descriptor roles produced during argument conversion."""
        return tuple(
            role
            for argument in arguments
            for role in (
                argument.entrypoint.descriptor_output_role,
                argument.entrypoint.descriptor_output_presence_role,
            )
            if role is not None
        )

    @staticmethod
    def _native_slot_roles(
        slots: tuple[NativeEntrypointProjectedSlotPlan, ...],
        source_kind: str,
    ) -> tuple[str, ...]:
        """Return symbolic roles produced by one native-slot category."""
        return tuple(slot.symbolic_role for slot in slots if slot.source_kind == source_kind)

    @staticmethod
    def _direct_result_roles(results: tuple[ResultPlan, ...]) -> tuple[str, ...]:
        """Return native result roles produced by direct-return plans."""
        return tuple(
            result.entrypoint.native_result_role for result in results if result.source_kind == "direct_return"
        )

    @staticmethod
    def _update_result_roles(results: tuple[ResultPlan, ...]) -> tuple[str, ...]:
        """Return native result roles produced beside a Python-visible argument."""
        return tuple(result.entrypoint.native_result_role for result in results if result.updates_argument)

    @staticmethod
    def _declaration_callable_roles(
        declarations: tuple[DeclarationCallablePlan, ...],
    ) -> tuple[str, ...]:
        """Return bridge-resolved declaration-callable symbol roles."""
        return tuple(item.symbolic_role for item in declarations)

    @staticmethod
    def _argument_extent_roles(arguments: tuple[ArgumentTransferPlan, ...]) -> tuple[str, ...]:
        """Return every binding-produced array extent role in argument order."""
        return tuple(
            role
            for argument in arguments
            for role in (argument.array.extent_roles if argument.array is not None else ())
        )

    # Diagnostic formatting and generated-wrapper assembly.
    def _diagnostic(self, owner_path: str, code: str, detail: object) -> WrapperPlanDiagnostic:
        """Create one normalized diagnostic from an owner, stable code, and detail.

        All validation paths use this helper so summaries preserve one string
        representation of arbitrary details.  It has no logging or mutation
        side effect.
        """
        return WrapperPlanDiagnostic(owner_path, code, str(detail))

    def _diagnostic_summary(self, diagnostics: tuple[WrapperPlanDiagnostic, ...]) -> str:
        """Format ordered diagnostics into the public generation failure message.

        ``diagnostics`` must already be in collection order.  The method joins
        each owner-local record without sorting or deduplicating it, preserving
        the error text established by the validation traversal.
        """
        details = "; ".join(f"{item.owner_path}:{item.code}:{item.message}" for item in diagnostics)
        return f"Invalid edited wrapper plan before generation: {details}"

    def _generated_wrapper(
        self,
        module_name: str,
        c_sources: tuple[str, ...],
        c_module_names: tuple[str, ...],
        c_header: str,
        fortran_source: str | None,
        native_support_keys: tuple[str, ...],
        required_headers: tuple[str, ...],
        required_link_languages: tuple[str, ...],
        native_generated_code_groups: tuple[NativeGeneratedCodeGroupPlan, ...],
    ) -> GeneratedWrapper:
        """Package rendered source text with the filenames owned by build integration.

        Each binding translation unit is named for the C module it renders, so
        the binding file is followed by any collision-adapter unit. The
        returned wrapper places bridge, C sources, and header text in that
        stable order; this helper does not write files or freeze the newly
        assembled source records.
        """
        # Name bridge, binding, and header files before pairing each with rendered text.
        binding_sources = tuple(Path(f"{name}.c") for name in c_module_names)
        bridge_sources = tuple(
            dict.fromkeys(
                Path(path)
                for group in native_generated_code_groups
                if group.language == "fortran"
                for path in group.source_paths
            )
        )
        if fortran_source is not None and len(bridge_sources) != 1:
            raise ValueError("Generated Fortran payload requires exactly one planned physical source")
        if fortran_source is None and bridge_sources:
            raise ValueError("Planned generated Fortran groups require a rendered source payload")
        headers = (Path(f"{module_name}_wrapper.h"),)

        # Preserve build-consumed source ordering: bridge, binding units, then header.
        return GeneratedWrapper(
            module_name=module_name,
            extension_init_name=f"PyInit_{module_name}",
            sources=(
                *((GeneratedSource(bridge_sources[0], fortran_source),) if fortran_source is not None else ()),
                *(GeneratedSource(path, source) for path, source in zip(binding_sources, c_sources, strict=True)),
                GeneratedSource(headers[0], c_header),
            ),
            bridge_sources=bridge_sources,
            binding_sources=binding_sources,
            headers=headers,
            native_support_keys=native_support_keys,
            required_headers=required_headers,
            required_link_languages=required_link_languages,
            native_generated_code_groups=native_generated_code_groups,
        )


if __name__ == "__main__":
    from prik.planning.planner import WrapperPlanner
    from prik.semantics.models import SemanticArgument, SemanticFunction, SemanticModule, SemanticType
    from prik.policy.completion import complete_semantic_policies

    module = SemanticModule(
        name="generator_demo",
        functions=[
            SemanticFunction(
                name="double_value",
                native_name="DOUBLE_VALUE",
                arguments=[SemanticArgument("value", SemanticType("Float64"))],
                return_type=SemanticType("Float64"),
            )
        ],
    )
    complete_semantic_policies(module)
    rendered = WrapperGenerator().generate(WrapperPlanner().build(module))

    print(f"Extension initializer: {rendered.extension_init_name}")
    print("Rendered sources:", ", ".join(source.path.name for source in rendered.sources))
    print("Native support:", ", ".join(rendered.native_support_keys) or "none")
