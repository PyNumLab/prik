"""Python-facing documentation rendered from completed wrapper-plan records."""

from __future__ import annotations

from prik.semantics.ownership import OwnershipOwner, SetterAction, TransferMode
from prik.semantics.wrapper_policy import (
    ClassConstructorKind,
    ModuleGetterAction,
    NativeArrayDescriptorKind,
    OptionalMode,
)
from prik.wrapper_codegen.plan import (
    ArgumentTransferPlan,
    ArrayHandoffPlan,
    BindingStatusErrorPlan,
    CallbackHandoffPlan,
    CallbackTransferPlan,
    ClassMethodPlan,
    ConstructorPlan,
    DatatypeFamily,
    DerivedFieldPlan,
    FunctionPlan,
    ModuleVariablePlan,
    OverloadPlan,
    ResultPlan,
)


_SCALAR_TYPES = {
    "Bool": "bool",
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
    """Build compact NumPy-style documentation without backend inference."""

    # Namespace and class summaries.
    def namespace(
        self,
        module_name: str,
        path: tuple[str, ...],
        functions: tuple[FunctionPlan, ...],
        variables: tuple[ModuleVariablePlan, ...],
        classes,
        overloads: tuple[OverloadPlan, ...],
    ) -> str:
        """Index every public owner in one generated Python namespace."""
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
        """Summarize one opaque class and its complete public descriptors."""
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

    # Callback documentation.
    def function(
        self,
        python_name: str,
        arguments: tuple[ArgumentTransferPlan, ...],
        results: tuple[ResultPlan, ...],
        *,
        status_error: BindingStatusErrorPlan | None = None,
        excluded_native_position: int | None = None,
    ) -> str:
        """Describe one Python callable from its completed transfers."""
        visible = self._visible_arguments(arguments, excluded_native_position)
        outputs = self._documented_outputs(arguments, results)
        lines = [self._callable_signature(python_name, visible, outputs)]
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
        """Describe one public method while omitting its passed-object slot."""
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
        """List accepted public signatures without exposing private candidates."""
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
        """Describe the selected construction route for one generated class."""
        if constructor.kind is ClassConstructorKind.ABSENT:
            return self._absent_constructor(python_name, constructor)
        handlers = {
            ClassConstructorKind.DEFAULT_FIELDS: self._default_constructor,
            ClassConstructorKind.BOUND_PROCEDURE: self._bound_constructor,
            ClassConstructorKind.OVERLOAD_SET: self._overloaded_constructor,
        }
        handler = handlers.get(constructor.kind)
        if handler is None:  # pragma: no cover - policy validation owns the enum envelope
            raise ValueError(f"Unsupported constructor kind: {constructor.kind.value}")
        lines = handler(python_name, constructor, fields)
        self._append_section(lines, "Returns", (python_name, "    New wrapper-owned native instance."))
        self._append_section(
            lines,
            "Raises",
            ("TypeError", "    If the supplied arguments do not satisfy the constructor contract."),
        )
        return "\n".join(lines)

    @staticmethod
    def _absent_constructor(python_name: str, constructor: ConstructorPlan) -> str:
        """Describe an explicitly nonconstructible wrapper class."""
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
        """Document the keyword-only editable-field constructor."""
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
        """Document a constructor backed by one completed native call."""
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
        """Document exact signatures accepted by an overloaded constructor."""
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

    # Attribute documentation.
    def module_variable(self, variable: ModuleVariablePlan) -> str:
        """Describe a module attribute where CPython cannot attach a descriptor docstring."""
        name = variable.binding.python_names[0]
        nullable = variable.binding.getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
        lines = [f"{name} : {self._type(variable, nullable=nullable, signature=False)}"]
        lines.extend(self._array_lines(variable.array))
        if variable.binding.getter_action is ModuleGetterAction.CONSTANT_VALUE:
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
        """Describe one property and its native lifetime or assignment behavior."""
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

    # Shared signature and section helpers.
    @staticmethod
    def _append_section(lines: list[str], heading: str, body: tuple[str, ...]) -> None:
        """Append one nonempty NumPy-style section."""
        if not body:
            return
        lines.extend(("", heading, "-" * len(heading), *body))

    @staticmethod
    def _first_line(docstring: str) -> str:
        """Return the stable summary line of a rendered docstring."""
        return docstring.splitlines()[0] if docstring else ""

    def _callable_signature(
        self,
        name: str,
        arguments: tuple[ArgumentTransferPlan, ...],
        outputs: tuple[ArgumentTransferPlan | ResultPlan, ...],
    ) -> str:
        return self._signature(name, arguments, self._result_summary(outputs))

    def _signature(
        self,
        name: str,
        arguments: tuple[ArgumentTransferPlan, ...],
        result_type: str,
    ) -> str:
        parameters = ", ".join(self._signature_parameter(argument) for argument in arguments)
        return f"{name}({parameters}) -> {result_type}"

    @staticmethod
    def _signature_parameter(argument: ArgumentTransferPlan) -> str:
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
        passed = candidate.class_call.passed_object_position if passed_object and candidate.class_call else None
        arguments = self._visible_arguments(candidate.arguments, passed)
        outputs = self._documented_outputs(candidate.arguments, candidate.results)
        parameters = ", ".join(self._typed_signature_parameter(argument) for argument in arguments)
        return f"{name}({parameters}) -> {result_type or self._result_summary(outputs)}"

    @staticmethod
    def _overload_candidates(overload: OverloadPlan):
        """Pair candidates with their completed passed-object flags."""
        return zip(overload.candidates, overload.candidate_passed_objects, strict=True)

    @staticmethod
    def _argument_at_native_position(
        arguments: tuple[ArgumentTransferPlan, ...],
        native_position: int,
    ) -> ArgumentTransferPlan:
        """Return the validated receiver selected by class-call policy."""
        return next(argument for argument in arguments if argument.native_position == native_position)

    def _candidate_mutates_receiver(self, candidate: FunctionPlan, passed_object: bool) -> bool:
        """Report receiver mutation for one completed overload candidate."""
        if not passed_object or candidate.class_call is None:
            return False
        receiver = self._argument_at_native_position(candidate.arguments, candidate.class_call.passed_object_position)
        return receiver.mutates_native

    def _overload_notes(self, overload: OverloadPlan) -> tuple[str, ...]:
        """Describe only receiver behavior shared by class-owned candidates."""
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
        """Render enough public type information to distinguish overloads."""
        parameter = f"{argument.binding.python_name}: {self._type(argument, nullable=argument.binding.nullable, signature=True)}"
        if argument.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}:
            return f"{parameter} = ..."
        return parameter

    @staticmethod
    def _visible_arguments(
        arguments: tuple[ArgumentTransferPlan, ...],
        excluded_native_position: int | None,
    ) -> tuple[ArgumentTransferPlan, ...]:
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
        by_position = {
            argument.result_position: argument
            for argument in arguments
            if argument.projects_result and argument.result_position is not None
        }
        by_position.update((result.result_position, result) for result in results)
        return tuple(by_position[position] for position in sorted(by_position))

    def _result_summary(self, outputs: tuple[ArgumentTransferPlan | ResultPlan, ...]) -> str:
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

    # Parameter and result details.
    def _argument_lines(self, argument: ArgumentTransferPlan) -> tuple[str, ...]:
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
        """Group descriptions under one heading per public exception type."""
        grouped: dict[str, list[str]] = {}
        for exception, description in exceptions:
            grouped.setdefault(exception, []).append(description)
        return tuple(
            line
            for exception, descriptions in grouped.items()
            for line in (exception, *(f"    {item}" for item in descriptions))
        )

    # Type, array, ownership, and constructor helpers.
    def _type(self, transfer, *, nullable: bool, signature: bool) -> str:
        type_name = self._base_type(transfer)
        if not nullable:
            return type_name
        return f"{type_name} | None" if signature else f"{type_name} or None"

    def _base_type(self, transfer) -> str:
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
        if callback is None:
            raise ValueError("Callback documentation requires a completed handoff plan")
        return callback.prototype_name

    @staticmethod
    def _callback_transfer_type(transfer: CallbackTransferPlan) -> str:
        if transfer.derived_type_identity is not None:
            return transfer.semantic_type_name
        scalar = _SCALAR_TYPES.get(transfer.semantic_type_name, transfer.semantic_type_name)
        if transfer.array is not None or transfer.abi.value == "reference":
            return f"ndarray[{scalar}]"
        return scalar

    @staticmethod
    def _array_lines(array: ArrayHandoffPlan | None) -> tuple[str, ...]:
        if array is None:
            return ()
        lines = [WrapperDocstringBuilder._array_rank_line(array)]
        if array.shape and all(str(extent) not in _UNKNOWN_EXTENTS for extent in array.shape):
            lines.append(f"    Shape: ({', '.join(map(str, array.shape))})")
        if (array.rank is None or array.rank > 1) and array.order in {"ORDER_C", "ORDER_F"}:
            layout = "C-contiguous" if array.order == "ORDER_C" else "F-contiguous"
            lines.append(f"    Layout: {layout}")
        return tuple(lines)

    @staticmethod
    def _array_rank_line(array: ArrayHandoffPlan) -> str:
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
        defaults = {field.name: field.default_value for field in constructor.fields}
        parameters = ", ".join(
            f"{field.name}={defaults[field.name] if defaults[field.name] is not None else '...'}" for field in fields
        )
        return f"{python_name}(*, {parameters}) -> {python_name}" if parameters else f"{python_name}() -> {python_name}"

    def _constructor_field_lines(self, field: DerivedFieldPlan) -> tuple[str, ...]:
        return (f"{field.name} : {self._type(field, nullable=False, signature=False)}",)
