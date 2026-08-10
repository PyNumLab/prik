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

    parser._resolve_signature_kinds(
        signature,
        {
            "api_mod": {"rk": "4 + 4", "rk_alias": "rk", "n": "3"},
        },
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
    parser._resolve_module_variable_kinds(module, {"api_mod": {"rk": "8", "rk_alias": "rk", "n": "3"}})

    assert module.variables[0].kind == "8"
    assert module.variables[0].shape == ["0:3"]
    assert module.variables[0].lbound == ["0"]
    assert module.variables[0].ubound == ["3"]
    assert module.variables[0].value == "5"

    assert parser._resolve_kind_expression("len=n + 1", {"n": "3"}) == "len=4"
    assert parser._resolve_symbol_reference("alias", {"alias": "target", "target": "8"}) == "8"
    assert parser._resolve_module_parameter_values(
        {"M": {"a": "4", "b": "a + 2", "rk": "selected_real_kind(12)", "dp": "rk"}}
    ) == {"m": {"a": "4", "b": "6", "rk": "selected_real_kind(12)", "dp": "selected_real_kind(12)"}}
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


def test_declaration_push_preserves_module_variables_parameters_and_bounds():
    parser = FortranParser()
    module = FortranModule("owner_mod")
    scope = _ParserScope(kind="module", name=module.name, model=module, module_owner=module.name)
    meta = parser._new_decl_meta("real", "rk")
    meta.update({"parameter": True, "shape": ["0:n"], "rank": 1})

    parser._helper_push_declaration_to_scope(
        scope,
        meta=meta,
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


def test_procedure_declaration_push_updates_dummy_or_records_local_type_and_duplicate_metadata():
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
    proc_meta = parser._new_decl_meta("procedure", "callback_iface")
    proc_meta["external"] = True

    parser._helper_push_declaration_to_scope(
        scope,
        meta=proc_meta,
        right="callback",
        role="procedure_symbol",
        filename="declarations.f90",
        lineno=9,
        source_line="procedure(callback_iface), external :: callback",
    )
    local_meta = parser._new_decl_meta("real", "rk")
    parser._helper_push_declaration_to_scope(
        scope,
        meta=local_meta,
        right="scratch",
        role="procedure_symbol",
        filename="declarations.f90",
        lineno=10,
        source_line="real(kind=rk) :: scratch",
    )

    assert signature.arguments[0].base_type == "procedure"
    assert signature.arguments[0].kind == "callback_iface"
    assert state["external_symbols"] == {"callback"}
    assert state["declared_local_types"] == {"scratch": {"base_type": "real", "kind": "rk"}}

    with pytest.raises(FortranParseError) as error:
        parser._helper_push_declaration_to_scope(
            scope,
            meta=parser._new_decl_meta("integer", ""),
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
    assert state["local_params"] == {"n": "4", "m": "n + 2"}
    assert state["legacy_local_params"] == set()
    assert state["implicit_typed_symbols"] == {}

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
    strict_state["implicit_none"] = True

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
    assert loose_state["local_params"] == {"ival": "2", "alpha": "1.0"}
    assert loose_state["implicit_typed_symbols"] == {"ival": "integer", "alpha": "real"}
    assert loose_state["legacy_local_params"] == set()


def test_namespace_collection_preserves_case_insensitive_dependencies_and_exact_payload(tmp_path: Path, monkeypatch):
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

    encodings = []
    original_read_text = Path.read_text

    def read_text(path, *args, **kwargs):
        encodings.append(kwargs.get("encoding"))
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)

    namespace = FortranParser()._helper_collect_namespace(tmp_path)

    ancestor = str(tmp_path / "ancestor.f90")
    parent = str(tmp_path / "parent.f90")
    helper = str(tmp_path / "helper.f90")
    child = str(tmp_path / "child.f90")
    grandchild = str(tmp_path / "grandchild.f90")
    units = str(tmp_path / "units.f90")

    assert encodings and set(encodings) == {"utf-8"}
    assert namespace["module_to_file"] == {
        "ancestor_mod": ancestor,
        "helper_mod": helper,
        "parent_mod": parent,
    }
    assert namespace["submodule_to_file"] == {
        "child_mod": child,
        "grandchild_mod": grandchild,
    }
    assert namespace["file_dependencies"] == {
        ancestor: [],
        child: [ancestor, helper, parent],
        grandchild: [child],
        helper: [],
        parent: [ancestor],
        units: [],
    }
    assert namespace["files"].index(ancestor) < namespace["files"].index(parent)
    assert namespace["files"].index(parent) < namespace["files"].index(child)
    assert namespace["files"].index(helper) < namespace["files"].index(child)
    assert namespace["files"].index(child) < namespace["files"].index(grandchild)
    assert {module.name for module in namespace["modules"]} == {"Ancestor_Mod", "Helper_Mod", "Parent_Mod"}
    assert {submodule.name for submodule in namespace["submodules"]} == {"Child_Mod", "Grandchild_Mod"}
    assert [program.name for program in namespace["programs"]] == ["Driver"]
    assert [block.name for block in namespace["block_data"]] == ["Init_Data"]
    assert {dtype.name for dtype in namespace["types"]} == {"Parent_State", "Child_State", "File_State"}
    assert {module.name: module.filename for module in namespace["modules"]} == {
        "Ancestor_Mod": ancestor,
        "Helper_Mod": helper,
        "Parent_Mod": parent,
    }
    assert {submodule.name: submodule.filename for submodule in namespace["submodules"]} == {
        "Child_Mod": child,
        "Grandchild_Mod": grandchild,
    }


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


def test_project_encoding_is_forwarded_to_directory_namespace_collection(tmp_path: Path):
    source = tmp_path / "latin1.f90"
    source.write_bytes("! caf\xe9\nmodule encoded_mod\nend module encoded_mod\n".encode("latin-1"))

    project = parse_fortran_project(tmp_path, encoding="latin-1")

    assert set(project.modules) == {"encoded_mod"}
    assert project.files[0].encoding == "latin-1"
    assert project.files[0].source.startswith("! caf\xe9")


def test_scope_include_import_and_derived_type_binding_contracts():
    parser = FortranParser()
    state = {}
    parser._proc_scope_add_include(state, "shared.inc")
    parser._proc_scope_add_imports(state, ["State_T", " ", "Callback"])

    assert state == {
        "includes": ["shared.inc"],
        "imports": {"state_t", "callback"},
    }

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
    state = {"signature": FortranProcedureSignature(name="work", kind="subroutine")}

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
