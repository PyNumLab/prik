"""Backend syntax nodes for direct wrapper-plan source generation."""

from __future__ import annotations

from dataclasses import dataclass

from prik.utilities.stage_values import StageRecord


@dataclass
class BackendScalarType(StageRecord):
    """Scalar type spelling consumed by C and Fortran printers."""

    semantic_name: str
    c_spelling: str
    fortran_spelling: str
    python_parse_unit: str | None = None
    numpy_type_macro: str | None = None
    python_result_kind: str | None = None
    python_type_name: str | None = None
    python_module_result_kind: str | None = None
    cfi_type_spelling: str | None = None


@dataclass
class CodeExpression(StageRecord):
    """Raw expression text owned by a backend emitter or focused test."""

    text: str


@dataclass
class CInclude(StageRecord):
    """C include directive."""

    header: str
    system: bool = True


@dataclass
class CMacroDefinition(StageRecord):
    """C preprocessor macro definition."""

    name: str
    value: str | None = None


@dataclass
class CComment(StageRecord):
    """One generated C line comment."""

    text: str


@dataclass
class CParameter(StageRecord):
    """C function parameter."""

    name: str
    type_name: str
    function_parameters: tuple[str, ...] | None = None


@dataclass
class CFunctionPrototype(StageRecord):
    """C function prototype for generated headers."""

    name: str
    return_type: str
    parameters: tuple[CParameter, ...] = ()
    storage: str | None = None


@dataclass
class CFunctionPointerType(StageRecord):
    """Named C function-pointer type used by typed runtime operation tables."""

    name: str
    return_type: str
    parameter_types: tuple[str, ...] = ()


@dataclass
class CStructDefinition(StageRecord):
    """Named C struct with ordinary or function-pointer fields."""

    name: str
    fields: tuple[CParameter, ...] = ()


@dataclass
class CMethodDefEntry(StageRecord):
    """One CPython method table entry."""

    python_name: str
    wrapper_name: str
    flags: str
    docstring: str = ""


@dataclass
class CMethodDefTable(StageRecord):
    """Generated CPython method table declaration."""

    name: str
    entries: tuple[CMethodDefEntry, ...] = ()


@dataclass
class CModuleDef(StageRecord):
    """Generated CPython module definition declaration."""

    name: str
    module_name: str
    docstring: str
    methods_name: str
    state_size: int = 0


@dataclass
class CModulePropertyEntry(StageRecord):
    """One dynamic module attribute routed through generated helpers."""

    python_name: str
    getter_name: str
    setter_name: str | None = None
    reject_replacement: bool = False


@dataclass
class CModulePropertySupport(StageRecord):
    """Heap module-type support for dynamic get/set attribute routing."""

    name: str
    module_name: str
    entries: tuple[CModulePropertyEntry, ...] = ()


@dataclass
class CDeclaration(StageRecord):
    """C local or global declaration."""

    name: str
    type_name: str
    initializer: CodeExpression | None = None


@dataclass
class CExpressionStatement(StageRecord):
    """C expression statement."""

    expression: CodeExpression


@dataclass
class CAllowThreadsBegin(StageRecord):
    """Release the CPython GIL immediately before one native call."""


@dataclass
class CAllowThreadsEnd(StageRecord):
    """Reacquire the CPython GIL immediately after one native call."""


@dataclass
class CIf(StageRecord):
    """C conditional with recursively printable statement bodies."""

    condition: CodeExpression
    body: tuple[CDeclaration | CExpressionStatement | CIf | CFor | CReturn, ...] = ()
    else_body: tuple[CDeclaration | CExpressionStatement | CIf | CFor | CReturn, ...] = ()


@dataclass
class CFor(StageRecord):
    """C for-loop used by compact table-driven runtime dispatch."""

    initializer: str
    condition: CodeExpression
    increment: CodeExpression
    body: tuple[CDeclaration | CExpressionStatement | CIf | CFor | CBreak | CReturn, ...] = ()


@dataclass
class CBreak(StageRecord):
    """C break statement."""


@dataclass
class CCase(StageRecord):
    """One value or default branch in a generated C switch."""

    value: CodeExpression | None
    body: tuple[CDeclaration | CExpressionStatement | CIf | CFor | CBreak | CReturn, ...] = ()


@dataclass
class CSwitch(StageRecord):
    """C switch statement used for planned integer dispatch keys."""

    expression: CodeExpression
    cases: tuple[CCase, ...] = ()


@dataclass
class CReturn(StageRecord):
    """C return statement."""

    expression: CodeExpression | None = None


@dataclass
class CFunction(StageRecord):
    """C function definition."""

    name: str
    return_type: str
    parameters: tuple[CParameter, ...] = ()
    body: tuple[
        CDeclaration
        | CExpressionStatement
        | CAllowThreadsBegin
        | CAllowThreadsEnd
        | CIf
        | CFor
        | CBreak
        | CSwitch
        | CReturn,
        ...,
    ] = ()
    storage: str | None = None


@dataclass
class CHeader(StageRecord):
    """Generated C header module."""

    guard: str
    includes: tuple[CInclude, ...] = ()
    prototypes: tuple[CFunctionPrototype, ...] = ()


@dataclass
class CModule(StageRecord):
    """Generated C source module."""

    name: str
    defines: tuple[CMacroDefinition, ...] = ()
    includes: tuple[CInclude, ...] = ()
    declarations: tuple[
        CComment
        | CDeclaration
        | CFunctionPointerType
        | CFunctionPrototype
        | CStructDefinition
        | CMethodDefTable
        | CModuleDef
        | CModulePropertySupport,
        ...,
    ] = ()
    functions: tuple[CFunction, ...] = ()


@dataclass
class FortranUse(StageRecord):
    """Fortran use statement."""

    module: str
    only: tuple[str, ...] = ()


@dataclass
class FortranParameter(StageRecord):
    """Fortran procedure argument declaration."""

    name: str
    type_name: str
    attributes: tuple[str, ...] = ()


@dataclass
class FortranDeclaration(StageRecord):
    """Fortran local or result declaration."""

    name: str
    type_name: str
    attributes: tuple[str, ...] = ()


@dataclass
class FortranTypeDefinition(StageRecord):
    """One generated native support type with explicit typed components."""

    name: str
    components: tuple[FortranDeclaration, ...] = ()


@dataclass
class FortranAssignment(StageRecord):
    """Fortran assignment statement."""

    target: str
    expression: CodeExpression


@dataclass
class FortranPointerAssignment(StageRecord):
    """Fortran pointer association statement."""

    target: str
    expression: CodeExpression


@dataclass
class FortranNullify(StageRecord):
    """Nullify one generated pointer variable or component."""

    target: str


@dataclass
class FortranAllocate(StageRecord):
    """One explicit native allocation selected by completed handle policy."""

    target: str
    extents: tuple[CodeExpression, ...] = ()
    status: str | None = None


@dataclass
class FortranDeallocate(StageRecord):
    """One explicit native deallocation selected by completed handle policy."""

    target: str


@dataclass
class FortranCall(StageRecord):
    """Fortran call statement."""

    function_name: str
    arguments: tuple[CodeExpression, ...] = ()


@dataclass
class FortranIf(StageRecord):
    """Fortran conditional with nested executable statements."""

    condition: CodeExpression
    body: tuple[
        FortranAllocate
        | FortranAssignment
        | FortranDeallocate
        | FortranPointerAssignment
        | FortranNullify
        | FortranCall
        | FortranIf,
        ...,
    ] = ()
    else_body: tuple[
        FortranAllocate
        | FortranAssignment
        | FortranDeallocate
        | FortranPointerAssignment
        | FortranNullify
        | FortranCall
        | FortranIf,
        ...,
    ] = ()


@dataclass
class FortranCase(StageRecord):
    """One explicit or default branch in a Fortran select-case block."""

    value: int | None
    body: tuple[
        FortranAssignment | FortranPointerAssignment | FortranNullify | FortranCall | FortranIf | FortranSelectCase,
        ...,
    ] = ()


@dataclass
class FortranSelectCase(StageRecord):
    """Fortran select-case dispatch used by planned runtime-rank arrays."""

    expression: CodeExpression
    cases: tuple[FortranCase, ...] = ()


@dataclass
class FortranInterfaceProcedure(StageRecord):
    """One native procedure signature inside an explicit interface."""

    name: str
    imports: tuple[str, ...] = ()
    parameters: tuple[FortranParameter, ...] = ()
    parameter_declarations: tuple[FortranParameter, ...] = ()
    result_name: str | None = None
    result_type: str | None = None
    is_subroutine: bool = False
    bind_name: str | None = None
    bind_c: bool = False
    pure: bool = False


@dataclass
class FortranInterface(StageRecord):
    """Explicit native procedure interface required for optional dummies."""

    procedures: tuple[FortranInterfaceProcedure, ...] = ()
    abstract: bool = False


@dataclass
class FortranFunction(StageRecord):
    """Fortran function or subroutine body used by bridge generation."""

    name: str
    parameters: tuple[FortranParameter, ...] = ()
    result_name: str | None = None
    result_type: str | None = None
    bind_name: str | None = None
    bind_c: bool = False
    uses: tuple[FortranUse, ...] = ()
    implicit_none: bool = False
    interfaces: tuple[FortranInterface, ...] = ()
    declarations: tuple[FortranDeclaration, ...] = ()
    body: tuple[
        FortranAllocate
        | FortranAssignment
        | FortranDeallocate
        | FortranPointerAssignment
        | FortranNullify
        | FortranCall
        | FortranIf
        | FortranSelectCase,
        ...,
    ] = ()
    is_subroutine: bool = False
    internal_procedures: tuple[FortranFunction, ...] = ()


@dataclass
class FortranModule(StageRecord):
    """Generated Fortran module."""

    name: str
    uses: tuple[FortranUse, ...] = ()
    type_definitions: tuple[FortranTypeDefinition, ...] = ()
    interfaces: tuple[FortranInterface, ...] = ()
    declarations: tuple[FortranDeclaration, ...] = ()
    procedures: tuple[FortranFunction, ...] = ()
    standalone_procedures: tuple[FortranFunction, ...] = ()


if __name__ == "__main__":
    example_c_function = CFunction(
        "wrap_ping",
        "PyObject *",
        parameters=(CParameter("self", "PyObject *"),),
        body=(CReturn(CodeExpression("Py_None")),),
    )
    example_c_module = CModule("demo_wrapper", functions=(example_c_function,))
    example_fortran_function = FortranFunction(
        "bind_c_ping",
        bind_name="PING",
        bind_c=True,
        body=(FortranCall("native_ping"),),
        is_subroutine=True,
    )
    example_fortran_module = FortranModule("bind_c_demo_wrapper", procedures=(example_fortran_function,))

    print(
        f"C node tree: {type(example_c_module).__name__} -> "
        f"{example_c_function.name} -> {type(example_c_function.body[0]).__name__}"
    )
    print(
        f"Fortran node tree: {type(example_fortran_module).__name__} -> "
        f"{example_fortran_function.name} -> {type(example_fortran_function.body[0]).__name__}"
    )
    print("Source text rendered: False")
