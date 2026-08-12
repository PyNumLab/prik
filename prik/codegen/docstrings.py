"""Render Python-facing documentation from completed wrapper-plan records.

``WrapperDocstringBuilder`` turns completed plan facts into compact NumPy-style
docstrings for generated modules, functions, classes, descriptors, overloads,
and constructors.  It is a presentation-only projection: ownership, optional
behavior, shape, and lifecycle decisions are read from the plan and never
re-derived from native declarations or backend output.
"""

from __future__ import annotations

from prik.policy.ownership import OwnershipOwner, SetterAction, TransferMode
from prik.policy.models import (
    ClassConstructorKind,
    ModuleGetterAction,
    NativeArrayDescriptorKind,
    OptionalMode,
)
from prik.planning.models import (
    ArgumentTransferPlan,
    ArrayHandoffPlan,
    BindingStatusErrorPlan,
    CallbackHandoffPlan,
    CallbackTransferPlan,
    ClassMethodPlan,
    ClassSurfacePlan,
    ConstructorPlan,
    DatatypeFamily,
    DerivedFieldPlan,
    FunctionPlan,
    ModulePlan,
    ModuleVariablePlan,
    NamespacePlan,
    OverloadPlan,
    ResultPlan,
)
from prik.semantics.scalar_types import BOOLEAN_SEMANTIC_TYPE_NAMES


_SCALAR_TYPES = {
    **dict.fromkeys(BOOLEAN_SEMANTIC_TYPE_NAMES, "bool"),
    "Int8": "int8",
    "Int16": "int16",
    "Int32": "int32",
    "Int64": "int64",
    "Float32": "float32",
    "Float64": "float64",
    "Complex64": "complex64",
    "Complex128": "complex128",
    "String": "str",
}

_UNKNOWN_EXTENTS = frozenset({"", ":", "::", "*", ".."})


class WrapperDocstringBuilder:
    """Build compact, public NumPy-style documentation from completed plans.

    :meth:`render` is called by ``WrapperGenerator`` after planning. It
    fills unresolved documentation fields in dependency order while preserving
    explicit editable-plan strings, including an intentionally empty string.
    The remaining public methods render individual plan records without
    changing policy or transfer facts.
    """

    def render(self, plan: ModulePlan) -> ModulePlan:
        """Fill unresolved Python-facing documentation on one editable plan.

        Child callables, fields, overloads, constructors, and variables are
        rendered before their class and namespace summaries. Existing strings
        are explicit plan overrides and remain unchanged. The same plan is
        returned for generation-stage chaining.
        """
        for namespace in plan.namespaces:
            self._render_namespace(plan.owner_path, namespace)
        return plan

    def _render_namespace(self, module_name: str, namespace: NamespacePlan) -> None:
        """Render one namespace's children before its aggregate summary."""
        for function in namespace.functions:
            self._render_function(function)
        for derived_type in namespace.derived_types:
            for field in derived_type.fields:
                self._render_field(field)
        for variable in namespace.variables:
            self._render_module_variable(variable)
        for overload in namespace.overloads:
            self._render_overload(overload)

        derived_types = {item.type_identity: item for item in namespace.derived_types}
        for surface in namespace.classes:
            derived_type = derived_types.get(surface.type_identity)
            self._render_class_surface(surface, () if derived_type is None else derived_type.fields)

        if namespace.docstring is None:
            namespace.docstring = self.namespace(
                module_name,
                namespace.python_path,
                namespace.functions,
                namespace.variables,
                namespace.classes,
                namespace.overloads,
            )

    def _render_function(self, function: FunctionPlan) -> None:
        """Render one ordinary callable unless the editable plan overrides it."""
        if function.binding.docstring is None:
            function.binding.docstring = self.function(
                function.binding.python_name,
                function.arguments,
                function.results,
                status_error=function.binding.status_error,
            )

    def _render_field(self, field: DerivedFieldPlan) -> None:
        """Render one class field unless the editable plan overrides it."""
        if field.docstring is None:
            field.docstring = self.field(field)

    def _render_module_variable(self, variable: ModuleVariablePlan) -> None:
        """Render one module attribute unless the editable plan overrides it."""
        if variable.docstring is None:
            variable.docstring = self.module_variable(variable)

    def _render_overload(self, overload: OverloadPlan) -> None:
        """Render overload candidates before their public dispatcher summary."""
        for candidate in overload.candidates:
            self._render_function(candidate)
        if overload.docstring is None:
            overload.docstring = self.overload(overload)

    def _render_class_surface(
        self,
        surface: ClassSurfacePlan,
        fields: tuple[DerivedFieldPlan, ...],
    ) -> None:
        """Render one class's dependent records before its aggregate summary."""
        for field in fields:
            self._render_field(field)
        for method in surface.methods:
            self._render_function(method.function)
            if method.docstring is None:
                method.docstring = self.method(method)
        for overload in surface.overloads:
            self._render_overload(overload)

        constructor = surface.constructor
        if constructor.target is not None:
            self._render_function(constructor.target)
        if constructor.overload is not None:
            self._render_overload(constructor.overload)
        if constructor.docstring is None:
            constructor.docstring = self.constructor(surface.python_names[0], constructor, fields)
        if surface.docstring is None:
            surface.docstring = self.class_surface(
                surface.python_names[0],
                surface.type_identity[1],
                constructor,
                fields,
                surface.methods,
                surface.overloads,
            )

    # Public entrypoints: namespace and class summaries.
    def namespace(
        self,
        module_name: str,
        path: tuple[str, ...],
        functions: tuple[FunctionPlan, ...],
        variables: tuple[ModuleVariablePlan, ...],
        classes,
        overloads: tuple[OverloadPlan, ...],
    ) -> str:
        """Render one namespace summary from its completed public plan records.

        ``module_name`` and ``path`` select the display name; functions,
        variables, classes, and overloads supply the summary entries.  Private
        generated functions are omitted, while ordering within each supplied
        collection is retained.  The resulting string is stored on the
        namespace plan and later attached to the generated module.
        """
        display_name = path[-1] if path else module_name
        lines = [display_name]
        callable_lines = (
            *(self._first_line(function.binding.docstring) for function in functions if function.binding.public),
            *(self._first_line(overload.docstring) for overload in overloads),
        )
        self._append_section(
            lines,
            "Module Attributes",
            tuple(line for variable in variables for line in self._module_variable_summary_lines(variable)),
        )
        self._append_section(lines, "Functions", callable_lines)
        self._append_section(lines, "Classes", tuple(name for surface in classes for name in surface.python_names))
        return "\n".join(lines)

    def class_surface(
        self,
        python_name: str,
        native_type_name: str,
        constructor: ConstructorPlan,
        fields: tuple[DerivedFieldPlan, ...],
        methods: tuple[ClassMethodPlan, ...],
        overloads: tuple[OverloadPlan, ...],
    ) -> str:
        """Render the public summary for one opaque native-wrapper class.

        The supplied constructor, fields, methods, and overloads are already
        completed plan records.  Only public methods appear in the summary;
        their pre-rendered first lines preserve the planner's method order.
        The returned text is normally attached to the generated Python class.
        """
        lines = [python_name, "", f"Opaque wrapper for native type {native_type_name}."]
        self._append_section(lines, "Constructor", (self._first_line(constructor.docstring),))
        self._append_section(lines, "Fields", tuple(self._first_line(field.docstring) for field in fields))
        self._append_section(
            lines,
            "Methods",
            (
                *(self._first_line(method.docstring) for method in methods if method.public),
                *(self._first_line(overload.docstring) for overload in overloads),
            ),
        )
        return "\n".join(lines)

    # Public entrypoints: callable, overload, and constructor documentation.
    def function(
        self,
        python_name: str,
        arguments: tuple[ArgumentTransferPlan, ...],
        results: tuple[ResultPlan, ...],
        *,
        status_error: BindingStatusErrorPlan | None = None,
        excluded_native_position: int | None = None,
    ) -> str:
        """Render a callable signature, parameter, return, and exception sections.

        ``arguments`` and ``results`` are completed transfer records.  An
        optional excluded native position removes a passed-object receiver from
        a method's public signature.  The returned string is attached to a
        function plan or method surface; it does not validate or alter the
        transfer records.
        """
        # Select public arguments and outputs before rendering their shared summary.
        visible = self._visible_arguments(arguments, excluded_native_position)
        outputs = self._documented_outputs(arguments, results)
        lines = [self._callable_signature(python_name, visible, outputs)]

        # Append sections in the stable public order used by generated callables.
        self._append_section(
            lines,
            "Parameters",
            tuple(line for argument in visible for line in self._argument_lines(argument)),
        )
        self._append_section(
            lines,
            "Returns",
            tuple(line for output in outputs for line in self._output_lines(output, arguments)) or ("None",),
        )
        self._append_section(lines, "Raises", self._raise_lines(visible, outputs, status_error))
        return "\n".join(lines)

    def method(self, method: ClassMethodPlan) -> str:
        """Render one class method, omitting its passed-object transfer.

        ``method`` carries both its public method metadata and underlying
        function plan.  Instance methods add the established in-place update
        note when their completed receiver is mutable; static methods preserve
        the base callable documentation unchanged.
        """
        docstring = self.function(
            method.python_name,
            method.function.arguments,
            method.function.results,
            status_error=method.function.binding.status_error,
            excluded_native_position=method.passed_object_position,
        )
        if method.passed_object_position is None:
            return docstring
        receiver = self._argument_at_native_position(method.function.arguments, method.passed_object_position)
        if receiver.mutates_native:
            docstring += "\n\nNotes\n-----\nUpdates the wrapped native instance in place."
        return docstring

    def overload(self, overload: OverloadPlan) -> str:
        """Render an overload dispatcher without exposing its private candidates.

        Candidate functions provide exact signatures, while their paired
        passed-object flags determine whether a receiver is omitted.  The
        returned text documents public dispatch behavior and its TypeError
        contract without changing candidate selection policy.
        """
        signatures = tuple(
            self._candidate_signature(overload.python_name, candidate, passed)
            for candidate, passed in zip(
                overload.candidates,
                overload.candidate_passed_objects,
                strict=True,
            )
        )
        lines = [f"{overload.python_name}(*args, **kwargs)"]
        self._append_section(lines, "Supported Signatures", signatures)
        self._append_section(
            lines,
            "Raises",
            ("TypeError", "    If no supported signature matches the supplied arguments."),
        )
        self._append_section(lines, "Notes", self._overload_notes(overload))
        return "\n".join(lines)

    def constructor(
        self,
        python_name: str,
        constructor: ConstructorPlan,
        fields: tuple[DerivedFieldPlan, ...],
    ) -> str:
        """Render the completed construction route for one generated class.

        ``constructor.kind`` selects the documented route: absent, default
        fields, one bound procedure, or an overload set.  The builder adds the
        shared return and TypeError sections after a supported route, returning
        text that the class emitter attaches to ``__new__`` or ``__init__``.
        """
        if constructor.kind is ClassConstructorKind.ABSENT:
            return self._absent_constructor(python_name, constructor)

        # Select the route already completed by policy; this is documentation dispatch only.
        handlers = {
            ClassConstructorKind.DEFAULT_FIELDS: self._default_constructor,
            ClassConstructorKind.BOUND_PROCEDURE: self._bound_constructor,
            ClassConstructorKind.OVERLOAD_SET: self._overloaded_constructor,
        }
        handler = handlers.get(constructor.kind)
        if handler is None:  # pragma: no cover - policy validation owns the enum envelope
            raise ValueError(f"Unsupported constructor kind: {constructor.kind.value}")
        lines = handler(python_name, constructor, fields)

        # Every supported route shares the same public result and argument-error contract.
        self._append_section(lines, "Returns", (python_name, "    New wrapper-owned native instance."))
        self._append_section(
            lines,
            "Raises",
            ("TypeError", "    If the supplied arguments do not satisfy the constructor contract."),
        )
        return "\n".join(lines)

    @staticmethod
    def _absent_constructor(python_name: str, constructor: ConstructorPlan) -> str:
        """Render the rejection-only documentation for an absent constructor.

        ``python_name`` supplies the displayed call while the completed
        constructor may supply a custom rejection message.  The returned text
        contains only the stable TypeError contract and does not modify class
        construction behavior.
        """
        return "\n".join(
            (
                f"{python_name}(*args, **kwargs)",
                "",
                "Raises",
                "------",
                "TypeError",
                f"    {constructor.rejection_message or 'Direct construction is disabled.'}",
            )
        )

    def _default_constructor(
        self,
        python_name: str,
        constructor: ConstructorPlan,
        fields: tuple[DerivedFieldPlan, ...],
    ) -> list[str]:
        """Render the editable-field portion of a default constructor.

        Constructor field metadata selects the subset and order of supplied
        field plans.  Missing plan fields remain absent as established by the
        completed constructor route; the returned mutable line list receives
        common return/raise sections from the caller.
        """
        by_name = {field.name: field for field in fields}
        parameters = tuple(by_name[item.name] for item in constructor.fields if item.name in by_name)
        lines = [self._keyword_field_signature(python_name, constructor, parameters)]
        self._append_section(
            lines,
            "Parameters",
            tuple(line for field in parameters for line in self._constructor_field_lines(field)),
        )
        return lines

    def _bound_constructor(
        self,
        python_name: str,
        constructor: ConstructorPlan,
        _fields: tuple[DerivedFieldPlan, ...],
    ) -> list[str]:
        """Render the signature and parameters for one bound-procedure constructor.

        The completed target function supplies public arguments and an optional
        passed-object position.  A missing target is inconsistent plan input
        and raises ``ValueError``; otherwise the caller appends shared sections
        to the returned line list.
        """
        target = constructor.target
        if target is None:
            raise ValueError(f"Bound constructor {python_name!r} has no target plan")
        passed = target.class_call.passed_object_position if target.class_call else None
        arguments = self._visible_arguments(target.arguments, passed)
        lines = [self._signature(python_name, arguments, python_name)]
        self._append_section(
            lines,
            "Parameters",
            tuple(line for argument in arguments for line in self._argument_lines(argument)),
        )
        return lines

    def _overloaded_constructor(
        self,
        python_name: str,
        constructor: ConstructorPlan,
        _fields: tuple[DerivedFieldPlan, ...],
    ) -> list[str]:
        """Render public signatures for an overload-set constructor.

        Candidate/receiver pairs remain zipped in completed order and use the
        class name as their public result type.  A missing overload record is
        invalid plan input and raises ``ValueError``; common sections remain
        the responsibility of the caller.
        """
        overload = constructor.overload
        if overload is None:
            raise ValueError(f"Overloaded constructor {python_name!r} has no overload plan")
        signatures = tuple(
            self._candidate_signature(python_name, candidate, passed, result_type=python_name)
            for candidate, passed in zip(
                overload.candidates,
                overload.candidate_passed_objects,
                strict=True,
            )
        )
        lines = [f"{python_name}(*args, **kwargs) -> {python_name}"]
        self._append_section(lines, "Supported Signatures", signatures)
        return lines

    # Public entrypoints: module attributes and class fields.
    def module_variable(self, variable: ModuleVariablePlan) -> str:
        """Render a module-attribute summary for its owning namespace docstring.

        CPython cannot attach a separate descriptor docstring to these module
        attributes, so the returned lines are included in the namespace
        documentation.  Getter, setter, array-handle, and derived-object text
        comes directly from the completed variable plan.
        """
        name = variable.binding.python_names[0]
        nullable = variable.binding.getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
        lines = [f"{name} : {self._type(variable, nullable=nullable, signature=False)}"]
        lines.extend(self._array_lines(variable.array))
        if variable.binding.getter_action in {
            ModuleGetterAction.CONSTANT_VALUE,
            ModuleGetterAction.NATIVE_CONSTANT_VALUE,
            ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE,
        }:
            lines.append("    Read-only constant.")
        elif variable.binding.getter_action is ModuleGetterAction.BORROWED_ARRAY_VIEW:
            lines.append("    Native-owned borrowed view; mutations affect module storage.")
        elif variable.native_array_handle is not None:
            lines.append(f"    Persistent {variable.native_array_handle.descriptor_kind.value} descriptor handle.")
        elif variable.derived is not None:
            lines.append("    Live native module object.")
        if variable.binding.setter_action is SetterAction.REJECT_REPLACEMENT:
            lines.append("    Replacement assignment is not supported.")
        return "\n".join(lines)

    def field(self, field: DerivedFieldPlan) -> str:
        """Render one generated class-property docstring from its field plan.

        Array/handle lifetime and setter wording reflect the completed field
        access policy.  The string is later installed on the generated Python
        property; this builder does not alter native assignment or retention.
        """
        lines = [f"{field.name} : {self._type(field, nullable=False, signature=False)}"]
        lines.extend(self._array_lines(field.array))
        if field.native_array_handle is not None:
            lines.append(f"    Live {field.native_array_handle.descriptor_kind.value} array descriptor handle.")
            lines.append("    The parent wrapper retains the descriptor owner.")
        elif field.array is not None:
            lines.append("    Borrowed native view retained by the parent wrapper.")
        if field.setter_action is SetterAction.WRITE_THROUGH:
            lines.append("    Assignment writes through to native storage.")
        elif field.setter_action is SetterAction.REJECT_REPLACEMENT:
            lines.append("    Replacement assignment is not supported.")
        else:
            lines.append("    Read-only attribute.")
        return "\n".join(lines)

    # Shared callable signatures, public sections, and output descriptions.
    @staticmethod
    def _append_section(lines: list[str], heading: str, body: tuple[str, ...]) -> None:
        """Append one nonempty NumPy-style section to an in-progress line list.

        ``lines`` is mutated only when ``body`` contains public content.  The
        helper preserves the established blank-line, heading, underline, and
        body ordering; empty sections intentionally leave the list unchanged.
        """
        if not body:
            return
        lines.extend(("", heading, "-" * len(heading), *body))

    @staticmethod
    def _first_line(docstring: str | None) -> str:
        """Return the first summary line from rendered text or an empty string.

        Namespace and class summaries use this to embed a callable's compact
        public signature.  It neither trims nor changes the supplied docstring
        beyond selecting its first split line.
        """
        return docstring.splitlines()[0] if docstring else ""

    def _callable_signature(
        self,
        name: str,
        arguments: tuple[ArgumentTransferPlan, ...],
        outputs: tuple[ArgumentTransferPlan | ResultPlan, ...],
    ) -> str:
        """Build the first-line callable signature from visible inputs and outputs.

        ``arguments`` are already filtered for public visibility and ``outputs``
        are ordered public result producers.  The helper delegates type wording
        to the shared signature/result formatters and has no plan side effects.
        """
        return self._signature(name, arguments, self._result_summary(outputs))

    def _signature(
        self,
        name: str,
        arguments: tuple[ArgumentTransferPlan, ...],
        result_type: str,
    ) -> str:
        """Render one untyped public signature with its prepared result text.

        Parameter order is the supplied tuple order, which callers derive from
        completed Python positions.  ``result_type`` is already rendered so
        this helper only joins the final stable first line.
        """
        parameters = ", ".join(self._signature_parameter(argument) for argument in arguments)
        return f"{name}({parameters}) -> {result_type}"

    @staticmethod
    def _signature_parameter(argument: ArgumentTransferPlan) -> str:
        """Render one public parameter name and optional default marker.

        Required values keep their Python name unchanged.  Any completed
        optional mode renders the established ``= ...`` marker without
        inspecting native defaults or changing optionality.
        """
        name = argument.binding.python_name
        if argument.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}:
            return f"{name}=..."
        return name

    def _candidate_signature(
        self,
        name: str,
        candidate: FunctionPlan,
        passed_object: bool,
        *,
        result_type: str | None = None,
    ) -> str:
        """Render one typed overload candidate without exposing private names.

        ``passed_object`` determines whether the completed receiver position is
        removed.  The candidate's public outputs produce the result summary
        unless a constructor supplies its explicit ``result_type``.
        """
        passed = candidate.class_call.passed_object_position if passed_object and candidate.class_call else None
        arguments = self._visible_arguments(candidate.arguments, passed)
        outputs = self._documented_outputs(candidate.arguments, candidate.results)
        parameters = ", ".join(self._typed_signature_parameter(argument) for argument in arguments)
        return f"{name}({parameters}) -> {result_type or self._result_summary(outputs)}"

    @staticmethod
    def _overload_candidates(overload: OverloadPlan):
        """Yield overload candidates paired with completed receiver flags.

        The strict zip preserves candidate order and exposes a length mismatch
        as the normal ``ValueError``.  Callers consume this iterator for
        documentation-only receiver notes without changing dispatch policy.
        """
        return zip(overload.candidates, overload.candidate_passed_objects, strict=True)

    @staticmethod
    def _argument_at_native_position(
        arguments: tuple[ArgumentTransferPlan, ...],
        native_position: int,
    ) -> ArgumentTransferPlan:
        """Return the argument at one completed native receiver position.

        The caller supplies a function's transfer tuple and its selected native
        position.  The first matching transfer is returned; a missing receiver
        raises the normal ``StopIteration`` because the plan is inconsistent.
        """
        return next(argument for argument in arguments if argument.native_position == native_position)

    def _candidate_mutates_receiver(self, candidate: FunctionPlan, passed_object: bool) -> bool:
        """Return whether one overload candidate mutates its passed-object receiver.

        Static candidates and candidates without class-call metadata are false.
        Instance candidates reuse the completed receiver transfer and return
        its stored mutability fact without deriving behavior from method names.
        """
        if not passed_object or candidate.class_call is None:
            return False
        receiver = self._argument_at_native_position(candidate.arguments, candidate.class_call.passed_object_position)
        return receiver.mutates_native

    def _overload_notes(self, overload: OverloadPlan) -> tuple[str, ...]:
        """Render shared class-overload notes from completed receiver metadata.

        Module overloads return no notes.  Class-owned overloads describe their
        native-instance dispatch and add the established update note when any
        candidate mutates its receiver; candidate order and state stay intact.
        """
        if not any(overload.candidate_passed_objects):
            return ()
        notes = ["Dispatches to a native operation on the wrapped instance."]
        if any(
            self._candidate_mutates_receiver(candidate, passed)
            for candidate, passed in self._overload_candidates(overload)
        ):
            notes.append("Updates the wrapped native instance in place.")
        return tuple(notes)

    def _typed_signature_parameter(self, argument: ArgumentTransferPlan) -> str:
        """Render one typed overload parameter and optional default marker.

        The type and nullability are read from the completed transfer.  This
        richer spelling differentiates public overload candidates while using
        the same optional marker as ordinary callable signatures.
        """
        parameter = f"{argument.binding.python_name}: {self._type(argument, nullable=argument.binding.nullable, signature=True)}"
        if argument.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}:
            return f"{parameter} = ..."
        return parameter

    @staticmethod
    def _visible_arguments(
        arguments: tuple[ArgumentTransferPlan, ...],
        excluded_native_position: int | None,
    ) -> tuple[ArgumentTransferPlan, ...]:
        """Return public arguments in completed Python-position order.

        The passed-object position is excluded only when supplied.  Arguments
        marked non-public are always omitted, preserving method and callback
        signatures without mutating their underlying function plan.
        """
        return tuple(
            argument
            for argument in sorted(arguments, key=lambda item: item.python_position)
            if argument.python_visible and argument.native_position != excluded_native_position
        )

    @staticmethod
    def _documented_outputs(
        arguments: tuple[ArgumentTransferPlan, ...],
        results: tuple[ResultPlan, ...],
    ) -> tuple[ArgumentTransferPlan | ResultPlan, ...]:
        """Merge projected arguments and declared results by public result position.

        Projected arguments are collected first; declared results at the same
        position take precedence, matching the established public projection.
        The returned tuple is sorted by position and leaves both input tuples
        unchanged.
        """
        by_position = {
            argument.result_position: argument
            for argument in arguments
            if argument.projects_result and argument.result_position is not None
        }
        by_position.update((result.result_position, result) for result in results)
        return tuple(by_position[position] for position in sorted(by_position))

    def _result_summary(self, outputs: tuple[ArgumentTransferPlan | ResultPlan, ...]) -> str:
        """Render the compact result type used by a callable's first line.

        Nullable argument outputs use their completed optional mode; result
        outputs use their stored nullability.  Zero, one, and multiple outputs
        render as ``None``, one type, or a typed tuple respectively.
        """
        types = tuple(
            self._type(
                output,
                nullable=(
                    output.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}
                    if isinstance(output, ArgumentTransferPlan)
                    else output.nullable
                ),
                signature=True,
            )
            for output in outputs
        )
        if not types:
            return "None"
        if len(types) == 1:
            return types[0]
        return f"tuple[{', '.join(types)}]"

    # Parameter, result, ownership, and exception details.
    def _argument_lines(self, argument: ArgumentTransferPlan) -> tuple[str, ...]:
        """Render the complete public parameter block for one transfer.

        The lines combine type, array shape, optionality, mutation, ownership,
        and descriptor facts in a fixed order.  All wording derives from the
        supplied completed transfer and returns a new tuple without mutation.
        """
        optional = argument.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}
        nullable = optional or argument.binding.nullable
        lines = [f"{argument.binding.python_name} : {self._type(argument, nullable=nullable, signature=False)}"]
        lines.extend(self._array_lines(argument.array))
        lines.extend(self._optional_lines(argument))
        lines.extend(self._mutation_lines(argument))
        if argument.datatype_family is DatatypeFamily.DERIVED or argument.array is not None:
            lines.extend(self._ownership_lines(argument.ownership_owner))
        if argument.native_array_handle is not None:
            lines.append(f"    Descriptor ownership: {argument.native_array_handle.descriptor_ownership.value}.")
        return tuple(lines)

    def _output_lines(
        self,
        output: ArgumentTransferPlan | ResultPlan,
        arguments: tuple[ArgumentTransferPlan, ...],
    ) -> tuple[str, ...]:
        """Render the complete public return block for one output producer.

        Projected arguments keep their Python name and optionality; declared
        results resolve a stable public result name.  Array/handle, ownership,
        copy-return, and nullable notes are appended in the established order
        without changing the owning plan records.
        """
        if isinstance(output, ArgumentTransferPlan):
            name = output.binding.python_name
            nullable = output.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}
        else:
            name = self._result_name(output, arguments)
            nullable = output.nullable
        lines = [f"{name} : {self._type(output, nullable=nullable, signature=False)}"]
        lines.extend(self._array_lines(output.array))
        if output.native_array_handle is not None:
            handle = output.native_array_handle
            lines.append(f"    Descriptor ownership: {handle.descriptor_ownership.value}.")
            state = "Unallocated" if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "Unassociated"
            lines.append(f"    {state} state remains inside the returned handle.")
        if isinstance(output, ArgumentTransferPlan):
            lines.extend(self._ownership_lines(output.ownership_owner))
            if output.transfer_mode is TransferMode.COPY_RETURN:
                lines.append("    Detached replacement; the original Python value is unchanged.")
        elif output.datatype_family is DatatypeFamily.DERIVED or output.array is not None:
            lines.extend(self._ownership_lines(output.ownership_owner))
        if nullable and output.native_array_handle is None:
            lines.append("    May be None.")
        return tuple(lines)

    @staticmethod
    def _optional_lines(argument: ArgumentTransferPlan) -> tuple[str, ...]:
        """Describe a transfer's completed optional or nullable input contract.

        Descriptor modes distinguish absent native dummies from present empty
        descriptors.  Other optional modes use the public omission wording;
        required nullable values retain their distinct ``None`` wording.
        """
        mode = argument.binding.optional_mode
        if mode is OptionalMode.DESCRIPTOR:
            return (
                "    Omit to make the native optional dummy absent.",
                "    Pass None for a present unallocated or unassociated descriptor.",
            )
        if mode is OptionalMode.REQUIRED_DESCRIPTOR:
            return ("    Pass None for an unallocated or unassociated required descriptor.",)
        if mode is not OptionalMode.REQUIRED:
            return ("    May be omitted or passed as None.",)
        if argument.binding.nullable:
            return ("    May be passed as None.",)
        return ()

    @staticmethod
    def _mutation_lines(argument: ArgumentTransferPlan) -> tuple[str, ...]:
        """Describe completed native mutation and copy-return projection behavior.

        Non-mutating arguments produce no note.  Copy returns, projected
        updates, and in-place storage each retain their established wording;
        the helper does not infer mutability from datatype or intent.
        """
        if not argument.mutates_native:
            return ()
        if argument.transfer_mode is TransferMode.COPY_RETURN:
            return (
                "    Native code writes to a private copy.",
                "    The original Python value is unchanged; the replacement is returned.",
            )
        if argument.projects_result:
            return ("    Native code may update this value; the updated value is returned.",)
        return ("    Native code may update the supplied storage in place.",)

    def _raise_lines(
        self,
        arguments: tuple[ArgumentTransferPlan, ...],
        outputs: tuple[ArgumentTransferPlan | ResultPlan, ...],
        status_error: BindingStatusErrorPlan | None,
    ) -> tuple[str, ...]:
        """Collect public exceptions implied by completed callable transfers.

        Type errors are always documented; arrays, derived objects, and status
        envelopes contribute their respective contract errors.  Duplicate
        exception names are grouped by the shared formatter in insertion order.
        """
        exceptions = [("TypeError", "If an argument has an incompatible Python type or dtype.")]
        if any(item.array is not None or item.native_array_handle is not None for item in (*arguments, *outputs)):
            exceptions.append(("ValueError", "If rank, shape, layout, or descriptor state violates the contract."))
        if any(item.datatype_family is DatatypeFamily.DERIVED for item in arguments):
            exceptions.append(("RuntimeError", "If a derived-object transaction cannot be acquired or restored."))
        if status_error is not None:
            exceptions.append(
                (
                    status_error.exception_kind.value,
                    f"If native status differs from the success value {status_error.success}.",
                )
            )
        return self._merged_exception_lines(exceptions)

    @staticmethod
    def _merged_exception_lines(exceptions: list[tuple[str, str]]) -> tuple[str, ...]:
        """Group exception descriptions by type while preserving first-seen order.

        ``exceptions`` is an ordered list of public error descriptions.  The
        returned alternating heading/detail lines merge repeated exception
        names without sorting or mutating the input collection.
        """
        grouped: dict[str, list[str]] = {}
        for exception, description in exceptions:
            grouped.setdefault(exception, []).append(description)
        return tuple(
            line
            for exception, descriptions in grouped.items()
            for line in (exception, *(f"    {item}" for item in descriptions))
        )

    # Type, array, ownership, and constructor-formatting helpers.
    def _type(self, transfer, *, nullable: bool, signature: bool) -> str:
        """Render one completed transfer's public type, optionally with ``None``.

        ``signature`` selects annotation versus prose spelling for nullability.
        The base type is delegated to the completed family/handle/array facts;
        this helper performs presentation only.
        """
        type_name = self._base_type(transfer)
        if not nullable:
            return type_name
        return f"{type_name} | None" if signature else f"{type_name} or None"

    def _base_type(self, transfer) -> str:
        """Map one completed transfer family and storage facet to public type text.

        Callback and derived types keep their named plan identities.  Scalar,
        descriptor-handle, and ordinary-array cases use the shared scalar map
        and stored facets, never a native declaration or backend spelling.
        """
        if getattr(transfer, "datatype_family", None) is DatatypeFamily.CALLBACK:
            return self._callback_type(transfer.callback)
        if getattr(transfer, "datatype_family", None) is DatatypeFamily.DERIVED:
            return transfer.semantic_type_name
        scalar = _SCALAR_TYPES.get(transfer.semantic_type_name, transfer.semantic_type_name)
        handle = getattr(transfer, "native_array_handle", None)
        if handle is not None:
            prefix = (
                "AllocatableArray"
                if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
                else "PointerArray"
            )
            return f"{prefix}[{scalar}]"
        if getattr(transfer, "array", None) is not None:
            element = "bytes" if transfer.semantic_type_name == "String" else scalar
            return f"ndarray[{element}]"
        return scalar

    def _callback_type(self, callback: CallbackHandoffPlan | None) -> str:
        """Return the named completed prototype for one callback transfer.

        Callback documentation requires the handoff plan attached during
        policy completion.  A missing handoff is an inconsistent caller input
        and raises ``ValueError`` rather than inventing a callable signature.
        """
        if callback is None:
            raise ValueError("Callback documentation requires a completed handoff plan")
        return callback.prototype.name

    @staticmethod
    def _callback_transfer_type(transfer: CallbackTransferPlan) -> str:
        """Render a callback prototype argument or result from completed ABI facts.

        Derived transfers preserve their type identity.  Arrays and reference
        ABI transfers render as NumPy arrays; other transfers use the scalar
        map.  The helper is pure and does not inspect outer wrapper policy.
        """
        if transfer.derived_type_identity is not None:
            return transfer.semantic_type_name
        scalar = _SCALAR_TYPES.get(transfer.semantic_type_name, transfer.semantic_type_name)
        if transfer.array is not None or transfer.abi.value == "reference":
            return f"ndarray[{scalar}]"
        return scalar

    @staticmethod
    def _array_lines(array: ArrayHandoffPlan | None) -> tuple[str, ...]:
        """Render rank, resolved display shape, and layout notes for one array facet.

        ``None`` produces no lines.  Unknown extents are intentionally omitted
        from shape text while rank and supported layout facts remain visible;
        the supplied plan is not normalized or validated here.
        """
        if array is None:
            return ()
        lines = [WrapperDocstringBuilder._array_rank_line(array)]
        display_shape = array.display_shape or array.shape
        if display_shape and all(str(extent) not in _UNKNOWN_EXTENTS for extent in display_shape):
            lines.append(f"    Shape: ({', '.join(map(str, display_shape))})")
        if (array.rank is None or array.rank > 1) and array.order in {"ORDER_C", "ORDER_F"}:
            layout = "C-contiguous" if array.order == "ORDER_C" else "F-contiguous"
            lines.append(f"    Layout: {layout}")
        return tuple(lines)

    @staticmethod
    def _array_rank_line(array: ArrayHandoffPlan) -> str:
        """Render the rank sentence for ordinary or flattened Python storage.

        Flattened storage preserves the special native-rank and flat-axis
        wording.  Assumed rank and concrete rank use their distinct stable
        forms, with no inspection of native declaration expressions.
        """
        if array.flatten_python_storage:
            native_rank = 1 if array.rank is None else array.rank
            if native_rank == 1:
                return "    Rank: 1..15, flattened to native rank 1"
            edge = "leading" if array.flat_axis == 0 else "final"
            return f"    Rank: {native_rank}..15, flattened at {edge} Flat axis to native rank {native_rank}"
        if array.rank is None:
            return "    Rank: 1..15"
        return f"    Rank: {array.rank}"

    @staticmethod
    def _ownership_lines(owner: OwnershipOwner) -> tuple[str, ...]:
        """Render the public ownership label for one completed owner enum.

        Every supported ``OwnershipOwner`` maps to one stable prose label.  An
        unsupported value raises the normal mapping error rather than silently
        choosing a different ownership description.
        """
        label = {
            OwnershipOwner.CALLER: "Caller-owned",
            OwnershipOwner.NATIVE: "Native-owned",
            OwnershipOwner.PYTHON: "Python-owned",
            OwnershipOwner.WRAPPER: "Wrapper-owned",
            OwnershipOwner.TEMPORARY: "Temporary",
            OwnershipOwner.UNKNOWN: "Unknown",
        }[owner]
        return (f"    Ownership: {label}.",)

    @staticmethod
    def _result_name(result: ResultPlan, arguments: tuple[ArgumentTransferPlan, ...]) -> str:
        """Choose the stable public name for one declared result record.

        A matching projected argument wins, then a native-slot Python name,
        then the positional ``result`` fallback.  The lookup only presents the
        already-planned public projection and does not modify result ordering.
        """
        projected = next(
            (
                argument.binding.python_name
                for argument in arguments
                if argument.projects_result and argument.result_position == result.result_position
            ),
            None,
        )
        if projected is not None:
            return projected
        if result.native_call_slot is not None and result.native_call_slot.python_name:
            return result.native_call_slot.python_name
        return "result" if result.result_position == 0 else f"result_{result.result_position}"

    def _module_variable_summary_lines(self, variable: ModuleVariablePlan) -> tuple[str, ...]:
        """Expand one module-variable docstring for every exported Python alias.

        The first line supplies the rendered type while the remaining details
        are reused verbatim for each alias, preserving attribute documentation
        without rebuilding getter/setter policy.  A nonstandard first line is
        returned unchanged as one summary line.
        """
        if variable.docstring is None:
            raise ValueError(f"Module variable {variable.owner_path!r} has no rendered documentation")
        first, *details = variable.docstring.splitlines()
        _name, separator, type_name = first.partition(" : ")
        if not separator:
            return (first,)
        return tuple(line for name in variable.binding.python_names for line in (f"{name} : {type_name}", *details))

    def _keyword_field_signature(
        self,
        python_name: str,
        constructor: ConstructorPlan,
        fields: tuple[DerivedFieldPlan, ...],
    ) -> str:
        """Render a keyword-only default-field constructor signature.

        Field order follows the supplied completed field tuple, and each
        constructor default uses the matching prepared field metadata.  With no
        fields the helper returns the stable empty constructor form.
        """
        defaults = {field.name: field.default_value for field in constructor.fields}
        parameters = ", ".join(
            f"{field.name}={defaults[field.name] if defaults[field.name] is not None else '...'}" for field in fields
        )
        return f"{python_name}(*, {parameters}) -> {python_name}" if parameters else f"{python_name}() -> {python_name}"

    def _constructor_field_lines(self, field: DerivedFieldPlan) -> tuple[str, ...]:
        """Render one editable constructor field as a public parameter line.

        The field's already completed type is rendered without nullability
        decoration, matching the default-field constructor contract.  No
        setter or ownership wording is added in this compact parameter view.
        """
        return (f"{field.name} : {self._type(field, nullable=False, signature=False)}",)


if __name__ == "__main__":
    from prik.planning.planner import WrapperPlanner
    from prik.semantics.models import SemanticArgument, SemanticFunction, SemanticModule, SemanticType
    from prik.policy.completion import complete_semantic_policies

    module = SemanticModule(
        name="docstring_demo",
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
    plan = WrapperPlanner().build(module)
    WrapperDocstringBuilder().render(plan)
    docstring = plan.namespaces[0].functions[0].binding.docstring

    print(docstring)
