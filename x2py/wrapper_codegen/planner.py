"""Hierarchical wrapper-plan construction from completed semantic policy."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace

from x2py.semantics import models
from x2py.semantics.native_array_handles import NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER
from x2py.semantics.wrapper_policy import (
    ArgumentHandoffMode,
    ArrayHandoffPolicy,
    CallbackHandoffPolicy,
    CallbackResultPolicy,
    CallbackTransferPolicy,
    ClassSurfacePolicy,
    DerivedCallPolicy,
    DerivedFieldPolicy,
    DerivedFieldAccessMechanism,
    DerivedHandoffPolicy,
    DerivedTypePolicy,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    ModuleVariablePolicy,
    OverloadPolicy,
    OptionalMode,
    ArgumentPolicy,
    FunctionWrapperPolicy,
    LifecycleOperation,
    LifecyclePolicy,
    NativeCallSlotPolicy,
    NativeArrayActualPolicy,
    NativeArrayHandleWrapperPolicy,
    NativeDescriptorHandoffABI,
    NativeDescriptorHandoffPolicy,
    NativeStatusErrorPolicy,
    PolymorphicDispatchPolicy,
    ResultPolicy,
    ScalarDescriptorResultPolicy,
    TransformationPolicy,
    WritebackPhase,
    completed_module_variable_policy,
    completed_function_wrapper_policy,
    completed_derived_type_policy,
    completed_class_surface_policy,
)
from x2py.semantics.wrapper_exports import PythonExportPolicy
from x2py.semantics.ownership import NativeBarrierAction, SetterAction
from x2py.wrapper_codegen.docstrings import WrapperDocstringBuilder
from x2py.wrapper_codegen.plan import (
    ArrayHandoffPlan,
    ArgumentTransferPlan,
    BindingArgumentPlan,
    BindingFunctionPlan,
    BindingLifecyclePlan,
    BindingModulePlan,
    BindingModuleVariablePlan,
    BindingResultPlan,
    BindingStatusErrorPlan,
    BridgeArgumentPlan,
    BridgeFunctionPlan,
    BridgeLifecyclePlan,
    BridgeModulePlan,
    BridgeModuleVariablePlan,
    BridgeResultPlan,
    CallbackHandoffPlan,
    CallbackResultPlan,
    CallbackTransferPlan,
    ClassMethodPlan,
    ClassCallPlan,
    OverloadArgumentMatchPlan,
    OverloadPlan,
    ClassSurfacePlan,
    ConstructorFieldPlan,
    ConstructorPlan,
    DatatypeFamily,
    DerivedFieldPlan,
    DerivedCallCasePlan,
    DerivedCallPlan,
    DerivedHandoffPlan,
    DerivedMemberPathPlan,
    DerivedModuleObjectPlan,
    DerivedTypePlan,
    FunctionPlan,
    LifecycleActionPlan,
    ModulePlan,
    ModuleVariablePlan,
    NamespacePlan,
    NativeCallSlotPlan,
    NativeArrayActualPlan,
    NativeArrayHandlePlan,
    NativeDescriptorHandoffPlan,
    PolymorphicDispatchPlan,
    PolymorphicVariantPlan,
    ResultPlan,
    ScalarDescriptorResultPlan,
    TransformationPlan,
)
from x2py.wrapper_codegen.naming import NativeSymbolNames
from x2py.wrapper_codegen.visitor import ClassVisitor


_DATATYPE_FAMILIES = {
    "Bool": DatatypeFamily.BOOL,
    "Int8": DatatypeFamily.INTEGER,
    "Int16": DatatypeFamily.INTEGER,
    "Int32": DatatypeFamily.INTEGER,
    "Int64": DatatypeFamily.INTEGER,
    "Float32": DatatypeFamily.REAL,
    "Float64": DatatypeFamily.REAL,
    "Complex64": DatatypeFamily.COMPLEX,
    "Complex128": DatatypeFamily.COMPLEX,
    "String": DatatypeFamily.STRING,
}


class WrapperPlanner(ClassVisitor):
    """Project completed semantic policies into one editable shared plan."""

    def __init__(self):
        """Create a planner for one policy-completed semantic module."""
        super().__init__()
        self.docstrings = WrapperDocstringBuilder()

    def build(self, module: models.SemanticModule) -> ModulePlan:
        """Mechanically project one editable wrapper plan."""
        return self.visit(module)

    def _visit_SemanticModule(self, module: models.SemanticModule) -> ModulePlan:
        """Return one module plan, failing at the first inconsistent owner."""
        self._derived_type_names = {semantic_class.name for semantic_class in module.classes}
        self._derived_field_plans: dict[str, DerivedFieldPlan] = {}
        self._complete_derived_backend_symbols(module)
        functions, variables, derived_types, classes, overloads = self._namespace_member_plans(module)
        if not any(
            (*functions.values(), *variables.values(), *derived_types.values(), *classes.values(), *overloads.values())
        ):
            raise ValueError(f"Semantic module {module.name!r} has no public wrapper exports")
        self._attach_class_functions(functions, classes)
        self._attach_overload_functions(functions, overloads)
        namespaces = self._namespace_plans(module.name, functions, variables, derived_types, classes, overloads)
        return ModulePlan(
            owner_path=module.name,
            binding=BindingModulePlan(module.name),
            bridge=BridgeModulePlan(module.name),
            namespaces=namespaces,
            required_headers=self._required_headers(namespaces),
        )

    def _namespace_member_plans(self, module: models.SemanticModule) -> tuple[dict, dict, dict, dict, dict]:
        """Build namespace-owned plan maps before linking private callables."""
        return (
            self._functions_by_namespace(module),
            self._variables_by_namespace(module),
            self._derived_types_by_namespace(module),
            self._classes_by_namespace(module),
            self._module_overloads_by_namespace(module),
        )

    def _attach_class_functions(self, functions: dict, classes: dict) -> None:
        """Add each class-owned callable to the namespace's shared function list."""
        for namespace, surfaces in classes.items():
            functions[namespace].extend(
                function for surface in surfaces for function in self._class_function_plans(surface)
            )

    @staticmethod
    def _attach_overload_functions(functions: dict, overloads: dict) -> None:
        """Expose private module-overload candidates to the shared C method table."""
        for namespace, plans in overloads.items():
            functions[namespace].extend(candidate for overload in plans for candidate in overload.candidates)

    def _namespace_plans(
        self,
        module_name: str,
        functions: dict,
        variables: dict,
        derived_types: dict,
        classes: dict,
        overloads: dict,
    ) -> tuple[NamespacePlan, ...]:
        """Freeze linked namespace members in dependency-safe path order."""
        self._complete_generated_symbols(functions, variables)
        namespace_paths = self._namespace_paths((*functions, *variables, *derived_types, *classes, *overloads))
        return tuple(
            self._namespace_plan(
                module_name,
                path,
                tuple(functions[path]),
                tuple(variables[path]),
                tuple(derived_types[path]),
                tuple(classes[path]),
                tuple(overloads[path]),
            )
            for path in namespace_paths
        )

    def _namespace_plan(
        self,
        module_name: str,
        path: tuple[str, ...],
        functions: tuple[FunctionPlan, ...],
        variables: tuple[ModuleVariablePlan, ...],
        derived_types: tuple[DerivedTypePlan, ...],
        classes: tuple[ClassSurfacePlan, ...],
        overloads: tuple[OverloadPlan, ...],
    ) -> NamespacePlan:
        """Freeze one namespace with stable public documentation."""
        return NamespacePlan(
            owner_path=self._namespace_owner_path(module_name, path),
            python_path=path,
            functions=functions,
            variables=variables,
            derived_types=derived_types,
            classes=classes,
            overloads=overloads,
            docstring=self.docstrings.namespace(
                module_name,
                path,
                functions,
                variables,
                classes,
                overloads,
            ),
        )

    def _complete_derived_backend_symbols(self, module: models.SemanticModule) -> None:
        """Keep short native type names unless the complete unit needs qualification."""
        policies = tuple(completed_derived_type_policy(item) for item in module.classes)
        counts = Counter(policy.native_type_name.casefold() for policy in policies)
        self._derived_backend_symbols = {
            policy.type_identity: self._derived_backend_symbol_for_policy(policy, counts) for policy in policies
        }
        self._class_python_names = self._completed_class_python_names(policies)

    @staticmethod
    def _completed_class_python_names(policies: tuple[DerivedTypePolicy, ...]) -> dict[tuple[str, str], str]:
        """Index the primary completed Python export for each native type."""
        return {policy.type_identity: policy.python_names[0] for policy in policies if policy.python_names}

    @staticmethod
    def _derived_backend_symbol_for_policy(policy: DerivedTypePolicy, counts: Counter) -> str:
        """Choose a short native symbol, qualifying only genuine name collisions."""
        native_name = policy.native_type_name.casefold()
        if counts[native_name] == 1:
            return native_name
        return NativeSymbolNames.compact(
            ".".join(policy.type_identity),
            policy.native_type_name,
            limit=12,
        )

    def _derived_backend_symbol(self, type_identity: tuple[str, str]) -> str:
        """Return the qualified backend symbol completed for one native identity."""
        try:
            return self._derived_backend_symbols[type_identity]
        except KeyError as exc:
            raise ValueError(f"Missing derived backend symbol for {type_identity!r}") from exc

    # Derived-type definition and field planning.
    def _derived_types_by_namespace(
        self,
        module: models.SemanticModule,
    ) -> dict[tuple[str, ...], list[DerivedTypePlan]]:
        """Project opaque types from completed class and field policies."""
        grouped = defaultdict(list)
        for semantic_class in self._semantic_classes(module.classes):
            if semantic_class.visibility != "public":
                continue
            policy = completed_derived_type_policy(semantic_class)
            surface = completed_class_surface_policy(semantic_class)
            exports_by_namespace = defaultdict(list)
            for export in policy.python_exports:
                exports_by_namespace[export.namespace].append(export.name)
            for namespace, python_names in exports_by_namespace.items():
                grouped[namespace].append(
                    self._derived_type_plan(
                        policy,
                        tuple(python_names),
                        fields=surface.effective_fields,
                    )
                )
        return grouped

    def _derived_type_plan(
        self,
        policy: DerivedTypePolicy,
        python_names: tuple[str, ...],
        *,
        fields: tuple[DerivedFieldPolicy, ...] | None = None,
    ) -> DerivedTypePlan:
        """Mechanically project one completed derived type and its public fields."""
        planned_fields = tuple(self._derived_field_plan(field) for field in (fields or policy.fields))
        return DerivedTypePlan(
            owner_path=policy.owner_path,
            type_name=policy.type_name,
            type_identity=policy.type_identity,
            backend_symbol=self._derived_backend_symbol(policy.type_identity),
            native_type_name=policy.native_type_name,
            native_scope=policy.native_scope,
            python_names=python_names,
            fields=planned_fields,
            finalizers=policy.finalizers,
            bind_c=policy.bind_c,
            sequence=policy.sequence,
        )

    # Generated class surfaces compose Phase 8 types and ordinary function plans.
    def _classes_by_namespace(
        self,
        module: models.SemanticModule,
    ) -> dict[tuple[str, ...], list[ClassSurfacePlan]]:
        """Project completed class surfaces into their public namespaces."""
        grouped = defaultdict(list)
        for semantic_class in self._semantic_classes(module.classes):
            if semantic_class.visibility != "public":
                continue
            policy = completed_class_surface_policy(semantic_class)
            exports_by_namespace = defaultdict(list)
            for export in policy.python_exports:
                exports_by_namespace[export.namespace].append(export.name)
            for namespace, python_names in exports_by_namespace.items():
                grouped[namespace].append(
                    self._class_surface_plan(
                        module.name,
                        namespace,
                        semantic_class,
                        policy,
                        tuple(python_names),
                    )
                )
        return grouped

    @staticmethod
    def _semantic_classes(classes: list[models.SemanticClass]):
        """Yield classes in source order while retaining nested declarations."""
        for semantic_class in classes:
            yield semantic_class
            yield from WrapperPlanner._semantic_classes(semantic_class.classes)

    def _class_surface_plan(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        semantic_class: models.SemanticClass,
        policy: ClassSurfacePolicy,
        python_names: tuple[str, ...],
    ) -> ClassSurfacePlan:
        """Compose one class plan from completed method and constructor facts."""
        methods = self._class_method_plans(module_name, namespace, semantic_class, policy)
        overloads_by_name = {overload.python_name: overload for overload in policy.overloads}
        overloads = self._class_overload_plans(
            module_name,
            namespace,
            semantic_class,
            policy.type_identity,
            overloads_by_name,
        )
        fields = tuple(self._derived_field_plan(field) for field in policy.effective_fields)
        constructor = self._constructor_plan(
            module_name,
            namespace,
            semantic_class,
            policy,
            methods,
            overloads_by_name,
            python_name=python_names[0],
            fields=fields,
        )
        return ClassSurfacePlan(
            owner_path=policy.owner_path,
            type_identity=policy.type_identity,
            python_names=python_names,
            base_identities=policy.base_identities,
            constructor=constructor,
            methods=methods,
            overloads=overloads,
            registration=policy.registration,
            docstring=self.docstrings.class_surface(
                python_names[0],
                policy.type_identity[1],
                constructor,
                fields,
                methods,
                overloads,
            ),
        )

    def _class_method_plans(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        semantic_class: models.SemanticClass,
        policy: ClassSurfacePolicy,
    ) -> tuple[ClassMethodPlan, ...]:
        """Link public methods and a private constructor target in source order."""
        methods_by_owner = self._class_methods_by_owner(policy)
        methods = []
        for method in semantic_class.methods:
            if method.name == "__init__":
                continue
            owner_path = f"{policy.owner_path}.{method.name}"
            method_policy = methods_by_owner[owner_path]
            if not self._class_method_is_planned(method, method_policy, owner_path, policy):
                continue
            methods.append(
                self._class_method_plan(
                    module_name,
                    namespace,
                    method,
                    method_policy,
                    policy.type_identity,
                )
            )
        return tuple(methods)

    @staticmethod
    def _class_methods_by_owner(policy: ClassSurfacePolicy) -> dict[str, object]:
        """Index completed method records by their stable semantic owner path."""
        return {method.owner_path: method for method in policy.methods}

    @staticmethod
    def _class_method_is_planned(method, method_policy, owner_path: str, policy: ClassSurfacePolicy) -> bool:
        """Keep public methods plus the private target selected for construction."""
        return method_policy.public or owner_path == policy.constructor.target_owner_path

    def _class_overload_plans(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        semantic_class: models.SemanticClass,
        type_identity: tuple[str, str],
        policies: dict[str, OverloadPolicy],
    ) -> tuple[OverloadPlan, ...]:
        """Link every non-constructor overload set to ordinary function plans."""
        functions = self._class_overload_functions(semantic_class, policies.values())
        return tuple(
            self._overload_plan(
                module_name,
                namespace,
                policy,
                functions,
                private_name=lambda name, index: self._class_callable_name(type_identity, f"{name}_{index}"),
            )
            for policy in policies.values()
            if policy.python_name != "__init__"
        )

    def _constructor_plan(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        semantic_class: models.SemanticClass,
        policy: ClassSurfacePolicy,
        methods: tuple[ClassMethodPlan, ...],
        overloads_by_name: dict,
        *,
        python_name: str,
        fields: tuple[DerivedFieldPlan, ...],
    ) -> ConstructorPlan:
        """Link one completed constructor to its target and lifecycle records."""
        constructor = policy.constructor
        target = next((item.function for item in methods if item.owner_path == constructor.target_owner_path), None)
        overload = self._constructor_overload_plan(
            module_name,
            namespace,
            semantic_class,
            policy.type_identity,
            overloads_by_name,
        )
        plan = ConstructorPlan(
            kind=constructor.kind,
            fields=tuple(self._constructor_field_plan(field) for field in constructor.fields),
            target_owner_path=constructor.target_owner_path,
            overload_name=constructor.overload_name,
            lifecycle=constructor.lifecycle,
            rejection_message=constructor.rejection_message,
            target=target,
            overload=overload,
        )
        plan.docstring = self.docstrings.constructor(python_name, plan, fields)
        return plan

    def _constructor_overload_plan(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        semantic_class: models.SemanticClass,
        type_identity: tuple[str, str],
        policies: dict[str, OverloadPolicy],
    ) -> OverloadPlan | None:
        """Return the constructor-owned overload set, when one was completed."""
        policy = policies.get("__init__")
        if policy is not None:
            functions = self._class_overload_functions(semantic_class, (policy,))
            return self._overload_plan(
                module_name,
                namespace,
                policy,
                functions,
                private_name=lambda name, index: self._class_callable_name(type_identity, f"{name}_{index}"),
            )
        return None

    @staticmethod
    def _constructor_field_plan(field) -> ConstructorFieldPlan:
        """Project one editable default-constructor field record."""
        return ConstructorFieldPlan(
            owner_path=field.owner_path,
            name=field.name,
            default_value=field.default_value,
            setter_action=field.setter_action,
        )

    def _class_method_plan(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        method: models.SemanticMethod,
        policy,
        type_identity: tuple[str, str],
    ) -> ClassMethodPlan:
        """Link one method descriptor to the existing function transfer path."""
        function_policy = completed_function_wrapper_policy(method)
        private_name = self._class_callable_name(type_identity, policy.python_name)
        function = self._function_plan(
            function_policy,
            PythonExportPolicy(namespace, private_name),
            module_name,
            public=False,
        )
        plan = ClassMethodPlan(
            owner_path=policy.owner_path,
            python_name=policy.python_name,
            kind=policy.kind,
            passed_object_position=policy.passed_object_position,
            public=policy.public,
            function=function,
        )
        plan.docstring = self.docstrings.method(plan)
        return plan

    def _overload_plan(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        policy: OverloadPolicy,
        functions: dict[str, models.SemanticFunction],
        *,
        private_name,
    ) -> OverloadPlan:
        """Link one overload plan to its explicit concrete candidates."""
        candidates = tuple(
            self._function_plan(
                completed_function_wrapper_policy(functions[candidate.owner_path]),
                PythonExportPolicy(
                    namespace,
                    private_name(policy.python_name, index),
                ),
                module_name,
                public=False,
            )
            for index, candidate in enumerate(policy.candidates)
        )
        plan = OverloadPlan(
            owner_path=policy.owner_path,
            python_name=policy.python_name,
            kind=policy.kind,
            candidates=candidates,
            candidate_matches=tuple(
                tuple(
                    OverloadArgumentMatchPlan(
                        python_name=argument.python_name,
                        kind=argument.kind,
                        optional=argument.optional,
                        semantic_type_name=argument.semantic_type_name,
                        rank=argument.rank,
                        derived_type_identity=argument.derived_type_identity,
                        accept_builtin_scalar=argument.accept_builtin_scalar,
                    )
                    for argument in candidate.arguments
                )
                for candidate in policy.candidates
            ),
            candidate_passed_objects=tuple(candidate.passed_object for candidate in policy.candidates),
            unsupported_extra_argument_message=policy.unsupported_extra_argument_message,
            identity_receiver_shortcut=policy.identity_receiver_shortcut,
        )
        plan.docstring = self.docstrings.overload(plan)
        return plan

    @staticmethod
    def _class_overload_functions(
        semantic_class: models.SemanticClass,
        policies,
    ) -> dict[str, models.SemanticFunction]:
        """Index only concrete class procedures selected by completed overload policy."""
        selected = WrapperPlanner._selected_overload_owner_paths(policies)
        owner_path = completed_class_surface_policy(semantic_class).owner_path
        return {
            path: procedure
            for path, procedure in WrapperPlanner._class_overload_entries(semantic_class, owner_path)
            if path in selected
        }

    @staticmethod
    def _selected_overload_owner_paths(policies) -> set[str]:
        """Return concrete owner paths referenced by completed overloads."""
        return {candidate.owner_path for policy in policies for candidate in policy.candidates}

    @staticmethod
    def _class_overload_entries(
        semantic_class: models.SemanticClass,
        owner_path: str,
    ) -> tuple[tuple[str, models.SemanticFunction], ...]:
        """Pair every concrete class procedure with its completed owner path."""
        return tuple(
            (f"{owner_path}.{overload.name}.{procedure.name}", procedure)
            for overload in semantic_class.overload_sets
            for procedure in overload.procedures
        )

    def _class_callable_name(self, type_identity: tuple[str, str], name: str) -> str:
        """Return one private callable export fixed during plan construction."""
        return f"_x2py_class_{self._derived_backend_symbol(type_identity)}_{name.casefold()}"

    @staticmethod
    def _class_function_plans(surface: ClassSurfacePlan) -> tuple[FunctionPlan, ...]:
        """Return every ordinary function plan owned by one class surface."""
        return (
            *(method.function for method in surface.methods),
            *(candidate for overload in surface.overloads for candidate in overload.candidates),
            *(surface.constructor.overload.candidates if surface.constructor.overload is not None else ()),
        )

    def _derived_field_plan(self, policy: DerivedFieldPolicy) -> DerivedFieldPlan:
        """Project one completed field once for every backend and module path."""
        cached = self._derived_field_plans.get(policy.owner_path)
        if cached is not None:
            return cached
        array = self._array_plan(policy.array, policy.owner_path, include_buffer_roles=False)
        plan = DerivedFieldPlan(
            owner_path=policy.owner_path,
            name=policy.name,
            native_name=policy.native_name,
            semantic_type_name=policy.semantic_type_name,
            string_element=policy.string_element,
            rank=policy.rank,
            object_kind=policy.object_kind,
            access=policy.access,
            getter_action=policy.getter_action,
            setter_action=policy.setter_action,
            native_assignment=policy.native_assignment,
            owner_retention=policy.owner_retention,
            character_length=policy.character_length,
            getter_role=f"{policy.owner_path}:getter",
            setter_role=(f"{policy.owner_path}:setter" if policy.setter_action is SetterAction.WRITE_THROUGH else None),
            array=array,
            native_array_handle=self._native_array_handle_plan(
                policy.native_array_handle,
                policy.owner_path,
                array=array,
            ),
            derived=self._derived_handoff_plan(policy.derived),
            docstring="",
        )
        plan.docstring = self.docstrings.field(plan)
        self._derived_field_plans[policy.owner_path] = plan
        return plan

    def _functions_by_namespace(self, module: models.SemanticModule) -> dict[tuple[str, ...], list[FunctionPlan]]:
        """Group exported function plans by completed Python namespace."""
        functions = defaultdict(list)
        for function in module.functions:
            if function.visibility != "public":
                continue
            policy = self._module_function_policy(function)
            if policy is None:
                continue
            for export in policy.python_exports:
                functions[export.namespace].append(self._function_plan(policy, export, module.name))
        return functions

    def _module_overloads_by_namespace(
        self,
        module: models.SemanticModule,
    ) -> dict[tuple[str, ...], list[OverloadPlan]]:
        """Group completed module generics and their private concrete calls."""
        grouped = defaultdict(list)
        policies = module.metadata.get(models.RESOLVED_MODULE_OVERLOAD_POLICIES_METADATA)
        if not isinstance(policies, tuple):
            if module.overload_sets:
                raise ValueError(f"Module {module.name!r} has no completed overload policies")
            policies = ()
        functions = self._module_overload_function_index(module)
        for item in policies:
            policy = self._completed_module_overload_policy(module, item)
            for export in policy.python_exports:
                grouped[export.namespace].append(self._exported_module_overload_plan(module, policy, export, functions))
        return grouped

    @staticmethod
    def _module_overload_function_index(
        module: models.SemanticModule,
    ) -> dict[str, models.SemanticFunction]:
        """Index concrete module-generic procedures by completed owner path."""
        return {
            f"{(procedure.origin.native_scope or module.name)!s}.{overload.name}.{procedure.name}": procedure
            for overload in module.overload_sets
            for procedure in overload.procedures
        }

    @staticmethod
    def _completed_module_overload_policy(module: models.SemanticModule, policy) -> OverloadPolicy:
        """Require one completed module-overload policy before plan projection."""
        if not isinstance(policy, OverloadPolicy):
            raise ValueError(f"Module {module.name!r} has an incomplete overload policy")
        if policy.blockers:
            details = "; ".join(policy.blockers)
            raise ValueError(f"Module overload {policy.owner_path!r} has unsupported policy: {details}")
        return policy

    def _exported_module_overload_plan(
        self,
        module: models.SemanticModule,
        policy: OverloadPolicy,
        export: PythonExportPolicy,
        functions: dict[str, models.SemanticFunction],
    ) -> OverloadPlan:
        """Project one namespace export onto the shared concrete candidates."""
        exported = replace(
            policy,
            owner_path=self._export_owner_path(module.name, export.namespace, export.name),
            python_name=export.name,
        )
        return self._overload_plan(
            module.name,
            export.namespace,
            exported,
            functions,
            private_name=self._module_overload_callable_name,
        )

    @staticmethod
    def _module_overload_callable_name(name: str, index: int) -> str:
        """Return one private Python export for a module-overload candidate."""
        stem = name.strip("_").casefold() or "call"
        return f"_x2py_overload_{stem}_{index}"

    @staticmethod
    def _module_function_policy(function: models.SemanticFunction) -> FunctionWrapperPolicy | None:
        """Return a public function plan policy, excluding class-only root targets."""
        policy = function.metadata.get(models.RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA)
        if isinstance(policy, FunctionWrapperPolicy) and not policy.module_export:
            return None
        return completed_function_wrapper_policy(function)

    def _variables_by_namespace(
        self,
        module: models.SemanticModule,
    ) -> dict[tuple[str, ...], list[ModuleVariablePlan]]:
        """Group exported module-variable plans by completed Python namespace."""
        variables = defaultdict(list)
        for variable in module.variables:
            if variable.visibility != "public":
                continue
            policy = completed_module_variable_policy(variable)
            exports_by_namespace = defaultdict(list)
            for export in policy.python_exports:
                exports_by_namespace[export.namespace].append(export.name)
            for namespace, python_names in exports_by_namespace.items():
                variables[namespace].append(
                    self._module_variable_plan(policy, namespace, tuple(python_names), module.name)
                )
        return variables

    def _complete_generated_symbols(
        self,
        functions: dict[tuple[str, ...], list[FunctionPlan]],
        variables: dict[tuple[str, ...], list[ModuleVariablePlan]],
    ) -> None:
        """Keep unique symbols short and qualify only colliding local names."""
        entries = (*self._planned_items(functions), *self._planned_items(variables))
        counts = Counter(item.symbol_name.casefold() for _namespace, item in entries)
        for namespace, item in entries:
            if counts[item.symbol_name.casefold()] > 1:
                item.symbol_name = self._symbol_name(namespace, item.symbol_name)
        self._qualify_variable_bridge_collisions(functions, variables)

    def _qualify_variable_bridge_collisions(
        self,
        functions: dict[tuple[str, ...], list[FunctionPlan]],
        variables: dict[tuple[str, ...], list[ModuleVariablePlan]],
    ) -> None:
        """Qualify a variable helper when its get/set spelling collides with a function."""
        for namespace, namespace_variables in variables.items():
            function_symbols = {function.symbol_name for function in functions[namespace]}
            self._qualify_namespace_variable_helpers(namespace, namespace_variables, function_symbols)

    def _qualify_namespace_variable_helpers(
        self,
        namespace: tuple[str, ...],
        variables: list[ModuleVariablePlan],
        function_symbols: set[str],
    ) -> None:
        """Resolve get/set helper collisions inside one Python namespace."""
        for variable in variables:
            helper_symbols = {f"get_{variable.symbol_name}", f"set_{variable.symbol_name}"}
            if function_symbols & helper_symbols:
                variable.symbol_name = self._symbol_name(namespace, variable.symbol_name)

    def _planned_items(self, grouped: dict[tuple[str, ...], list]) -> tuple[tuple[tuple[str, ...], object], ...]:
        """Flatten namespace groups while retaining each item's namespace."""
        return tuple((namespace, item) for namespace, items in grouped.items() for item in items)

    def _module_variable_plan(
        self,
        policy: ModuleVariablePolicy,
        namespace: tuple[str, ...],
        python_names: tuple[str, ...],
        module_name: str,
    ) -> ModuleVariablePlan:
        getter_role = self._module_getter_role(policy)
        setter_role = f"{policy.owner_path}:setter" if policy.setter_action is SetterAction.WRITE_THROUGH else None
        plan = ModuleVariablePlan(
            owner_path=self._export_owner_path(module_name, namespace, python_names[0]),
            symbol_name=policy.native_name.casefold(),
            semantic_type_name=policy.semantic_type_name,
            datatype_family=self._transfer_datatype_family(
                policy.semantic_type_name,
                policy.derived.handoff if policy.derived is not None else None,
            ),
            binding=BindingModuleVariablePlan(
                python_names=python_names,
                getter_action=policy.getter_action,
                setter_action=policy.setter_action,
                initializer=policy.initializer,
                constant_value=policy.constant_value,
            ),
            bridge=BridgeModuleVariablePlan(
                native_name=policy.native_name,
                native_module=policy.native_module,
                getter_action=policy.getter_action,
                native_assignment=policy.native_assignment,
                descriptor_kind=policy.descriptor_kind,
                getter_role=getter_role,
                setter_role=setter_role,
            ),
            array=self._array_plan(policy.array, policy.owner_path),
            native_array_handle=self._native_array_handle_plan(policy.native_array_handle, policy.owner_path),
            derived=(
                DerivedModuleObjectPlan(
                    handoff=self._derived_handoff_plan(policy.derived.handoff),
                    access=policy.derived.access,
                    replacement=policy.derived.replacement,
                    member_paths=tuple(
                        DerivedMemberPathPlan(
                            path=member.path,
                            native_path=member.native_path,
                            declaring_type_name=member.declaring_type_name,
                            declaring_type_identity=member.declaring_type_identity,
                            field=self._derived_field_plan(member.field),
                        )
                        for member in policy.derived.member_paths
                    ),
                )
                if policy.derived is not None
                else None
            ),
            docstring="",
        )
        plan.docstring = self.docstrings.module_variable(plan)
        return plan

    @staticmethod
    def _module_getter_role(policy: ModuleVariablePolicy) -> str | None:
        """Name a whole-value getter only when completed policy crosses one."""
        if policy.getter_action is ModuleGetterAction.CONSTANT_VALUE:
            return None
        if policy.derived is not None and policy.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY:
            return None
        return f"{policy.owner_path}:getter"

    def _function_plan(
        self,
        policy: FunctionWrapperPolicy,
        export: PythonExportPolicy,
        module_name: str,
        *,
        public: bool = True,
    ) -> FunctionPlan:
        """Return one exported function plan from completed policy."""
        native_call_slots = self._native_slot_plans(policy)
        arguments = self._argument_plans(policy, native_call_slots)
        results = self._result_plans(policy, native_call_slots)
        status_error = self._status_error_plan(policy.status_error, native_call_slots)
        return FunctionPlan(
            owner_path=self._export_owner_path(module_name, export.namespace, export.name),
            symbol_name=export.name.casefold(),
            binding=BindingFunctionPlan(
                python_name=export.name,
                docstring=self.docstrings.function(
                    export.name,
                    arguments,
                    results,
                    status_error=status_error,
                ),
                hold_gil=policy.hold_gil,
                status_error=status_error,
                public=public,
            ),
            bridge=BridgeFunctionPlan(
                policy.native_name,
                policy.native_invocation,
                policy.native_operator,
                policy.external,
                policy.external_declaration,
                policy.native_module,
                policy.native_is_subroutine,
            ),
            class_call=self._class_call_plan(policy),
            arguments=arguments,
            results=results,
            native_call_slots=native_call_slots,
            available_roles=self._available_roles(arguments, results, native_call_slots),
            writeback_actions=tuple(self.visit(action) for action in policy.writeback_actions),
            cleanup_actions=tuple(self.visit(action) for action in policy.cleanup_actions),
            release_actions=tuple(self.visit(action) for action in policy.release_actions),
        )

    def _native_slot_plans(self, policy: FunctionWrapperPolicy) -> tuple[NativeCallSlotPlan, ...]:
        """Project ordered native call slots with their completed symbolic roles."""
        return tuple(
            self._native_slot_plan(slot, self._native_slot_role(slot, policy.results))
            for slot in policy.native_call_slots
        )

    @staticmethod
    def _class_call_plan(policy: FunctionWrapperPolicy) -> ClassCallPlan | None:
        """Project the optional class receiver action without backend inference."""
        if policy.class_call is None:
            return None
        return ClassCallPlan(
            kind=policy.class_call.kind,
            passed_object_position=policy.class_call.passed_object_position,
            invocation=policy.class_call.invocation,
            type_bound_name=policy.class_call.type_bound_name,
        )

    def _argument_plans(
        self,
        policy: FunctionWrapperPolicy,
        native_call_slots: tuple[NativeCallSlotPlan, ...],
    ) -> tuple[ArgumentTransferPlan, ...]:
        """Return declared transfers sharing the function's native-slot records."""
        return tuple(
            self.visit(
                argument,
                native_slot=self._planned_native_slot(native_call_slots, argument.owner_path),
            )
            for argument in policy.arguments
        )

    def _result_plans(
        self,
        policy: FunctionWrapperPolicy,
        native_call_slots: tuple[NativeCallSlotPlan, ...],
    ) -> tuple[ResultPlan, ...]:
        """Return ordered result consumers sharing completed native slots."""
        return tuple(
            self.visit(
                result,
                native_slot=self._result_native_slot(result, native_call_slots),
            )
            for result in sorted(policy.results, key=lambda item: item.result_position)
        )

    # Shared argument, result, and lifecycle transfer planning.
    def _visit_ArgumentPolicy(
        self,
        policy: ArgumentPolicy,
        *,
        native_slot: NativeCallSlotPlan,
    ) -> ArgumentTransferPlan:
        """Return one transfer whose backend views share one handoff role."""
        role = self._value_role(policy.owner_path)
        native_array_handle = native_slot.native_array_handle
        length_role = self._argument_length_role(policy)
        return ArgumentTransferPlan(
            owner_path=policy.owner_path,
            python_position=policy.python_position,
            native_position=policy.native_position,
            semantic_type_name=policy.semantic_type_name,
            datatype_family=self._transfer_datatype_family(
                policy.semantic_type_name,
                policy.derived,
                callback=policy.callback,
            ),
            character_length=policy.character_length,
            object_kind=policy.ownership.kind,
            ownership_owner=policy.ownership.owner,
            transfer_mode=policy.ownership.transfer,
            destruction_policy=policy.ownership.destruction,
            storage_mode=policy.storage_mode,
            boundary_storage_mode=policy.boundary_storage_mode,
            nullable=policy.nullable,
            mutates_native=policy.writable,
            projects_result=policy.projects_result,
            python_visible=policy.python_visible,
            result_position=policy.result_position,
            array=native_slot.array,
            native_array_actual=self._native_array_actual_plan(policy.native_array_actual),
            native_array_handle=native_array_handle,
            derived=native_slot.derived,
            derived_call=self._derived_call_plan(policy.derived_call),
            callback=self._callback_handoff_plan(policy.callback),
            polymorphic=self._polymorphic_dispatch_plan(policy.polymorphic),
            binding=self._binding_argument_plan(policy, role, length_role),
            bridge=self._bridge_argument_plan(policy, native_slot, native_array_handle, role, length_role),
            native_call_slot=native_slot,
            transformations=tuple(self.visit(item) for item in policy.transformations),
        )

    def _callback_handoff_plan(
        self,
        policy: CallbackHandoffPolicy | None,
    ) -> CallbackHandoffPlan | None:
        """Project one completed callback site and every backend symbol once."""
        if policy is None:
            return None
        stem = NativeSymbolNames.compact(policy.owner_path, "callback", limit=24)
        return CallbackHandoffPlan(
            owner_path=policy.owner_path,
            prototype_name=policy.prototype_name,
            prototype_module=policy.prototype_module,
            declaration_mode=policy.declaration_mode,
            context_type_symbol=f"x2py_callback_context_{stem}",
            context_current_symbol=f"x2py_callback_current_{stem}",
            adapter_symbol=f"x2py_callback_adapter_{stem}",
            trampoline_symbol=f"x2py_callback_trampoline_{stem}",
            abort_symbol=f"x2py_callback_abort_{stem}",
            arguments=tuple(self._callback_transfer_plan(item) for item in policy.arguments),
            result=self._callback_result_plan(policy.result),
            lifecycle=policy.lifecycle,
            thread_action=policy.thread_action,
            gil_actions=policy.gil_actions,
            fatal_action=policy.fatal_action,
        )

    def _callback_result_plan(self, policy: CallbackResultPolicy) -> CallbackResultPlan:
        """Project one callback result without rebuilding its transfer."""
        return CallbackResultPlan(
            transfer=(self._callback_transfer_plan(policy.transfer) if policy.transfer is not None else None),
            action=policy.action,
        )

    def _callback_transfer_plan(self, policy: CallbackTransferPolicy) -> CallbackTransferPlan:
        """Project callback ABI roles and exact derived backend identity."""
        array = self._array_plan(policy.array, policy.owner_path)
        return CallbackTransferPlan(
            owner_path=policy.owner_path,
            name=policy.name,
            semantic_type_name=policy.semantic_type_name,
            object_kind=policy.object_kind,
            rank=policy.rank,
            passed_by_value=policy.passed_by_value,
            abi=policy.abi,
            adapter_action=policy.adapter_action,
            python_action=policy.python_action,
            character_length=policy.character_length,
            array=array,
            derived_type_identity=policy.derived_type_identity,
            derived_backend_symbol=(
                self._derived_backend_symbol(policy.derived_type_identity)
                if policy.derived_type_identity is not None
                else None
            ),
            data_role=f"{policy.owner_path}:callback-data",
            extent_roles=(array.extent_roles if array is not None else ()),
            length_role=(f"{policy.owner_path}:callback-length" if policy.character_length is not None else None),
        )

    def _polymorphic_dispatch_plan(
        self,
        policy: PolymorphicDispatchPolicy | None,
    ) -> PolymorphicDispatchPlan | None:
        """Project concrete class identities into stable backend ABI codes."""
        if policy is None:
            return None
        return PolymorphicDispatchPlan(
            owner_path=policy.owner_path,
            variants=tuple(
                PolymorphicVariantPlan(
                    type_identity=identity,
                    backend_symbol=self._derived_backend_symbol(identity),
                    python_name=self._class_python_names[identity],
                    abi_code=index,
                )
                for index, identity in enumerate(policy.variants, start=1)
            ),
        )

    @staticmethod
    def _argument_length_role(policy: ArgumentPolicy) -> str | None:
        """Return the character length role selected by completed handoff policy."""
        if policy.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER:
            return f"{policy.owner_path}:length"
        return None

    @staticmethod
    def _binding_argument_plan(
        policy: ArgumentPolicy,
        role: str,
        length_role: str | None,
    ) -> BindingArgumentPlan:
        """Project the binding-facing view without revisiting semantic decisions."""
        return BindingArgumentPlan(
            python_name=policy.python_name,
            python_action=policy.python_barrier_action,
            codegen_action=policy.codegen_action,
            handoff_role=role,
            optional_mode=policy.optional_mode,
            nullable=policy.nullable,
            writable=policy.writable,
            descriptor_boundary=policy.descriptor_boundary,
            length_handoff_role=length_role,
        )

    def _bridge_argument_plan(
        self,
        policy: ArgumentPolicy,
        native_slot: NativeCallSlotPlan,
        native_array_handle: NativeArrayHandlePlan | None,
        role: str,
        length_role: str | None,
    ) -> BridgeArgumentPlan:
        """Project the bridge-facing view without revisiting semantic decisions."""
        return BridgeArgumentPlan(
            native_name=policy.native_name,
            native_action=policy.native_barrier_action,
            codegen_action=policy.codegen_action,
            handoff_mode=policy.handoff_mode,
            data_action=policy.bridge_data_action,
            copy_reason=policy.bridge_copy_reason,
            abi_position=native_slot.native_position,
            handoff_role=role,
            optional_mode=policy.optional_mode,
            presence_role=self._argument_presence_role(policy, native_array_handle),
            length_handoff_role=length_role,
            descriptor_output_role=self._required_descriptor_output_role(policy, "descriptor-output"),
            descriptor_output_presence_role=self._required_descriptor_output_role(
                policy,
                "descriptor-output-present",
            ),
        )

    @staticmethod
    def _argument_presence_role(
        policy: ArgumentPolicy,
        native_array_handle: NativeArrayHandlePlan | None,
    ) -> str | None:
        """Return the explicit optional or descriptor presence handoff role."""
        if native_array_handle is not None:
            return native_array_handle.handoff.presence_role
        if policy.optional_mode is OptionalMode.DESCRIPTOR:
            return f"{policy.owner_path}:present"
        return None

    @staticmethod
    def _required_descriptor_output_role(policy: ArgumentPolicy, suffix: str) -> str | None:
        """Return one required-descriptor copyout role when projection owns it."""
        if policy.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR and policy.projects_result:
            return f"{policy.owner_path}:{suffix}"
        return None

    def _visit_TransformationPolicy(self, policy: TransformationPolicy) -> TransformationPlan:
        """Mechanically retain one completed transformation owner and phase."""
        return TransformationPlan(
            phase=policy.phase,
            layer=policy.layer,
            action=policy.action,
            source_representation=policy.source_representation,
            target_representation=policy.target_representation,
            reason=policy.reason,
        )

    def _visit_LifecyclePolicy(
        self,
        policy: LifecyclePolicy,
    ) -> LifecycleActionPlan:
        """Return one transfer-owned action for function-wide ordering."""
        family = self._datatype_family(policy.semantic_type_name)
        binding = None
        bridge = None
        if policy.phase is WritebackPhase.NATIVE_MUTATION:
            bridge = BridgeLifecyclePlan(source_role=policy.source_role)
        else:
            binding = BindingLifecyclePlan(
                source_role=policy.source_role,
                codegen_action=policy.codegen_action,
                semantic_type_name=policy.semantic_type_name,
                datatype_family=family,
                result_position=policy.result_position,
                python_result_role=(
                    f"{policy.owner_path}:python-result"
                    if policy.operation is LifecycleOperation.WRITEBACK and policy.phase is WritebackPhase.COPY_OUT
                    else None
                ),
                operation=policy.operation,
            )
        return LifecycleActionPlan(
            owner_path=policy.owner_path,
            phase=policy.phase,
            source_role=policy.source_role,
            codegen_action=policy.codegen_action,
            semantic_type_name=policy.semantic_type_name,
            datatype_family=family,
            object_kind=policy.object_kind,
            result_position=policy.result_position,
            operation=policy.operation,
            binding=binding,
            bridge=bridge,
        )

    def _visit_ResultPolicy(
        self,
        policy: ResultPolicy,
        *,
        native_slot: NativeCallSlotPlan | None,
    ) -> ResultPlan:
        """Return one result with binding consumer and bridge producer views."""
        native_role = f"{policy.owner_path}:native-result"
        if policy.source_kind == "hidden_output" and native_slot is None:
            raise ValueError(f"{policy.owner_path!r} hidden result requires its completed native-call slot")
        array = self._result_array_plan(policy, native_slot)
        native_array_handle = self._result_native_array_handle_plan(policy, native_slot, array)
        return ResultPlan(
            owner_path=policy.owner_path,
            semantic_type_name=policy.semantic_type_name,
            datatype_family=self._transfer_datatype_family(policy.semantic_type_name, policy.derived),
            source_kind=policy.source_kind,
            result_position=policy.result_position,
            character_length=policy.character_length,
            object_kind=policy.ownership.kind,
            ownership_owner=policy.ownership.owner,
            transfer_mode=policy.ownership.transfer,
            destruction_policy=policy.ownership.destruction,
            storage_mode=policy.storage_mode,
            boundary_storage_mode=policy.boundary_storage_mode,
            nullable=policy.ownership.nullable,
            array=array,
            native_array_handle=native_array_handle,
            derived=(native_slot.derived if native_slot is not None else self._derived_handoff_plan(policy.derived)),
            binding=BindingResultPlan(
                policy.codegen_action,
                policy.python_barrier_action,
                f"{policy.owner_path}:python-result",
            ),
            bridge=BridgeResultPlan(
                policy.codegen_action,
                policy.native_barrier_action,
                policy.bridge_data_action,
                policy.bridge_copy_reason,
                native_role,
                policy.native_name,
                policy.native_position,
            ),
            native_call_slot=native_slot,
            scalar_descriptor=self._result_scalar_descriptor_plan(policy, native_slot),
            transformations=tuple(self.visit(item) for item in policy.transformations),
        )

    def _result_array_plan(
        self,
        policy: ResultPolicy,
        native_slot: NativeCallSlotPlan | None,
    ) -> ArrayHandoffPlan | None:
        """Reuse a hidden slot array or project one direct result array."""
        if native_slot is not None:
            return native_slot.array
        return self._array_plan(
            policy.array,
            policy.owner_path,
            include_buffer_roles=policy.native_array_handle is None,
        )

    def _result_native_array_handle_plan(
        self,
        policy: ResultPolicy,
        native_slot: NativeCallSlotPlan | None,
        array: ArrayHandoffPlan | None,
    ) -> NativeArrayHandlePlan | None:
        """Reuse a hidden slot handle or project one direct result handle."""
        if native_slot is not None:
            return native_slot.native_array_handle
        return self._native_array_handle_plan(policy.native_array_handle, policy.owner_path, array=array)

    def _result_scalar_descriptor_plan(
        self,
        policy: ResultPolicy,
        native_slot: NativeCallSlotPlan | None,
    ) -> ScalarDescriptorResultPlan | None:
        """Reuse exact hidden descriptor state or project one direct result."""
        if native_slot is not None:
            return native_slot.scalar_descriptor
        return self._scalar_descriptor_result_plan(policy.scalar_descriptor, policy.owner_path)

    def _native_slot_plan(self, slot: NativeCallSlotPolicy, role: str) -> NativeCallSlotPlan:
        """Return one shared ABI slot without selecting backend behavior."""
        array = self._array_plan(
            slot.array,
            slot.owner_path,
            include_buffer_roles=slot.native_barrier_action is NativeBarrierAction.PASS_ARRAY_BUFFER,
        )
        return NativeCallSlotPlan(
            owner_path=slot.owner_path,
            native_position=slot.native_position,
            source_kind=slot.source_kind,
            python_position=slot.python_position,
            python_name=slot.python_name,
            native_name=slot.native_name,
            value_kind=slot.value_kind,
            symbolic_role=role,
            native_action=slot.native_barrier_action,
            codegen_action=slot.codegen_action,
            bridge_data_action=slot.bridge_data_action,
            bridge_copy_reason=slot.bridge_copy_reason,
            object_kind=slot.object_kind,
            literal_type=slot.literal_type,
            literal_value=slot.literal_value,
            result_position=slot.result_position,
            semantic_type_name=slot.semantic_type_name,
            datatype_family=(
                self._transfer_datatype_family(
                    slot.semantic_type_name,
                    slot.derived,
                    callback=slot.callback,
                )
                if slot.semantic_type_name
                else None
            ),
            character_length=slot.character_length,
            array=array,
            native_array_handle=self._native_array_handle_plan(slot.native_array_handle, slot.owner_path, array=array),
            scalar_descriptor=self._scalar_descriptor_result_plan(slot.scalar_descriptor, slot.owner_path),
            derived=self._derived_handoff_plan(slot.derived),
        )

    # Derived-type argument, result, and module handoff planning.
    def _derived_handoff_plan(self, policy: DerivedHandoffPolicy | None) -> DerivedHandoffPlan | None:
        """Mechanically project one completed scalar-derived handoff."""
        if policy is None:
            return None
        return DerivedHandoffPlan(
            type_name=policy.type_name,
            type_identity=policy.type_identity,
            backend_symbol=self._derived_backend_symbol(policy.type_identity),
            native_type_name=policy.native_type_name,
            native_scope=policy.native_scope,
            origin=policy.origin,
            owner_retention=policy.owner_retention,
            release=policy.release,
            target_owner_retention=policy.target_owner_retention,
            target_release=policy.target_release,
            nullable=policy.nullable,
            native_handoff=policy.native_handoff,
            storage=policy.storage,
        )

    @staticmethod
    def _derived_call_plan(policy: DerivedCallPolicy | None) -> DerivedCallPlan | None:
        """Mechanically project completed dummy compatibility cases."""
        if policy is None:
            return None
        return DerivedCallPlan(
            dummy_category=policy.dummy_category,
            cases=tuple(
                DerivedCallCasePlan(
                    case.actual_storage,
                    case.action,
                    case.access,
                    case.abi_code,
                    case.requires_present,
                    case.target_lifetime,
                    case.failure_kind,
                    case.failure_message,
                )
                for case in policy.cases
            ),
            writeback=policy.writeback,
            status_role=policy.status_role,
            origin_identity_role=policy.origin_identity_role,
            acquisition_order=policy.acquisition_order,
            cleanup_order=policy.cleanup_order,
        )

    # Rank-zero scalar/string descriptor result planning.
    def _scalar_descriptor_result_plan(
        self,
        policy: ScalarDescriptorResultPolicy | None,
        owner_path: str,
    ) -> ScalarDescriptorResultPlan | None:
        """Mechanically project one nullable rank-zero descriptor result."""
        if policy is None:
            return None
        return ScalarDescriptorResultPlan(
            descriptor_kind=policy.descriptor_kind,
            runtime_length=policy.runtime_length,
            nullable=policy.nullable,
            copy_reason=policy.copy_reason,
            release_owner=policy.release_owner,
            presence_role=f"{owner_path}:present",
        )

    # Native-array-handle planning.
    def _native_array_actual_plan(self, policy: NativeArrayActualPolicy | None) -> NativeArrayActualPlan | None:
        """Mechanically project completed ordinary-array accepted sources."""
        if policy is None:
            return None
        return NativeArrayActualPlan(
            accepted_sources=policy.accepted_sources,
            dtype=policy.dtype,
            rank=policy.rank,
            shape=policy.shape,
            order=policy.order,
            writable=policy.writable,
            require_native_byte_order=policy.require_native_byte_order,
            require_aligned=policy.require_aligned,
            require_contiguous=policy.require_contiguous,
            flatten_storage=policy.flatten_storage,
            flat_axis=policy.flat_axis,
        )

    def _native_array_handle_plan(
        self,
        policy: NativeArrayHandleWrapperPolicy | None,
        owner_path: str,
        *,
        array: ArrayHandoffPlan | None = None,
    ) -> NativeArrayHandlePlan | None:
        """Project one typed handle policy and its subordinate descriptor roles."""
        if policy is None:
            return None
        array_plan = array or self._array_plan(policy.array, owner_path, include_buffer_roles=False)
        if array_plan is None:
            raise ValueError(f"Native array handle {owner_path!r} is missing its array data facet")
        return NativeArrayHandlePlan(
            descriptor_kind=policy.descriptor_kind,
            handle_kind=policy.handle_kind,
            origin=policy.origin,
            owner=policy.owner,
            owner_retention=policy.owner_retention,
            descriptor_ownership=policy.descriptor_ownership,
            borrowed=policy.borrowed,
            getter_behavior=policy.getter_behavior,
            setter_action=policy.setter_action,
            native_assignment=policy.native_assignment,
            output_projection=policy.output_projection,
            result_allocation=policy.result_allocation,
            release=policy.release,
            target_lifetime=policy.target_lifetime,
            destroy_behavior=policy.destroy_behavior,
            extraction_action=policy.extraction_action,
            descriptor_interop=policy.descriptor_interop,
            nullable=policy.nullable,
            optional_absent=policy.optional_absent,
            storage_mode=policy.storage_mode,
            operations=policy.operations,
            required_headers=policy.required_headers,
            array=array_plan,
            handoff=self._native_descriptor_handoff_plan(policy.handoff, owner_path, policy.operations),
        )

    def _native_descriptor_handoff_plan(
        self,
        policy: NativeDescriptorHandoffPolicy,
        owner_path: str,
        operations,
    ) -> NativeDescriptorHandoffPlan:
        """Name descriptor facts once for binding, bridge, and lifecycle consumers."""
        fact_packed = policy.abi is NativeDescriptorHandoffABI.FACT_PACKED_CALL_LOCAL
        return NativeDescriptorHandoffPlan(
            abi=policy.abi,
            descriptor_pointer_role=self._native_descriptor_pointer_role(policy, owner_path),
            base_addr_role=self._native_descriptor_fact_role(owner_path, "base-addr", fact_packed),
            elem_len_role=self._native_descriptor_fact_role(owner_path, "elem-len", fact_packed),
            rank_role=self._native_descriptor_fact_role(owner_path, "descriptor-rank", fact_packed),
            lower_bound_roles=self._native_descriptor_axis_roles(owner_path, policy.rank, "lower-bound", fact_packed),
            extent_roles=self._native_descriptor_axis_roles(owner_path, policy.rank, "descriptor-extent", fact_packed),
            stride_multiplier_roles=self._native_descriptor_axis_roles(
                owner_path, policy.rank, "stride-multiplier", fact_packed
            ),
            presence_role=self._native_descriptor_presence_role(policy, owner_path),
            owner_storage_role=self._native_descriptor_owner_role(policy, owner_path),
            operation_roles=tuple((operation, f"{owner_path}:operation:{operation.value}") for operation in operations),
        )

    def _native_descriptor_pointer_role(
        self,
        policy: NativeDescriptorHandoffPolicy,
        owner_path: str,
    ) -> str | None:
        """Name call-local or direct descriptor storage when one crosses the ABI."""
        if policy.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE:
            return None
        return f"{owner_path}:descriptor"

    def _native_descriptor_fact_role(self, owner_path: str, label: str, enabled: bool) -> str | None:
        """Name one fact-packed scalar descriptor field."""
        return f"{owner_path}:{label}" if enabled else None

    def _native_descriptor_presence_role(
        self,
        policy: NativeDescriptorHandoffPolicy,
        owner_path: str,
    ) -> str | None:
        """Name optional descriptor presence separately from allocation state."""
        return f"{owner_path}:descriptor-present" if policy.optional_presence else None

    def _native_descriptor_owner_role(
        self,
        policy: NativeDescriptorHandoffPolicy,
        owner_path: str,
    ) -> str | None:
        """Name persistent wrapper-owned descriptor storage."""
        if policy.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE:
            return f"{owner_path}:owner-storage"
        return None

    def _native_descriptor_axis_roles(
        self,
        owner_path: str,
        rank: int,
        label: str,
        enabled: bool,
    ) -> tuple[str, ...]:
        """Name one standard-descriptor field role per declared axis."""
        if not enabled:
            return ()
        return tuple(f"{owner_path}:{label}:{axis}" for axis in range(rank))

    # Ordinary-array buffer and raw-address planning.
    def _array_plan(
        self,
        policy: ArrayHandoffPolicy | None,
        owner_path: str,
        *,
        include_buffer_roles: bool = True,
    ) -> ArrayHandoffPlan | None:
        """Mechanically add only the ABI roles selected by completed transport."""
        if policy is None:
            return None
        abi_rank, runtime_rank_role, itemsize_role = self._array_transport_roles(
            policy,
            owner_path,
            include_buffer_roles,
        )
        return ArrayHandoffPlan(
            rank=policy.rank,
            shape=policy.shape,
            axes=policy.axes,
            order=policy.order,
            native_order=policy.native_order,
            contiguous=policy.contiguous,
            flatten_python_storage=policy.flatten_python_storage,
            flat_axis=policy.flat_axis,
            itemsize=policy.itemsize,
            category=policy.category,
            data_role=self._value_role(owner_path),
            extent_roles=tuple(f"{owner_path}:extent:{axis}" for axis in range(abi_rank)),
            extent_reference_roles=self._array_extent_reference_roles(owner_path, policy.extent_references),
            upper_bound_roles=self._array_layout_roles(owner_path, abi_rank, policy.contiguous, "upper-bound"),
            stride_roles=self._array_layout_roles(owner_path, abi_rank, policy.contiguous, "stride"),
            runtime_rank_role=runtime_rank_role,
            itemsize_role=itemsize_role,
        )

    def _array_transport_roles(
        self,
        policy: ArrayHandoffPolicy,
        owner_path: str,
        include_buffer_roles: bool,
    ) -> tuple[int, str | None, str | None]:
        """Return packed-buffer roles or the raw-address empty role set."""
        if not include_buffer_roles:
            return 0, None, None
        return (
            self._array_abi_rank(policy),
            self._array_runtime_rank_role(policy, owner_path),
            self._array_itemsize_role(policy, owner_path),
        )

    def _array_abi_rank(self, policy: ArrayHandoffPolicy) -> int:
        """Return the concrete ABI field count for fixed or assumed rank."""
        return 15 if policy.rank is None else policy.rank

    def _array_runtime_rank_role(self, policy: ArrayHandoffPolicy, owner_path: str) -> str | None:
        """Name the runtime-rank role only for assumed-rank arrays."""
        return f"{owner_path}:rank" if policy.rank is None else None

    def _array_itemsize_role(self, policy: ArrayHandoffPolicy, owner_path: str) -> str | None:
        """Name the itemsize role only for fixed-width character arrays."""
        return f"{owner_path}:itemsize" if policy.itemsize is not None else None

    def _array_layout_roles(
        self,
        owner_path: str,
        rank: int,
        contiguous: bool | None,
        label: str,
    ) -> tuple[str, ...]:
        """Name one ABI role per axis only for stride-aware layouts."""
        if contiguous is not False:
            return ()
        return tuple(f"{owner_path}:{label}:{axis}" for axis in range(rank))

    def _array_extent_reference_roles(
        self,
        owner_path: str,
        references: tuple[tuple[str, ...], ...],
    ) -> tuple[tuple[str, ...], ...]:
        """Resolve completed extent names to existing argument handoff roles."""
        function_path = owner_path.rsplit(".", 1)[0]
        return tuple(tuple(f"{function_path}.{name}:value" for name in axis) for axis in references)

    def _status_error_plan(
        self,
        policy: NativeStatusErrorPolicy | None,
        native_call_slots: tuple[NativeCallSlotPlan, ...],
    ) -> BindingStatusErrorPlan | None:
        """Project one completed native-status decision into binding roles."""
        if policy is None:
            return None
        roles = {slot.owner_path: slot.symbolic_role for slot in native_call_slots}
        try:
            status_role = roles[policy.status.owner_path]
            message_role = roles[policy.message.owner_path] if policy.message is not None else None
        except KeyError as error:
            raise ValueError(f"Completed native status output {error.args[0]!r} has no native-call slot") from None
        return BindingStatusErrorPlan(
            status_role=status_role,
            message_role=message_role,
            success=policy.success,
            exception_kind=policy.exception_kind,
        )

    def _planned_native_slot(
        self,
        native_call_slots: tuple[NativeCallSlotPlan, ...],
        owner_path: str,
    ) -> NativeCallSlotPlan:
        """Return the one shared editable native-call slot for an owner."""
        for slot in native_call_slots:
            if slot.owner_path == owner_path:
                return slot
        raise ValueError(f"{owner_path!r} is missing a completed native-call slot")

    def _result_native_slot(
        self,
        result_policy: ResultPolicy,
        native_call_slots: tuple[NativeCallSlotPlan, ...],
    ) -> NativeCallSlotPlan | None:
        """Return the completed slot for one hidden result, if any."""
        if result_policy.source_kind != "hidden_output":
            return None
        return self._planned_native_slot(native_call_slots, result_policy.owner_path)

    def _available_roles(
        self,
        arguments: tuple[ArgumentTransferPlan, ...],
        results: tuple[ResultPlan, ...],
        native_call_slots: tuple[NativeCallSlotPlan, ...],
    ) -> tuple[str, ...]:
        """Return symbolic roles available after the native call."""
        roles = [argument.binding.handoff_role for argument in arguments]
        roles.extend(
            role
            for argument in arguments
            for role in (
                argument.bridge.descriptor_output_role,
                argument.bridge.descriptor_output_presence_role,
            )
            if role is not None
        )
        roles.extend(self._native_result_roles(native_call_slots))
        roles.extend(self._direct_result_roles(results))
        return tuple(dict.fromkeys(roles))

    def _required_headers(self, namespaces: tuple[NamespacePlan, ...]) -> tuple[str, ...]:
        """Return the union of headers selected by completed handle plans."""
        handles = tuple(
            handle
            for namespace in namespaces
            for handle in self._namespace_native_array_handles(namespace)
            if handle is not None
        )
        headers = list(self._native_array_headers(handles))
        if self._requires_derived_descriptor_header(namespaces):
            headers.append(NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER)
        return tuple(dict.fromkeys(headers))

    @staticmethod
    def _requires_derived_descriptor_header(namespaces: tuple[NamespacePlan, ...]) -> bool:
        """Return whether one derived field uses a standard C descriptor callback."""
        descriptor_access = {
            DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR,
            DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE,
        }
        fields = (field for namespace in namespaces for derived in namespace.derived_types for field in derived.fields)
        return any(field.access in descriptor_access for field in fields)

    def _native_array_headers(self, handles: tuple[NativeArrayHandlePlan, ...]) -> tuple[str, ...]:
        """Deduplicate planned handle headers in encounter order."""
        return tuple(dict.fromkeys(header for handle in handles for header in handle.required_headers))

    def _namespace_native_array_handles(
        self,
        namespace: NamespacePlan,
    ) -> tuple[NativeArrayHandlePlan | None, ...]:
        """Return argument, result, and module handle plans for one namespace."""
        return (
            *(handle for function in namespace.functions for handle in self._function_native_array_handles(function)),
            *(variable.native_array_handle for variable in namespace.variables),
            *self._derived_field_native_array_handles(namespace),
        )

    @staticmethod
    def _derived_field_native_array_handles(
        namespace: NamespacePlan,
    ) -> tuple[NativeArrayHandlePlan | None, ...]:
        """Return descriptor handles subordinate to namespace-derived fields."""
        return tuple(field.native_array_handle for derived in namespace.derived_types for field in derived.fields)

    def _function_native_array_handles(
        self,
        function: FunctionPlan,
    ) -> tuple[NativeArrayHandlePlan | None, ...]:
        """Return datatype-varying handle owners for one function."""
        return (
            *(argument.native_array_handle for argument in function.arguments),
            *(result.native_array_handle for result in function.results),
        )

    def _native_result_roles(self, native_call_slots: tuple[NativeCallSlotPlan, ...]) -> tuple[str, ...]:
        """Return every role produced through a native result slot."""
        return tuple(slot.symbolic_role for slot in native_call_slots if slot.source_kind == "result")

    def _direct_result_roles(self, results: tuple[ResultPlan, ...]) -> tuple[str, ...]:
        """Return direct-return roles produced by the bridge function result."""
        return tuple(result.bridge.native_result_role for result in results if result.source_kind == "direct_return")

    def _datatype_family(self, semantic_type_name: str) -> DatatypeFamily:
        """Copy the backend-relevant family of one supported semantic type."""
        try:
            return _DATATYPE_FAMILIES[semantic_type_name]
        except KeyError:
            if semantic_type_name in getattr(self, "_derived_type_names", set()):
                return DatatypeFamily.DERIVED
            raise ValueError(f"Unsupported first-lane scalar type {semantic_type_name!r}") from None

    def _transfer_datatype_family(
        self,
        semantic_type_name: str,
        derived: DerivedHandoffPolicy | None,
        *,
        callback: CallbackHandoffPolicy | None = None,
    ) -> DatatypeFamily:
        """Select the derived family from its completed handoff, never a name guess."""
        if callback is not None:
            return DatatypeFamily.CALLBACK
        if derived is not None:
            return DatatypeFamily.DERIVED
        return self._datatype_family(semantic_type_name)

    def _namespace_paths(self, declared_paths: tuple[tuple[str, ...], ...]) -> tuple[tuple[str, ...], ...]:
        """Return root plus every declared namespace and required ancestor."""
        paths = {()}
        for path in declared_paths:
            paths.update(path[:depth] for depth in range(1, len(path) + 1))
        return tuple(sorted(paths, key=lambda item: (len(item), item)))

    def _namespace_owner_path(self, module_name: str, namespace: tuple[str, ...]) -> str:
        return ".".join((module_name, *namespace)) if namespace else module_name

    def _export_owner_path(
        self,
        module_name: str,
        namespace: tuple[str, ...],
        python_name: str,
    ) -> str:
        return ".".join((module_name, *namespace, python_name))

    def _symbol_name(self, namespace: tuple[str, ...], local_name: str) -> str:
        """Return the readable generated symbol stem implied by one export path."""
        return "_".join((*namespace, local_name)).casefold()

    def _value_role(self, owner_path: str) -> str:
        """Return the symbolic value role for one transfer owner."""
        return f"{owner_path}:value"

    def _native_slot_role(
        self,
        native_slot: NativeCallSlotPolicy,
        results: tuple[ResultPolicy, ...],
    ) -> str:
        """Return the symbolic role for one native-call slot."""
        if native_slot.source_kind == "literal":
            return f"{native_slot.owner_path}:literal"
        public_result = self._public_result_for_slot(native_slot, results)
        if public_result is not None:
            return f"{public_result.owner_path}:native-result"
        if native_slot.source_kind == "result":
            return f"{native_slot.owner_path}:native-result"
        return self._value_role(native_slot.owner_path)

    def _public_result_for_slot(
        self,
        native_slot: NativeCallSlotPolicy,
        results: tuple[ResultPolicy, ...],
    ) -> ResultPolicy | None:
        """Return the Python-visible hidden result carried by one native slot."""
        if native_slot.source_kind != "result":
            return None
        return next(
            (
                result
                for result in results
                if result.source_kind == "hidden_output" and result.owner_path == native_slot.owner_path
            ),
            None,
        )
