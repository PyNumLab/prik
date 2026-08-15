"""Shared symbol spelling for the C binding and its Python surface."""

from __future__ import annotations

from prik.naming.native_symbols import NativeSymbolNames
from prik.planning.models import (
    ClassSurfacePlan,
    DerivedFieldPlan,
    DerivedMemberPathPlan,
    DerivedTypePlan,
    ModuleVariablePlan,
    OverloadPlan,
)


class CBindingNames:
    """Own symbols referenced by both generated C and embedded Python source."""

    @staticmethod
    def derived_origin_symbol(variable: ModuleVariablePlan) -> str:
        """Return the compact native-origin symbol for one module variable."""
        return NativeSymbolNames.compact(variable.owner_path, variable.symbol_name)

    @classmethod
    def derived_origin_capsule_method(cls, variable: ModuleVariablePlan) -> str:
        """Return the private Python callable exposing native-origin operations."""
        return f"_prik_origin_{cls.derived_origin_symbol(variable)}_native_ops"

    @staticmethod
    def derived_field_symbol(derived: DerivedTypePlan, field: DerivedFieldPlan) -> str:
        """Return the shared symbol fragment for one derived field."""
        return f"{derived.backend_symbol}_{field.name}".casefold()

    @classmethod
    def derived_field_method(cls, derived: DerivedTypePlan, field: DerivedFieldPlan, action: str) -> str:
        """Return the private Python callable for one direct field operation."""
        return f"_prik_field_{cls.derived_field_symbol(derived, field)}_{action}"

    @classmethod
    def allocatable_holder_field_method(
        cls,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        """Return the private callable for one allocatable-holder field operation."""
        return f"_prik_allocatable_holder_field_{cls.derived_field_symbol(derived, field)}_{action}"

    @classmethod
    def pointer_holder_field_method(
        cls,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        """Return the private callable for one pointer-holder field operation."""
        return f"_prik_pointer_holder_field_{cls.derived_field_symbol(derived, field)}_{action}"

    @staticmethod
    def allocatable_holder_presence_method(type_name: str) -> str:
        """Return the allocatable-holder presence guard exposed to Python."""
        return f"_prik_{type_name.casefold()}_allocatable_holder_require_present"

    @staticmethod
    def pointer_holder_presence_method(type_name: str) -> str:
        """Return the pointer-holder presence guard exposed to Python."""
        return f"_prik_{type_name.casefold()}_pointer_holder_require_present"

    @staticmethod
    def allocatable_holder_ops(type_name: str) -> str:
        """Return the Python operation-map name for an allocatable holder."""
        return f"_prik_ops_{type_name.casefold()}_allocatable_holder"

    @staticmethod
    def pointer_holder_ops(type_name: str) -> str:
        """Return the Python operation-map name for a pointer holder."""
        return f"_prik_ops_{type_name.casefold()}_pointer_holder"

    @staticmethod
    def module_member_symbol(variable: ModuleVariablePlan, member: DerivedMemberPathPlan) -> str:
        """Return the shared symbol fragment for one module-derived member."""
        return "_".join((variable.symbol_name, *member.path)).casefold()

    @classmethod
    def module_member_method(
        cls,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        action: str,
    ) -> str:
        """Return the private Python callable for one module-member operation."""
        return f"_prik_module_field_{cls.module_member_symbol(variable, member)}_{action}"

    @staticmethod
    def module_member_ops(variable: ModuleVariablePlan, prefix: tuple[str, ...]) -> str:
        """Return the operation-map name for one reachable module-object path."""
        suffix = "_".join((variable.symbol_name, *prefix)).casefold()
        return f"_prik_ops_{suffix}"

    @staticmethod
    def module_derived_presence_method(variable: ModuleVariablePlan) -> str:
        """Return the presence guard for a nullable module-derived object."""
        return f"_prik_module_{variable.symbol_name.casefold()}_require_present"

    @staticmethod
    def class_create_method(surface: ClassSurfacePlan) -> str:
        """Return the private C constructor callable installed in the namespace."""
        return f"_prik_create_{surface.type_identity[1].casefold()}"

    @staticmethod
    def class_wrap_helper(
        surface: ClassSurfacePlan | None,
        *,
        fallback: str | None = None,
    ) -> str:
        """Return the Python helper attaching existing native storage."""
        name = surface.python_names[0] if surface is not None else fallback
        if name is None:
            raise ValueError("Class wrapper helper requires a Python type name")
        return f"_prik_wrap_{name}"

    @staticmethod
    def overload_dispatch_symbol(overload: OverloadPlan) -> str:
        """Return one compact symbol unique to the planned overload surface."""
        return NativeSymbolNames.compact(overload.owner_path, overload.python_name, limit=38)

    @classmethod
    def overload_dispatch_method(cls, overload: OverloadPlan) -> str:
        """Return the private namespace callable used by class forwarding methods."""
        return f"_prik_dispatch_{cls.overload_dispatch_symbol(overload)}"

    @classmethod
    def overload_dispatch_function(cls, overload: OverloadPlan) -> str:
        """Return the generated C function implementing overload selection."""
        return f"wrap_{cls.overload_dispatch_method(overload)}"
