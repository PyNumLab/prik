"""Emit the executable Python facade embedded in a generated C extension."""

from __future__ import annotations

from dataclasses import dataclass

from prik.codegen.c.naming import CBindingNames
from prik.planning.models import (
    ArgumentTransferPlan,
    ClassMethodPlan,
    ClassSurfacePlan,
    DerivedFieldPlan,
    DerivedMemberPathPlan,
    DerivedTypePlan,
    FunctionPlan,
    ModuleVariablePlan,
    NamespacePlan,
    OverloadPlan,
)
from prik.codegen.visitor import ClassVisitor
from prik.policy.ownership import SetterAction
from prik.policy.models import (
    ClassConstructorKind,
    ClassMethodKind,
    ModuleObjectAccessMechanism,
    OptionalMode,
)


@dataclass(frozen=True)
class PythonSurfaceContext:
    """Store namespace facts already selected by planning and C orchestration."""

    allocatable_holder_identities: frozenset[tuple[str, str]]
    pointer_holder_identities: frozenset[tuple[str, str]]
    nullable_module_proxy_owner_paths: frozenset[str]


class PythonSurfaceEmitter(ClassVisitor):
    """Render derived classes and their thin overload forwarders as Python source."""

    def __init__(self, context: PythonSurfaceContext) -> None:
        self._context = context

    def emit(self, namespace: NamespacePlan) -> str:
        """Return overloads, opaque classes, and typed member operation maps."""
        return self.visit(namespace)

    def _visit_NamespacePlan(self, namespace: NamespacePlan) -> str:
        """Render one planned namespace as executable Python source."""
        surfaces = self._class_surfaces(namespace)
        class_names = self._class_names(namespace)
        ops_names = self._direct_ops_names(namespace)
        sections = [
            "_prik_unset = object()",
            *(
                self._derived_type_python_source(
                    derived,
                    surfaces.get(derived.type_identity),
                    class_names,
                    ops_names,
                )
                for derived in namespace.derived_types
            ),
        ]
        sections.extend(self._holder_ops_python_sources(namespace))
        sections.extend(self._module_proxy_ops_python_sources(namespace))
        return "\n\n".join(section for section in sections if section)

    @staticmethod
    def _class_surfaces(namespace: NamespacePlan) -> dict[tuple[str, str], ClassSurfacePlan]:
        """Index planned class surfaces by completed type identity."""
        return {surface.type_identity: surface for surface in namespace.classes}

    @staticmethod
    def _class_names(namespace: NamespacePlan) -> dict[tuple[str, str], str]:
        """Index visible class names needed for inheritance rendering."""
        return {surface.type_identity: surface.python_names[0] for surface in namespace.classes if surface.python_names}

    def _direct_ops_names(self, namespace: NamespacePlan) -> dict[tuple[str, str], str]:
        """Index operation dictionaries inherited by generated subclasses."""
        return {derived.type_identity: self._direct_type_ops_name(derived) for derived in namespace.derived_types}

    def _holder_ops_python_sources(self, namespace: NamespacePlan) -> tuple[str, ...]:
        """Render allocatable and pointer holder operation maps by completed identity."""
        return (
            *(
                self._allocatable_holder_ops_python_source(derived)
                for derived in namespace.derived_types
                if derived.type_identity in self._context.allocatable_holder_identities
            ),
            *(
                self._pointer_holder_ops_python_source(derived)
                for derived in namespace.derived_types
                if derived.type_identity in self._context.pointer_holder_identities
            ),
        )

    def _module_proxy_ops_python_sources(self, namespace: NamespacePlan) -> tuple[str, ...]:
        """Render persistent module-derived operation maps in declaration order."""
        return tuple(
            self._module_proxy_ops_python_source(variable)
            for variable in namespace.variables
            if variable.derived is not None
        )

    def _derived_type_python_source(
        self,
        derived: DerivedTypePlan,
        surface: ClassSurfacePlan | None,
        class_names: dict[tuple[str, str], str],
        ops_names: dict[tuple[str, str], str],
    ) -> str:
        """Return one opaque wrapper assembled from its completed class surface."""
        name = derived.python_names[0]
        ops_name = self._direct_type_ops_name(derived)
        base = self._class_base_name(surface, class_names)
        base_ops = self._class_base_ops_name(surface, ops_names)
        slots = self._class_slots(base)
        own_ops = self._direct_type_ops_literal(derived)
        combined_ops = self._combined_ops_literal(base_ops, own_ops)
        lines = [
            f"{ops_name} = {combined_ops}",
            f"class {name}{f'({base})' if base else ''}:",
            self._class_docstring_line(surface, name),
            f"    __slots__ = {slots}",
        ]
        lines.extend(self._class_constructor_python_lines(surface))
        lines.extend(self._derived_class_member_python_lines(derived, surface))
        lines.extend(self._class_wrap_helper_python_lines(surface, name, ops_name))
        return "\n".join(lines)

    @staticmethod
    def _class_base_ops_name(
        surface: ClassSurfacePlan | None,
        ops_names: dict[tuple[str, str], str],
    ) -> str | None:
        """Return the inherited operation-map name, when one is planned."""
        if surface is None or not surface.base_identities:
            return None
        return ops_names[surface.base_identities[0]]

    @staticmethod
    def _class_slots(base: str | None) -> str:
        """Store native wrapper state only on the root generated class."""
        return "()" if base else "('_prik_capsule', '_prik_owner', '_prik_ops', '_prik_origin')"

    @staticmethod
    def _combined_ops_literal(base_ops: str | None, own_ops: str) -> str:
        """Merge inherited and directly declared operation dictionaries."""
        return f"{{**{base_ops}, **{own_ops}}}" if base_ops is not None else own_ops

    @staticmethod
    def _class_docstring_line(surface: ClassSurfacePlan | None, name: str) -> str:
        """Return the class-body docstring line from its completed surface."""
        return f"    {surface.docstring!r}" if surface is not None else f"    {name!r}"

    def _derived_class_member_python_lines(
        self,
        derived: DerivedTypePlan,
        surface: ClassSurfacePlan | None,
    ) -> tuple[str, ...]:
        """Render fields, public methods, and overload descriptors for one class."""
        methods = () if surface is None else tuple(method for method in surface.methods if method.public)
        overloads = () if surface is None else surface.overloads
        return (
            *self._derived_property_python_source_lines(derived.fields),
            *self._class_method_python_source_lines(methods),
            *self._class_overload_python_source_lines(overloads),
        )

    def _derived_property_python_source_lines(self, fields: tuple[DerivedFieldPlan, ...]) -> tuple[str, ...]:
        """Flatten field descriptors while preserving declaration order."""
        return tuple(line for field in fields for line in self._derived_property_python_lines(field))

    def _class_method_python_source_lines(self, methods: tuple[ClassMethodPlan, ...]) -> tuple[str, ...]:
        """Flatten public method descriptors while preserving plan order."""
        return tuple(line for method in methods for line in self._class_method_python_lines(method))

    def _class_overload_python_source_lines(self, overloads: tuple[OverloadPlan, ...]) -> tuple[str, ...]:
        """Flatten overload descriptors while preserving plan order."""
        return tuple(line for overload in overloads for line in self._class_overload_python_lines(overload))

    def _class_wrap_helper_python_lines(
        self,
        surface: ClassSurfacePlan | None,
        name: str,
        ops_name: str,
    ) -> tuple[str, ...]:
        """Render the sole helper that attaches existing opaque native storage."""
        return (
            f"def {CBindingNames.class_wrap_helper(surface, fallback=name)}(capsule, owner=None, ops=None, origin='direct'):",
            f"    value = object.__new__({name})",
            "    value._prik_capsule = capsule",
            "    value._prik_owner = owner",
            f"    value._prik_ops = {ops_name} if ops is None else ops",
            "    value._prik_origin = origin",
            "    return value",
        )

    def _class_constructor_python_lines(self, surface: ClassSurfacePlan | None) -> tuple[str, ...]:
        """Render one constructor selected entirely by the class plan."""
        if surface is None or surface.constructor.kind is ClassConstructorKind.ABSENT:
            return self._absent_constructor_python_lines(surface)
        handlers = {
            ClassConstructorKind.DEFAULT_FIELDS: self._default_constructor_python_lines,
            ClassConstructorKind.BOUND_PROCEDURE: self._bound_constructor_python_lines,
            ClassConstructorKind.OVERLOAD_SET: self._overloaded_constructor_python_lines,
        }
        handler = handlers.get(surface.constructor.kind)
        if handler is None:
            raise ValueError(f"Unsupported completed constructor kind: {surface.constructor.kind.value}")
        return handler(surface)

    @staticmethod
    def _absent_constructor_python_lines(surface: ClassSurfacePlan | None) -> tuple[str, ...]:
        """Render one explicit rejection for a nonconstructible wrapper class."""
        message = (
            surface.constructor.rejection_message
            if surface is not None and surface.constructor.rejection_message
            else "native wrapper construction is disabled"
        )
        return (
            "    def __new__(cls, *args, **kwargs):",
            f"        {surface.constructor.docstring!r}" if surface is not None else "        'Construction disabled.'",
            f"        raise TypeError({message!r})",
        )

    def _default_constructor_python_lines(self, surface: ClassSurfacePlan) -> tuple[str, ...]:
        """Allocate one owner, then apply only explicitly supplied field values."""
        fields = surface.constructor.fields
        parameters = ", ".join(f"{field.name}=_prik_unset" for field in fields)
        signature = f", *, {parameters}" if parameters else ""
        lines = [
            "    def __new__(cls, *args, **kwargs):",
            f"        return {CBindingNames.class_create_method(surface)}()",
            f"    def __init__(self{signature}):",
            f"        {surface.constructor.docstring!r}",
        ]
        if not fields:
            lines.append("        pass")
        for field in fields:
            lines.extend(
                (
                    f"        if {field.name} is not _prik_unset:",
                    f"            self.{field.name} = {field.name}",
                )
            )
        return tuple(lines)

    def _bound_constructor_python_lines(self, surface: ClassSurfacePlan) -> tuple[str, ...]:
        """Call one validated target after allocating the persistent owner."""
        target = surface.constructor.target
        if target is None:
            raise ValueError(f"Bound constructor {surface.owner_path!r} has no target function")
        parameters = self._callable_public_arguments(target)
        lines = [
            "    def __new__(cls, *args, **kwargs):",
            f"        return {CBindingNames.class_create_method(surface)}()",
            f"    def __init__(self{self._python_parameter_suffix(parameters)}):",
            f"        {surface.constructor.docstring!r}",
            "        _prik_arguments = {'self': self}",
        ]
        lines.extend(self._optional_keyword_collection_lines(parameters, indent="        "))
        lines.append(f"        {target.binding.python_name}(**_prik_arguments)")
        return tuple(lines)

    def _overloaded_constructor_python_lines(self, surface: ClassSurfacePlan) -> tuple[str, ...]:
        """Dispatch one completed constructor overload after owner allocation."""
        overload = surface.constructor.overload
        if overload is None:
            raise ValueError(f"Overloaded constructor {surface.owner_path!r} has no overload plan")
        return (
            "    def __new__(cls, *args, **kwargs):",
            f"        return {CBindingNames.class_create_method(surface)}()",
            *self._class_overload_python_lines(
                overload,
                constructor=True,
                docstring=surface.constructor.docstring,
            ),
        )

    def _class_method_python_lines(self, method: ClassMethodPlan) -> tuple[str, ...]:
        """Render a readable Python descriptor over one ordinary function plan."""
        arguments = self._ordered_method_arguments(method)
        passed = self._passed_method_argument(method, arguments)
        signature = self._class_method_signature(method, arguments, passed)
        call_names = self._class_method_call_names(arguments, passed)
        return (
            *self._class_method_decorators(method),
            f"    def {method.python_name}({signature}):",
            f"        {method.docstring!r}",
            f"        return {method.function.binding.python_name}({', '.join(call_names)})",
        )

    @staticmethod
    def _ordered_method_arguments(method: ClassMethodPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return class-call arguments in their completed Python order."""
        return tuple(sorted(method.function.arguments, key=lambda argument: argument.python_position))

    @staticmethod
    def _passed_method_argument(
        method: ClassMethodPlan,
        arguments: tuple[ArgumentTransferPlan, ...],
    ) -> ArgumentTransferPlan | None:
        """Return the argument occupied by the planned class receiver."""
        return next(
            (argument for argument in arguments if argument.native_position == method.passed_object_position),
            None,
        )

    @staticmethod
    def _class_method_signature(
        method: ClassMethodPlan,
        arguments: tuple[ArgumentTransferPlan, ...],
        passed: ArgumentTransferPlan | None,
    ) -> str:
        """Render one static or instance method signature."""
        public_names = tuple(argument.binding.python_name for argument in arguments if argument is not passed)
        names = public_names if method.kind is ClassMethodKind.STATIC else ("self", *public_names)
        return ", ".join(names)

    @staticmethod
    def _class_method_call_names(
        arguments: tuple[ArgumentTransferPlan, ...],
        passed: ArgumentTransferPlan | None,
    ) -> tuple[str, ...]:
        """Render candidate call arguments with the receiver restored."""
        return tuple("self" if argument is passed else argument.binding.python_name for argument in arguments)

    @staticmethod
    def _class_method_decorators(method: ClassMethodPlan) -> tuple[str, ...]:
        """Return the Python descriptor decorators for one planned method."""
        return ("    @staticmethod",) if method.kind is ClassMethodKind.STATIC else ()

    def _class_overload_python_lines(
        self,
        overload: OverloadPlan,
        *,
        constructor: bool = False,
        docstring: str | None = None,
    ) -> tuple[str, ...]:
        """Render one thin class descriptor over a namespace-installed C dispatcher."""
        passed_object = self._overload_has_receiver(overload, constructor)
        return (
            *self._overload_decorators(passed_object),
            f"    def {self._overload_method_name(overload, constructor)}({self._overload_signature(passed_object)}):",
            f"        {docstring or overload.docstring!r}",
            f"        return {CBindingNames.overload_dispatch_method(overload)}("
            f"{self._overload_receiver_prefix(passed_object)}*args, **kwargs)",
        )

    @staticmethod
    def _overload_has_receiver(overload: OverloadPlan, constructor: bool) -> bool:
        """Return the completed receiver convention for one class overload."""
        return constructor or overload.candidate_passed_objects[0]

    @staticmethod
    def _overload_decorators(passed_object: bool) -> tuple[str, ...]:
        """Render the static-method marker when no receiver is planned."""
        return () if passed_object else ("    @staticmethod",)

    @staticmethod
    def _overload_method_name(overload: OverloadPlan, constructor: bool) -> str:
        """Return the Python descriptor name for a method or constructor."""
        return "__init__" if constructor else overload.python_name

    @staticmethod
    def _overload_signature(passed_object: bool) -> str:
        """Return the variadic descriptor signature with its receiver convention."""
        return "self, *args, **kwargs" if passed_object else "*args, **kwargs"

    @staticmethod
    def _overload_receiver_prefix(passed_object: bool) -> str:
        """Return the receiver prefix forwarded to the private C dispatcher."""
        return "self, " if passed_object else ""

    @staticmethod
    def _callable_public_arguments(function: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return ordered user parameters, excluding the class passed object."""
        return tuple(
            argument
            for argument in sorted(function.arguments, key=lambda item: item.python_position)
            if argument.binding.python_name != "self"
        )

    @staticmethod
    def _python_parameter_suffix(arguments: tuple[ArgumentTransferPlan, ...]) -> str:
        """Return one rendered Python constructor parameter suffix."""
        if not arguments:
            return ""
        rendered = ", ".join(
            argument.binding.python_name
            + (
                "=_prik_unset"
                if argument.binding.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}
                else ""
            )
            for argument in arguments
        )
        return f", {rendered}"

    @staticmethod
    def _optional_keyword_collection_lines(
        arguments: tuple[ArgumentTransferPlan, ...],
        *,
        indent: str,
    ) -> tuple[str, ...]:
        """Build optional keyword collection lines from completed binding plans."""
        lines = []
        for argument in arguments:
            name = argument.binding.python_name
            if argument.binding.optional_mode in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}:
                lines.append(f"{indent}_prik_arguments['{name}'] = {name}")
            else:
                lines.extend(
                    (
                        f"{indent}if {name} is not _prik_unset:",
                        f"{indent}    _prik_arguments['{name}'] = {name}",
                    )
                )
        return tuple(lines)

    @staticmethod
    def _class_base_name(
        surface: ClassSurfacePlan | None,
        class_names: dict[tuple[str, str], str],
    ) -> str | None:
        """Return the planned Python base-class name."""
        if surface is None or not surface.base_identities:
            return None
        return class_names[surface.base_identities[0]]

    @staticmethod
    def _derived_property_python_lines(field: DerivedFieldPlan) -> tuple[str, ...]:
        """Build a property from completed getter and setter actions."""
        lines = [
            "    @property",
            f"    def {field.name}(self):",
            f"        {field.docstring!r}",
            "        present = self._prik_ops.get('_present')",
            "        if present is not None:",
            "            present(self)",
            f"        return self._prik_ops['{field.name}_get'](self)",
        ]
        if field.setter_action is SetterAction.WRITE_THROUGH:
            lines.extend(
                (
                    f"    @{field.name}.setter",
                    f"    def {field.name}(self, value):",
                    "        present = self._prik_ops.get('_present')",
                    "        if present is not None:",
                    "            present(self)",
                    f"        self._prik_ops['{field.name}_set'](self, value)",
                )
            )
        elif field.setter_action is SetterAction.REJECT_REPLACEMENT:
            lines.extend(
                (
                    f"    @{field.name}.setter",
                    f"    def {field.name}(self, value):",
                    f"        raise AttributeError('field {field.name} does not support replacement assignment')",
                )
            )
        return tuple(lines)

    def _direct_type_ops_literal(self, derived: DerivedTypePlan) -> str:
        """Return the operation dictionary for directly owned native storage."""
        entries = []
        for field in derived.fields:
            entries.append(f"'{field.name}_get': {CBindingNames.derived_field_method(derived, field, 'get')}")
            if field.setter_action is SetterAction.WRITE_THROUGH:
                entries.append(f"'{field.name}_set': {CBindingNames.derived_field_method(derived, field, 'set')}")
        return "{" + ", ".join(entries) + "}"

    def _allocatable_holder_ops_python_source(self, derived: DerivedTypePlan) -> str:
        """Build the operation dictionary for allocatable-holder storage."""
        entries = [f"'_present': {CBindingNames.allocatable_holder_presence_method(derived.backend_symbol)}"]
        for field in derived.fields:
            entries.append(
                f"'{field.name}_get': {CBindingNames.allocatable_holder_field_method(derived, field, 'get')}"
            )
            if field.setter_action is SetterAction.WRITE_THROUGH:
                entries.append(
                    f"'{field.name}_set': {CBindingNames.allocatable_holder_field_method(derived, field, 'set')}"
                )
        return f"{CBindingNames.allocatable_holder_ops(derived.backend_symbol)} = {{{', '.join(entries)}}}"

    def _pointer_holder_ops_python_source(self, derived: DerivedTypePlan) -> str:
        """Build the operation dictionary for pointer-holder storage."""
        entries = [f"'_present': {CBindingNames.pointer_holder_presence_method(derived.backend_symbol)}"]
        for field in derived.fields:
            entries.append(f"'{field.name}_get': {CBindingNames.pointer_holder_field_method(derived, field, 'get')}")
            if field.setter_action is SetterAction.WRITE_THROUGH:
                entries.append(
                    f"'{field.name}_set': {CBindingNames.pointer_holder_field_method(derived, field, 'set')}"
                )
        return f"{CBindingNames.pointer_holder_ops(derived.backend_symbol)} = {{{', '.join(entries)}}}"

    @staticmethod
    def _direct_type_ops_name(derived: DerivedTypePlan) -> str:
        """Return the Python operation-map name for direct storage."""
        return f"_prik_ops_{derived.type_name.casefold()}"

    def _module_proxy_ops_python_source(self, variable: ModuleVariablePlan) -> str:
        """Return one operation dictionary per reachable plain-module object path."""
        if variable.derived is None:
            return ""
        if variable.derived.access is ModuleObjectAccessMechanism.DIRECT_ADDRESS:
            direct = f"_prik_ops_{variable.derived.handoff.type_name.casefold()}"
            native_ops = CBindingNames.derived_origin_capsule_method(variable)
            return f"{CBindingNames.module_member_ops(variable, ())} = dict({direct}, _native_ops={native_ops}())"
        grouped: dict[tuple[str, ...], list[DerivedMemberPathPlan]] = {}
        for member in variable.derived.member_paths:
            grouped.setdefault(member.path[:-1], []).append(member)
        return "\n".join(
            f"{CBindingNames.module_member_ops(variable, prefix)} = "
            f"{self._module_proxy_ops_literal(variable, prefix, members)}"
            for prefix, members in grouped.items()
        )

    def _module_proxy_ops_literal(
        self,
        variable: ModuleVariablePlan,
        prefix: tuple[str, ...],
        members: list[DerivedMemberPathPlan],
    ) -> str:
        """Return one completed module-proxy operation dictionary."""
        entries = []
        if not prefix:
            entries.append(f"'_native_ops': {CBindingNames.derived_origin_capsule_method(variable)}()")
        if variable.owner_path in self._context.nullable_module_proxy_owner_paths:
            entries.append(f"'_present': {CBindingNames.module_derived_presence_method(variable)}")
        for member in members:
            field = member.field
            entries.append(f"'{field.name}_get': {CBindingNames.module_member_method(variable, member, 'get')}")
            if field.setter_action is SetterAction.WRITE_THROUGH:
                entries.append(f"'{field.name}_set': {CBindingNames.module_member_method(variable, member, 'set')}")
        return "{" + ", ".join(entries) + "}"
