"""Tests split by stable ownership concept from `test_source_form_and_diagnostics_regressions.py`."""

import pytest
from pathlib import Path
from prik import FortranParseError
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranDerivedType,
    FortranModule,
    FortranProcedureSignature,
)
from prik.parsers.fortran.parser import (
    _Declaration,
    FortranParser,
    _ParserScope,
    parse_fortran_project,
)


def test_compile_time_resolution_helpers_preserve_kind_shape_values_and_literal_policy():
    parser = FortranParser()
    signature = FortranProcedureSignature(
        "consume",
        "subroutine",
        module="api_mod",
        arguments=[FortranArgument("values", base_type="real", kind="rk_alias", shape=["n + 1"])],
    )
    signature.variables["local_n"] = FortranArgument(
        "local_n",
        base_type="integer",
        value="n + 2",
        symbolic_value="n + 2",
        value_type="expression",
        is_parameter=True,
    )

    symbols = parser._resolve_compile_time_symbols(
        {
            "api_mod": {"rk": "4 + 4", "rk_alias": "rk", "n": "3"},
        }
    )
    parser._resolve_procedure_compile_time_facts(
        signature,
        symbols,
        resolve_shapes=True,
    )

    assert signature.arguments[0].kind == "8"
    assert signature.arguments[0].shape == ["4"]
    assert signature.variables["local_n"].value == "5"
    assert signature.variables["local_n"].symbolic_value == "n + 2"

    module = FortranModule("api_mod")
    module.variables.append(
        FortranArgument(
            "values",
            base_type="real",
            kind="rk_alias",
            shape=["0:n"],
            value="n + 2",
            symbolic_value="n + 2",
            value_type="expression",
            is_parameter=True,
        )
    )
    parser._resolve_module_like_compile_time_facts(module, symbols)

    assert module.variables[0].kind == "8"
    assert module.variables[0].shape == ["0:3"]
    assert module.variables[0].lbound == ["0"]
    assert module.variables[0].ubound == ["3"]
    assert module.variables[0].value == "5"

    assert parser._resolve_kind_expression("len=n + 1", {"n": "3"}) == "len=4"
    assert parser._resolve_symbol_reference("alias", {"alias": "target", "target": "8"}) == "8"
    resolved = parser._resolve_compile_time_symbols(
        {"M": {"a": "4", "b": "a + 2", "rk": "selected_real_kind(12)", "dp": "rk"}}
    )
    assert dict(resolved.in_module("m")) == {
        "a": "4",
        "b": "6",
        "rk": "selected_real_kind(12)",
        "dp": "selected_real_kind(12)",
    }
    assert parser._collect_relevant_local_params(
        FortranProcedureSignature(
            "shape",
            "subroutine",
            arguments=[FortranArgument("values", kind="rk", shape=["n"])],
        ),
        {"rk": "base", "base": "4", "n": "m + 1", "m": "3", "unused": "10"},
    ) == {"rk": "base", "base": "4", "n": "m + 1", "m": "3"}
    assert parser._extract_symbol_names("n + max(m, 2) .and. flag") == {"n", "max", "m", "flag"}
    assert parser._normalize_parameter_value("2.0d+0") == "2"
    assert parser._normalize_parameter_value("selected_real_kind(12)") is None
    assert parser._is_literal_parameter_value("(/ 1, 2, .true. /)") is True
    assert parser._safe_eval_int_expr("max(3, 7) + len_trim('abc   ')") == 10
    assert parser._infer_implicit_base_type("index") == "integer"
    assert parser._infer_implicit_base_type("alpha") == "real"


def test_declaration_storage_preserves_module_variables_parameters_visibility_and_bounds():
    parser = FortranParser()
    module = FortranModule("owner_mod")
    scope = _ParserScope(kind="module", name=module.name, model=module, module_owner=module.name)
    declaration = parser._new_declaration("real", "rk")
    parser._apply_declaration_attributes(
        declaration,
        ["parameter", "private", "dimension(0:n)"],
    )

    parser._store_declaration(
        scope,
        declaration=declaration,
        right="weights = 1.0_rk",
        role="module_variable",
        filename="declarations.f90",
        lineno=4,
        source_line="real(kind=rk), parameter, dimension(0:n) :: weights = 1.0_rk",
    )

    assert [(var.name, var.base_type, var.kind, var.shape, var.lbound, var.ubound) for var in module.variables] == [
        ("weights", "real", "rk", ["0:n"], ["0"], ["n"])
    ]
    assert module.variables[0].is_parameter is True
    assert module.variables[0].value == "1"
    assert module.variables[0].symbolic_value == "1.0_rk"
    assert module.variables[0].value_type == "expression"
    assert module.private_symbols == ["weights"]


def test_procedure_declaration_storage_updates_dummy_or_records_local_type_and_duplicate_metadata():
    parser = FortranParser()
    signature = FortranProcedureSignature(
        "apply",
        "subroutine",
        arguments=[FortranArgument("callback"), FortranArgument("value")],
    )
    state = parser._new_procedure_scope_state(
        signature,
        symbols={argument.name.lower(): argument for argument in signature.arguments},
    )
    scope = _ParserScope(kind="procedure", name=signature.name, model=signature, state=state)
    procedure_declaration = parser._new_declaration("procedure", "callback_iface")
    procedure_declaration.external = True

    parser._store_declaration(
        scope,
        declaration=procedure_declaration,
        right="callback",
        role="procedure_symbol",
        filename="declarations.f90",
        lineno=9,
        source_line="procedure(callback_iface), external :: callback",
    )
    local_declaration = parser._new_declaration("real", "rk")
    parser._store_declaration(
        scope,
        declaration=local_declaration,
        right="scratch",
        role="procedure_symbol",
        filename="declarations.f90",
        lineno=10,
        source_line="real(kind=rk) :: scratch",
    )

    assert signature.arguments[0].base_type == "procedure"
    assert signature.arguments[0].kind == "callback_iface"
    assert state.external_symbols == {"callback"}
    assert state.declared_local_types == {"scratch": _Declaration(base_type="real", kind="rk")}

    with pytest.raises(FortranParseError) as error:
        parser._store_declaration(
            scope,
            declaration=parser._new_declaration("integer", ""),
            right="callback",
            role="procedure_symbol",
            filename="declarations.f90",
            lineno=11,
            source_line="integer :: callback",
        )

    assert error.value.base_message == "Duplicate declaration of symbol 'callback' in procedure 'apply'."
    assert error.value.filename == "declarations.f90"
    assert error.value.line_number == 11
    assert error.value.source_line == "integer :: callback"
    assert error.value.code == "PARSE_DUPLICATE_DECLARATION"


def test_entity_character_length_uses_an_independent_typed_declaration():
    parser = FortranParser()
    declaration = parser._new_declaration("character", "default_len")

    entity_declaration = parser._entity_declaration("label*(name_len)", declaration)

    assert entity_declaration is not declaration
    assert entity_declaration.kind == "name_len"
    assert entity_declaration.character_length_syntax is True
    assert declaration.kind == "default_len"
    assert declaration.character_length_syntax is False


def test_procedure_finalization_consumes_typed_local_declarations():
    parser = FortranParser()
    signature = FortranProcedureSignature(
        "consume",
        "subroutine",
        arguments=[FortranArgument("value")],
    )
    state = parser._new_procedure_scope_state(
        signature,
        symbols={"value": signature.arguments[0]},
    )
    state.declared_local_types["value"] = _Declaration(
        base_type="real",
        kind="rk",
        declared_storage_bits=64,
    )
    state.declared_local_types["n"] = _Declaration(
        base_type="integer",
        kind="i4",
        target_kind_expression="kind(1)",
    )

    parser._reconcile_procedure_local_declarations(signature, state)
    parser._materialize_procedure_parameters(signature, state, {"n": "4"})

    assert signature.arguments[0].base_type == "real"
    assert signature.arguments[0].kind == "rk"
    assert signature.arguments[0].declared_storage_bits == 64
    assert signature.variables["n"].base_type == "integer"
    assert signature.variables["n"].kind == "i4"
    assert signature.variables["n"].target_kind_expression == "kind(1)"


def test_procedure_parameter_lines_preserve_local_parameter_state_and_duplicate_metadata():
    parser = FortranParser()
    signature = FortranProcedureSignature("shape", "subroutine", arguments=[FortranArgument("values")])
    state = parser._new_procedure_scope_state(
        signature,
        symbols={"values": signature.arguments[0]},
    )

    assert parser._handle_proc_parameter_line(
        "integer, parameter :: n = 4, m = n + 2",
        state,
        filename="parameters.f90",
        lineno=5,
        source_line="integer, parameter :: n = 4, m = n + 2",
    )
    assert state.local_params == {"n": "4", "m": "n + 2"}
    assert state.legacy_local_params == set()
    assert state.implicit_typed_symbols == {}

    with pytest.raises(FortranParseError) as error:
        parser._handle_proc_parameter_line(
            "integer, parameter :: n = 8",
            state,
            filename="parameters.f90",
            lineno=6,
            source_line="integer, parameter :: n = 8",
        )

    assert error.value.base_message == "Duplicate PARAMETER declaration of symbol 'n' in procedure 'shape'."
    assert error.value.filename == "parameters.f90"
    assert error.value.line_number == 6
    assert error.value.source_line == "integer, parameter :: n = 8"
    assert error.value.code == "PARSE_DUPLICATE_PARAMETER"


def test_legacy_parameter_lines_respect_implicit_none_and_implicit_typing_contracts():
    parser = FortranParser()
    strict_signature = FortranProcedureSignature("strict", "subroutine")
    strict_state = parser._new_procedure_scope_state(strict_signature, symbols={})
    strict_state.implicit_none = True

    with pytest.raises(FortranParseError) as error:
        parser._handle_proc_parameter_line(
            "parameter (zero = 0.0e+0)",
            strict_state,
            filename="parameters.f90",
            lineno=8,
            source_line="parameter (zero = 0.0e+0)",
        )

    assert error.value.base_message == "Unknown datatype for PARAMETER symbol 'zero' in procedure 'strict'."
    assert error.value.filename == "parameters.f90"
    assert error.value.line_number == 8
    assert error.value.source_line == "parameter (zero = 0.0e+0)"
    assert error.value.code == "PARSE_UNKNOWN_PARAMETER_TYPE"

    loose_signature = FortranProcedureSignature("loose", "subroutine")
    loose_state = parser._new_procedure_scope_state(loose_signature, symbols={})
    assert parser._handle_proc_parameter_line(
        "parameter (ival = 2, alpha = 1.0)",
        loose_state,
        filename="parameters.f90",
        lineno=9,
        source_line="parameter (ival = 2, alpha = 1.0)",
    )
    assert loose_state.local_params == {"ival": "2", "alpha": "1.0"}
    assert loose_state.implicit_typed_symbols == {"ival": "integer", "alpha": "real"}
    assert loose_state.legacy_local_params == set()


def test_directory_project_parses_once_and_assembles_dependency_ordered_models(tmp_path: Path, monkeypatch):
    sources = {
        "ancestor.f90": "module Ancestor_Mod\nend module Ancestor_Mod\n",
        "parent.f90": "module Parent_Mod\n  use Ancestor_Mod\n  type :: Parent_State\n  end type Parent_State\nend module Parent_Mod\n",
        "helper.f90": "module Helper_Mod\nend module Helper_Mod\n",
        "child.f90": (
            "submodule (Ancestor_Mod:Parent_Mod) Child_Mod\n"
            "  use Helper_Mod\n"
            "  type :: Child_State\n"
            "  end type Child_State\n"
            "end submodule Child_Mod\n"
        ),
        "grandchild.f90": "submodule (Child_Mod) Grandchild_Mod\nend submodule Grandchild_Mod\n",
        "units.f90": (
            "type :: File_State\n"
            "end type File_State\n"
            "program Driver\n"
            "  use Parent_Mod\n"
            "end program Driver\n"
            "block data Init_Data\n"
            "  integer :: seed\n"
            "end block data Init_Data\n"
        ),
    }
    for filename, source in sources.items():
        (tmp_path / filename).write_text(source, encoding="utf-8")

    read_paths: list[Path] = []
    encodings: list[str | None] = []
    original_read_text = Path.read_text

    def read_text(path, *args, **kwargs):
        read_paths.append(path)
        encodings.append(kwargs.get("encoding"))
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)

    project = parse_fortran_project(tmp_path)

    ancestor = str(tmp_path / "ancestor.f90")
    parent = str(tmp_path / "parent.f90")
    helper = str(tmp_path / "helper.f90")
    child = str(tmp_path / "child.f90")
    grandchild = str(tmp_path / "grandchild.f90")
    units = str(tmp_path / "units.f90")

    assert len(read_paths) == len(sources)
    assert set(read_paths) == {tmp_path / filename for filename in sources}
    assert set(encodings) == {"utf-8"}

    ordered_files = [parsed_file.filename for parsed_file in project.files]
    assert ordered_files.index(ancestor) < ordered_files.index(parent)
    assert ordered_files.index(parent) < ordered_files.index(child)
    assert ordered_files.index(helper) < ordered_files.index(child)
    assert ordered_files.index(child) < ordered_files.index(grandchild)
    assert units in ordered_files

    assert {module.name for module in project.modules.values()} == {
        "Ancestor_Mod",
        "Helper_Mod",
        "Parent_Mod",
    }
    assert {submodule.name for submodule in project.submodules.values()} == {
        "Child_Mod",
        "Grandchild_Mod",
    }
    assert [program.name for program in project.programs.values()] == ["Driver"]
    assert [block.name for parsed_file in project.files for block in parsed_file.block_data_units] == ["Init_Data"]
    assert {dtype.name for dtype in project.derived_types.values()} == {
        "Parent_State",
        "Child_State",
        "File_State",
    }
    assert {module.name: module.filename for module in project.modules.values()} == {
        "Ancestor_Mod": ancestor,
        "Helper_Mod": helper,
        "Parent_Mod": parent,
    }
    assert {submodule.name: submodule.filename for submodule in project.submodules.values()} == {
        "Child_Mod": child,
        "Grandchild_Mod": grandchild,
    }
    assert project.dependencies["parent_mod"] == {"ancestor_mod"}
    assert project.dependencies["child_mod"] == {"ancestor_mod", "parent_mod", "helper_mod"}
    assert project.dependencies["grandchild_mod"] == {"child_mod"}


def test_project_registries_preserve_qualified_aliases_values_and_dependencies():
    project = parse_fortran_project(
        {
            "api.f90": """
module api_mod
  type :: state_t
    integer :: id
  end type state_t
  interface callback
    subroutine on_step(x)
      integer, intent(in) :: x
    end subroutine on_step
  end interface callback
contains
  subroutine step(x)
    real, intent(in) :: x
  end subroutine step
end module api_mod
""",
            "child.f90": """
submodule (api_mod) child_mod
  type :: child_state_t
    integer :: id
  end type child_state_t
  interface child_callback
    subroutine child_step(x)
      integer, intent(in) :: x
    end subroutine child_step
  end interface child_callback
contains
  module procedure reset
  end procedure reset
end submodule child_mod
""",
            "units.f90": """
type :: global_state_t
  integer :: id
end type global_state_t
interface global_callback
  subroutine global_step()
  end subroutine global_step
end interface global_callback
program driver
  use api_mod
end program driver
""",
        }
    )

    module = project.modules["api_mod"]
    submodule = project.submodules["child_mod"]

    assert set(project.modules) == {"api_mod"}
    assert set(project.submodules) == {"child_mod"}
    assert set(project.programs) == {"driver"}
    assert project.dependencies == {
        "api_mod": set(),
        "child_mod": {"api_mod"},
        "driver": {"api_mod"},
    }
    assert set(project.procedures) == {"api_mod.step", "step", "child_mod.reset", "reset"}
    assert project.procedures["api_mod.step"] is project.procedures["step"] is module.procedures[0]
    assert project.procedures["child_mod.reset"] is project.procedures["reset"] is submodule.procedures[0]
    assert set(project.derived_types) == {
        "api_mod.state_t",
        "state_t",
        "child_mod.child_state_t",
        "child_state_t",
        "global_state_t",
    }
    assert project.derived_types["api_mod.state_t"] is project.derived_types["state_t"]
    assert project.derived_types["child_mod.child_state_t"] is project.derived_types["child_state_t"]
    assert set(project.interfaces) == {
        "api_mod.callback",
        "callback",
        "child_mod.child_callback",
        "child_callback",
        "global_callback",
    }
    assert project.interfaces["api_mod.callback"] is project.interfaces["callback"]
    assert project.interfaces["child_mod.child_callback"] is project.interfaces["child_callback"]


@pytest.mark.parametrize("standalone_first", [False, True])
def test_standalone_procedure_owns_unqualified_name_shared_with_module_member(standalone_first):
    module_source = """
module nan_mod
contains
  logical function sisnan(value)
    real, intent(in) :: value
  end function sisnan
end module nan_mod
"""
    standalone_source = """
logical function sisnan(value)
  real, intent(in) :: value
end function sisnan
"""
    sources = [("standalone.f90", standalone_source), ("module.f90", module_source)]
    if not standalone_first:
        sources.reverse()

    project = parse_fortran_project(dict(sources))
    module_procedure = project.modules["nan_mod"].procedures[0]
    standalone_procedure = next(procedure for parsed_file in project.files for procedure in parsed_file.procedures)

    assert project.procedures["nan_mod.sisnan"] is module_procedure
    assert project.procedures["sisnan"] is standalone_procedure


def test_parse_file_preserves_top_level_models_but_limits_file_symbol_registry():
    parsed = FortranParser().parse_file(
        """
type :: file_state_t
end type file_state_t
interface file_callback
  subroutine on_file()
  end subroutine on_file
end interface file_callback
subroutine global_step()
end subroutine global_step
module api_mod
contains
  subroutine module_step()
  end subroutine module_step
end module api_mod
""",
        filename="parse_file_contract.f90",
    )

    assert [dtype.name for dtype in parsed.derived_types] == ["file_state_t"]
    assert [interface.name for interface in parsed.interfaces] == ["file_callback"]
    assert [procedure.name for procedure in parsed.procedures] == ["global_step"]
    assert [module.name for module in parsed.modules] == ["api_mod"]
    assert set(parsed.symbols) == {"api_mod", "global_step"}
    assert parsed.symbols["api_mod"] is parsed.modules[0]
    assert parsed.symbols["global_step"] is parsed.procedures[0]


def test_parse_project_resolves_cross_file_used_module_parameters_once():
    project = parse_fortran_project(
        {
            "precision.f90": """
module precision_mod
  integer, parameter :: rk = 8
end module precision_mod
""",
            "api.f90": """
module api_mod
  use precision_mod
contains
  subroutine consume(value)
    real(kind=rk), intent(in) :: value
  end subroutine consume
end module api_mod
""",
        }
    )

    procedure = project.procedures["api_mod.consume"]
    assert procedure is project.procedures["consume"]
    assert procedure.arguments[0].kind == "8"
    assert project.dependencies == {
        "api_mod": {"precision_mod"},
        "precision_mod": set(),
    }


def test_parse_project_rejects_duplicate_modules_across_files_with_project_scope_metadata():
    with pytest.raises(FortranParseError) as duplicate:
        parse_fortran_project(
            {
                "first.f90": "module shared_mod\nend module shared_mod\n",
                "second.f90": "module shared_mod\nend module shared_mod\n",
            }
        )

    assert duplicate.value.base_message == "Duplicate symbol 'shared_mod' in project module scope."
    assert duplicate.value.filename is None
    assert duplicate.value.line_number is None
    assert duplicate.value.source_line is None
    assert duplicate.value.code == "PARSE_DUPLICATE_SYMBOL"


def test_project_topological_files_are_dependency_first_sorted_and_cycle_tolerant():
    ordered = FortranParser._topological_files(
        {
            "consumer.f90": {"module_a.f90", "module_b.f90"},
            "module_b.f90": set(),
            "module_a.f90": set(),
            "cycle_left.f90": {"cycle_right.f90"},
            "cycle_right.f90": {"cycle_left.f90"},
        }
    )

    assert ordered[:3] == ["module_a.f90", "module_b.f90", "consumer.f90"]
    assert ordered[3:] == ["cycle_left.f90", "cycle_right.f90"]


def test_project_encoding_is_forwarded_to_explicit_path_inputs(tmp_path: Path):
    source = tmp_path / "latin1.f90"
    source.write_bytes("! caf\xe9\nmodule encoded_mod\nend module encoded_mod\n".encode("latin-1"))

    project = parse_fortran_project([source], encoding="latin-1")

    assert project.files[0].encoding == "latin-1"
    assert project.files[0].source.startswith("! caf\xe9")


def test_project_encoding_is_forwarded_to_directory_file_parsing(tmp_path: Path):
    source = tmp_path / "latin1.f90"
    source.write_bytes("! caf\xe9\nmodule encoded_mod\nend module encoded_mod\n".encode("latin-1"))

    project = parse_fortran_project(tmp_path, encoding="latin-1")

    assert set(project.modules) == {"encoded_mod"}
    assert project.files[0].encoding == "latin-1"
    assert project.files[0].source.startswith("! caf\xe9")


def test_scope_include_import_and_derived_type_binding_contracts():
    parser = FortranParser()
    state = parser._new_procedure_scope_state(
        FortranProcedureSignature("scope_contract", "subroutine"),
        symbols={},
    )
    parser._proc_scope_add_include(state, "shared.inc")
    parser._proc_scope_add_imports(state, ["State_T", " ", "Callback"])

    assert state.includes == ["shared.inc"]
    assert state.imports == {"state_t", "callback"}

    dtype = parser._init_derived_type(
        "type, extends(parent(kind)), public :: child",
        current_module="owner_mod",
    )
    assert dtype == FortranDerivedType(
        name="child",
        module="owner_mod",
        extends="parent(kind)",
        attributes=["public"],
    )
    malformed = parser._init_derived_type("type, extends(parent :: child", current_module="owner_mod")
    assert malformed == FortranDerivedType(
        name="child",
        module="owner_mod",
        attributes=["extends(parent"],
    )

    parser._parse_derived_type_contains_line("procedure, pass(self), public :: update, reset", dtype)
    parser._parse_derived_type_contains_line("generic, public :: assignment(=) => assign_child, assign_other", dtype)
    parser._parse_derived_type_contains_line("FINAL :: cleanup, destroy", dtype)

    assert dtype.methods == ["update", "reset"]
    assert dtype.procedure_bindings == [
        {"name": "update", "attrs": ["pass(self)", "public"]},
        {"name": "reset", "attrs": ["pass(self)", "public"]},
    ]
    assert dtype.generic_bindings == [
        {
            "name": "assignment(=)",
            "targets": ["assign_child", "assign_other"],
            "attrs": ["public"],
        }
    ]


def test_unknown_procedure_declaration_kind_preserves_declaration_and_invalid_syntax_split():
    parser = FortranParser()
    state = parser._new_procedure_scope_state(
        FortranProcedureSignature(name="work", kind="subroutine"),
        symbols={},
    )

    with pytest.raises(FortranParseError) as declaration_error:
        parser._handle_unknown_proc_declaration(
            "vector(kind=4) :: value",
            state,
            filename="procedure_contract.f90",
            lineno=9,
            source_line="vector(kind=4) :: value",
        )

    assert (
        declaration_error.value.base_message
        == "Unknown or unsupported datatype declaration for procedure 'work': vector(kind=4) :: value"
    )
    assert declaration_error.value.filename == "procedure_contract.f90"
    assert declaration_error.value.line_number == 9
    assert declaration_error.value.source_line == "vector(kind=4) :: value"
    assert declaration_error.value.code == "PARSE_UNSUPPORTED_DECLARATION"

    with pytest.raises(FortranParseError) as syntax_error:
        parser._handle_unknown_proc_declaration(
            "call work()",
            state,
            filename="procedure_contract.f90",
            lineno=10,
            source_line="call work()",
        )

    assert (
        syntax_error.value.base_message == "Invalid Fortran syntax in procedure 'work' specification part: call work()"
    )
    assert syntax_error.value.filename == "procedure_contract.f90"
    assert syntax_error.value.line_number == 10
    assert syntax_error.value.source_line == "call work()"
    assert syntax_error.value.code == "PARSE_INVALID_SYNTAX"


def test_derived_type_collection_retains_sibling_and_nested_scope_contexts():
    parser = FortranParser()
    types = parser._collect_derived_type_source_units(
        """
type :: global_state
end type global_state
module owner_mod
  type :: first_state
  end type first_state
  type :: second_state
  end type second_state
contains
  subroutine work()
    type :: local_state
    end type local_state
  end subroutine work
end module owner_mod
""",
        filename="nested_types.f90",
    )

    assert [(unit.name, scope.kind, scope.name, scope.module_owner) for unit, scope in types] == [
        ("global_state", "file", None, None),
        ("first_state", "module", "owner_mod", "owner_mod"),
        ("second_state", "module", "owner_mod", "owner_mod"),
        ("local_state", "procedure", "work", "owner_mod"),
    ]
    assert [(scope.parent.kind, scope.parent.name) if scope.parent else None for _unit, scope in types] == [
        None,
        ("file", None),
        ("file", None),
        ("module", "owner_mod"),
    ]
