"""Fortran accessibility decides which use-associated entities a module publishes.

Accessibility is settled by precedence: an access statement naming the entity
decides it, otherwise the module's bare `public`/`private` default does, and
that default is itself `public`. Those rules cover a use-associated entity, so
an ordinary module publishes what it imports without naming it anywhere.

Every route to a name is read the same way whichever form of `use` it entered
by (bare, `only`, renamed, repeated), and each hop of a transitive chain applies
the rule again. Routes that agree on one declaration name one entity; routes
that disagree, or that pass through a module this project cannot read, leave
the name unresolved rather than guessing.
"""

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_project
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

DECLARING = (NATIVE_FIXTURES / "declaring_module.f90").read_text(encoding="utf-8")

NAMED_GENERIC = (NATIVE_FIXTURES / "a_plain_use_carries_a_named_generic_interface.f90").read_text(encoding="utf-8")

TRANSITIVE_DECLARING = (NATIVE_FIXTURES / "transitive_declaring.f90").read_text(encoding="utf-8")

TRANSITIVE_OTHER = (NATIVE_FIXTURES / "transitive_other.f90").read_text(encoding="utf-8")

CALLBACK_HOME = """\
module callback_types
  implicit none
  abstract interface
    integer function unary(x)
      integer, intent(in) :: x
    end function unary
  end interface
end module callback_types
"""

LOCAL_HOME = """\
module local_home
  implicit none
contains
  subroutine work()
{local}
  end subroutine work
end module local_home

module b_mod
  use local_home
  implicit none
end module b_mod
"""

ENUM_HOME = """\
module colors_mod
  implicit none
  enum, bind(c)
    enumerator :: red = 1
    enumerator :: green = 2
  end enum
end module colors_mod
"""

Q_HOME = """\
module a_mod
  implicit none
  integer :: q = 1
  integer :: other = 2
end module a_mod
"""

USER_ISO_FORTRAN_ENV = """\
module iso_fortran_env
  implicit none
  integer :: my_value = 7
end module iso_fortran_env
"""

CRATE_IMPORTER = """\
module b_mod
  use a_mod, only : crate => box
  implicit none
{access}
contains
  integer function crate_value(item) result(out)
    type(crate), intent(in) :: item
    out = item%value
  end function crate_value
end module b_mod
"""


def _modules(tmp_path: Path, *sources: str):
    """Parse one throwaway project and return its semantic modules by name."""
    (tmp_path / "project.f90").write_text("\n".join(sources), encoding="utf-8")
    modules = fortran_project_to_semantic_modules(parse_fortran_project(str(tmp_path)))
    return {module.name: module for module in modules}


def _row(id_: str, sources: tuple[str, ...], expected: list[tuple[str, str, str, str]], module: str = "b_mod"):
    return pytest.param(sources, module, expected, id=id_)


A_MOD_PUBLIC = [
    ("box", "box", "a_mod", "derived_type"),
    ("scale_value", "scale_value", "a_mod", "procedure"),
    ("x", "x", "a_mod", "variable"),
    ("y", "y", "a_mod", "variable"),
]
X_FROM_A = [("x", "x", "a_mod", "variable")]
X_UNRESOLVED_AT_MIDDLE = [("x", "x", "middle_mod", "unknown")]
UNARY = [("unary", "unary", "callback_types", "prototype")]

PUBLICATION_CASES = [
    # Accessibility precedence over the module default.
    _row("default-public-only-list", (DECLARING, "module b_mod\n  use a_mod, only : x\nend module b_mod\n"), X_FROM_A),
    _row(
        "default-public-procedure",
        (DECLARING, "module b_mod\n  use a_mod, only : scale_value\nend module b_mod\n"),
        [("scale_value", "scale_value", "a_mod", "procedure")],
    ),
    _row(
        "declaration-dependency-stays-public",
        (DECLARING, CRATE_IMPORTER.format(access="")),
        [("crate", "box", "a_mod", "derived_type")],
    ),
    _row(
        "explicit-public-declaration-dependency",
        (DECLARING, CRATE_IMPORTER.format(access="  public :: crate")),
        [("crate", "box", "a_mod", "derived_type")],
    ),
    _row(
        "third-module-resolves-through-importer",
        (
            DECLARING,
            "module b_mod\n  use a_mod, only : box\n  type(box) :: stored\nend module b_mod\n",
            "module c_mod\n  use b_mod, only : box\n  type(box) :: another\nend module c_mod\n",
        ),
        [("box", "box", "a_mod", "derived_type")],
        module="c_mod",
    ),
    _row("private-default", (DECLARING, "module b_mod\n  use a_mod, only : x\n  private\nend module b_mod\n"), []),
    _row(
        "public-name-over-private-default",
        (DECLARING, "module b_mod\n  use a_mod, only : x\n  private\n  public :: x\nend module b_mod\n"),
        X_FROM_A,
    ),
    _row(
        "private-name-over-public-default",
        (DECLARING, "module b_mod\n  use a_mod, only : x\n  private :: x\nend module b_mod\n"),
        [],
    ),
    _row("private-module-route", (DECLARING, "module b_mod\n  use a_mod\n  private :: a_mod\nend module b_mod\n"), []),
    _row(
        "public-module-route-over-private-default",
        (DECLARING, "module b_mod\n  use a_mod\n  private\n  public :: a_mod\nend module b_mod\n"),
        A_MOD_PUBLIC,
    ),
    _row(
        "any-public-route-keeps-an-entity-public",
        (
            DECLARING,
            "module left_mod\n  use a_mod, only : x\nend module left_mod\n",
            "module right_mod\n  use a_mod, only : x\nend module right_mod\n",
            "module b_mod\n  use left_mod\n  use right_mod\n  private :: left_mod\n  public :: right_mod\nend module b_mod\n",
        ),
        X_FROM_A,
    ),
    _row(
        "rename-publishes-the-local-name",
        (DECLARING, "module b_mod\n  use a_mod, only : renamed => y\nend module b_mod\n"),
        [("renamed", "y", "a_mod", "variable")],
    ),
    _row(
        "plain-use-carries-every-public-name",
        (DECLARING, "module b_mod\n  use a_mod\nend module b_mod\n"),
        A_MOD_PUBLIC,
    ),
    _row(
        "plain-use-carries-a-named-generic-interface",
        (NAMED_GENERIC,),
        [
            ("convert", "convert", "generic_home", "generic"),
            ("convert_i", "convert_i", "generic_home", "procedure"),
            ("convert_r", "convert_r", "generic_home", "procedure"),
        ],
    ),
    _row(
        "plain-use-under-private-default-carries-nothing",
        (DECLARING, "module b_mod\n  use a_mod\n  private\nend module b_mod\n"),
        [],
    ),
    # An abstract block names no generic; what it declares are its procedures.
    _row(
        "plain-use-carries-an-abstract-interface-procedure",
        (CALLBACK_HOME, "module middle_mod\n  use callback_types\nend module middle_mod\n"),
        UNARY,
        module="middle_mod",
    ),
    _row(
        "abstract-interface-procedure-survives-a-further-hop",
        (
            CALLBACK_HOME,
            "module middle_mod\n  use callback_types\nend module middle_mod\n",
            "module user_mod\n  use middle_mod, only : unary\nend module user_mod\n",
        ),
        UNARY,
        module="user_mod",
    ),
    # Callback accessibility is the module's accessibility, routes included: a
    # bare `private` would hide the name were the used module not named public.
    _row(
        "callback-through-a-public-route-stays-public",
        (
            CALLBACK_HOME,
            "module facade_mod\n  use callback_types\n  private\n  public :: callback_types\nend module facade_mod\n",
        ),
        UNARY,
        module="facade_mod",
    ),
    _row(
        "callback-through-a-private-route-is-withheld",
        (
            CALLBACK_HOME,
            "module facade_mod\n  use callback_types\n  private :: callback_types\nend module facade_mod\n",
        ),
        [],
        module="facade_mod",
    ),
    # Agreeing and disagreeing routes.
    _row(
        "routes-agreeing-on-one-entity-publish-it",
        (
            DECLARING,
            "module middle_mod\n  use a_mod, only : x\nend module middle_mod\n",
            "module b_mod\n  use a_mod, only : x\n  use middle_mod, only : x\nend module b_mod\n",
        ),
        X_FROM_A,
    ),
    # An unparsed module may carry the same entity or another one, so choosing
    # the readable route would be a guess about the one this project cannot read.
    _row(
        "readable-route-beside-an-unreadable-one-is-not-guessed",
        (DECLARING, "module b_mod\n  use a_mod, only : x\n  use external_mod, only : x\nend module b_mod\n"),
        [],
    ),
    _row(
        "single-unreadable-route-names-what-it-reached",
        (DECLARING, "module b_mod\n  use external_mod, only : y\nend module b_mod\n"),
        [("y", "y", "external_mod", "unknown")],
    ),
    _row(
        "wildcard-route-beside-an-unreadable-one-is-not-guessed",
        (
            DECLARING,
            "module left_mod\n  use a_mod, only : x\nend module left_mod\n",
            "module right_mod\n  use external_mod, only : x\nend module right_mod\n",
            "module b_mod\n  use left_mod\n  use right_mod\nend module b_mod\n",
        ),
        [],
    ),
    _row(
        "wildcard-routes-agreeing-on-one-entity-publish-it",
        (
            DECLARING,
            "module left_mod\n  use a_mod, only : x\nend module left_mod\n",
            "module b_mod\n  use left_mod\n  use a_mod, only : x\nend module b_mod\n",
        ),
        X_FROM_A,
    ),
    # How a route entered says nothing about what it carries: examining the
    # named route first would publish `a_mod::x`, and a re-exported module
    # variable generates native access to that owner directly.
    _row(
        "named-and-wildcard-routes-to-different-entities-stay-unresolved",
        (
            TRANSITIVE_DECLARING,
            TRANSITIVE_OTHER,
            "module b_mod\n  use a_mod, only : x\n  use c_mod\nend module b_mod\n",
        ),
        [],
    ),
    _row(
        "named-and-wildcard-routes-to-one-entity-resolve-together",
        (
            TRANSITIVE_DECLARING,
            "module pass_mod\n  use a_mod\nend module pass_mod\n",
            "module b_mod\n  use a_mod, only : x\n  use pass_mod\nend module b_mod\n",
        ),
        X_FROM_A,
    ),
    # PRIK cannot enumerate an unread module, so it is not a route for a name.
    _row(
        "unparsed-plain-use-carries-no-assumed-name",
        (TRANSITIVE_DECLARING, "module b_mod\n  use a_mod, only : x\n  use external_mod\nend module b_mod\n"),
        X_FROM_A,
    ),
    # A block written inside a contained procedure declares a name only there.
    _row(
        "procedure-local-abstract-interface-stays-in-its-procedure",
        (
            LOCAL_HOME.format(
                local="    abstract interface\n      subroutine local_callback()\n      end subroutine local_callback\n"
                "    end interface"
            ),
        ),
        [("work", "work", "local_home", "procedure")],
    ),
    _row(
        "procedure-local-generic-stays-in-its-procedure",
        (
            LOCAL_HOME.format(
                local="    interface local_generic\n      module procedure work\n    end interface local_generic"
            ),
        ),
        [("work", "work", "local_home", "procedure")],
    ),
    # Each hop of a transitive chain applies the same rule.
    _row(
        "private-name-in-an-intermediate-module-ends-the-chain",
        (
            TRANSITIVE_DECLARING,
            "module middle_mod\n  use a_mod, only : x\n  private :: x\nend module middle_mod\n",
            "module outer_mod\n  use middle_mod, only : x\nend module outer_mod\n",
        ),
        X_UNRESOLVED_AT_MIDDLE,
        module="outer_mod",
    ),
    _row(
        "routes-disagreeing-inside-an-intermediate-module-stay-unresolved",
        (
            TRANSITIVE_DECLARING,
            TRANSITIVE_OTHER,
            "module middle_mod\n  use a_mod, only : x\n  use c_mod, only : x\nend module middle_mod\n",
            "module outer_mod\n  use middle_mod, only : x\nend module outer_mod\n",
        ),
        X_UNRESOLVED_AT_MIDDLE,
        module="outer_mod",
    ),
    _row(
        "mixed-routes-through-an-intermediate-module-stay-unresolved",
        (
            TRANSITIVE_DECLARING,
            TRANSITIVE_OTHER,
            "module middle_mod\n  use a_mod, only : x\n  use c_mod\nend module middle_mod\n",
            "module outer_mod\n  use middle_mod, only : x\nend module outer_mod\n",
        ),
        X_UNRESOLVED_AT_MIDDLE,
        module="outer_mod",
    ),
    _row(
        "ordinary-chain-reaches-the-declaring-module",
        (
            TRANSITIVE_DECLARING,
            "module middle_mod\n  use a_mod, only : x\n  public :: x\nend module middle_mod\n",
            "module outer_mod\n  use middle_mod, only : x\nend module outer_mod\n",
        ),
        X_FROM_A,
        module="outer_mod",
    ),
    # An enum names constants, which is how every later stage models them.
    _row(
        "plain-use-carries-enumerators-as-constants",
        (ENUM_HOME, "module facade_mod\n  use colors_mod\nend module facade_mod\n"),
        [("green", "green", "colors_mod", "variable"), ("red", "red", "colors_mod", "variable")],
        module="facade_mod",
    ),
    _row(
        "only-list-names-an-enumerator",
        (ENUM_HOME, "module facade_mod\n  use colors_mod, only : red\nend module facade_mod\n"),
        [("red", "red", "colors_mod", "variable")],
        module="facade_mod",
    ),
    # ONLY, renaming, and repeated USE statements share one route interpretation.
    # A rename hides the source spelling; `only` narrows to what it lists (see
    # the default-public rows above).
    _row(
        "rename-without-only-hides-the-source-name",
        (Q_HOME, "module b_mod\n  use a_mod, p => q\nend module b_mod\n"),
        [("other", "other", "a_mod", "variable"), ("p", "q", "a_mod", "variable")],
    ),
    _row("empty-only-list", (TRANSITIVE_DECLARING, "module b_mod\n  use a_mod, only :\nend module b_mod\n"), []),
    _row(
        "repeated-statements",
        (Q_HOME, "module b_mod\n  use a_mod, only : p => q\n  use a_mod\nend module b_mod\n"),
        [("other", "other", "a_mod", "variable"), ("p", "q", "a_mod", "variable")],
    ),
    # A user module may share an intrinsic module's name; the `use` nature decides which is meant.
    _row(
        "non-intrinsic-names-the-user-module",
        (
            USER_ISO_FORTRAN_ENV,
            "module facade\n  use, non_intrinsic :: iso_fortran_env, only: my_value\nend module facade\n",
        ),
        [("my_value", "my_value", "iso_fortran_env", "variable")],
        module="facade",
    ),
    _row(
        "unstated-nature-prefers-the-parsed-module",
        (USER_ISO_FORTRAN_ENV, "module facade\n  use iso_fortran_env, only: my_value\nend module facade\n"),
        [("my_value", "my_value", "iso_fortran_env", "variable")],
        module="facade",
    ),
    _row(
        "intrinsic-names-the-processor-module",
        (USER_ISO_FORTRAN_ENV, "module facade\n  use, intrinsic :: iso_fortran_env, only: int32\nend module facade\n"),
        [("int32", "int32", "iso_fortran_env", "intrinsic")],
        module="facade",
    ),
    # Semantic resolution and source discovery share one inventory of processor modules.
    _row(
        "plain-use-of-an-ieee-module-names-the-processor-module",
        ("module facade\n  use ieee_arithmetic, only: ieee_is_nan\nend module facade\n",),
        [("ieee_is_nan", "ieee_is_nan", "ieee_arithmetic", "intrinsic")],
        module="facade",
    ),
]


@pytest.mark.parametrize(("sources", "module", "expected"), PUBLICATION_CASES)
def test_a_module_publishes_exactly_its_accessible_use_associations(
    sources: tuple[str, ...],
    module: str,
    expected: list[tuple[str, str, str, str]],
    tmp_path: Path,
):
    """Each published name records its local spelling, declaration, owner, and kind."""
    reexports = _modules(tmp_path, *sources)[module].reexports

    published = [(item.local_name, item.source_name, item.origin_module, item.entity_kind) for item in reexports]
    assert sorted(published) == sorted(expected)


@pytest.mark.parametrize(
    ("sources", "module", "name", "dependency"),
    [
        pytest.param(
            (DECLARING, CRATE_IMPORTER.format(access="")),
            "b_mod",
            "crate",
            True,
            id="a-dummy-type-is-a-dependency",
        ),
        pytest.param(
            (DECLARING, "module b_mod\n  use a_mod, only : box\n  type(box) :: item\nend module b_mod\n"),
            "b_mod",
            "box",
            True,
            id="a-declared-type-is-a-dependency",
        ),
        pytest.param(
            (
                DECLARING,
                'module b_mod\n  use a_mod, only : box\n  character(len=3), parameter :: label = "box"\nend module b_mod\n',
            ),
            "b_mod",
            "box",
            False,
            id="a-name-spelled-in-a-character-literal-is-not",
        ),
        pytest.param(
            (
                "module constants_mod\n  integer, parameter :: base = 10\nend module constants_mod\n",
                "module colors_mod\n  use constants_mod, only : base\n  enum, bind(c)\n"
                "    enumerator :: red = base\n  end enum\nend module colors_mod\n",
            ),
            "colors_mod",
            "base",
            True,
            id="an-enumerator-initializer-is-a-dependency",
        ),
    ],
)
def test_a_name_a_declaration_reads_is_a_declaration_dependency(
    sources: tuple[str, ...], module: str, name: str, dependency: bool, tmp_path: Path
):
    """A literal's contents are its value, not a reference to what they spell."""
    reexports = {item.local_name: item for item in _modules(tmp_path, *sources)[module].reexports}

    assert reexports[name].declaration_dependency is dependency


def test_a_compile_time_symbol_is_not_substituted_inside_a_character_literal():
    """A literal's contents are data, so a symbol spelled there is not a reference."""
    from prik.semantics.fortran2ir import _resolve_compile_time_text

    values = {"runtime": "4"}

    assert _resolve_compile_time_text('len("runtime")', values) == 'len("runtime")'
    # A reference outside the literal is still resolved, whatever its case, and
    # an unknown name is left as written.
    assert _resolve_compile_time_text("runtime + 1", values) == "4 + 1"
    assert _resolve_compile_time_text("RUNTIME + missing", values) == "4 + missing"
    assert _resolve_compile_time_text('len("runtime") + runtime', values) == 'len("runtime") + 4'


def test_a_non_only_rename_still_carries_imported_compile_time_symbols(tmp_path: Path):
    """Every consumer reads the same association, not just route resolution.

    `use kinds_mod, wp => rk` binds `wp` and still imports `nmax`, which a
    declaration's extent needs resolved.
    """
    (tmp_path / "project.f90").write_text(
        """\
module kinds_mod
  implicit none
  integer, parameter :: rk = 8
  integer, parameter :: nmax = 4
end module kinds_mod

module use_mod
  use kinds_mod, wp => rk
  implicit none
  real(wp) :: values(nmax)
end module use_mod
""",
        encoding="utf-8",
    )
    project = parse_fortran_project(str(tmp_path))
    declared = next(
        variable
        for parsed in project.files
        for module in parsed.modules
        if module.name == "use_mod"
        for variable in module.variables
    )

    assert (declared.kind, declared.shape) == ("8", ["4"])


USER_IEEE_ARITHMETIC = """\
module ieee_arithmetic
  implicit none
  abstract interface
    subroutine ieee_cb(x)
      real, intent(inout) :: x
    end subroutine ieee_cb
  end interface
  interface ieee_scale
    module procedure scale_real
  end interface ieee_scale
contains
  subroutine scale_real(x)
    real, intent(inout) :: x
  end subroutine scale_real
  pure integer function ieee_size(n)
    integer, intent(in) :: n
    ieee_size = n
  end function ieee_size
end module ieee_arithmetic
"""


@pytest.mark.parametrize(
    ("nature", "callback_storage", "bound_scope", "specifics"),
    [
        pytest.param("non_intrinsic", "callback", "ieee_arithmetic", ["scale_real", "scale_int"], id="user-module"),
        pytest.param("intrinsic", "reference", None, ["scale_int"], id="processor-module"),
    ],
)
def test_an_intrinsic_use_reads_nothing_from_a_same_named_user_module(
    tmp_path: Path, nature, callback_storage, bound_scope, specifics
):
    """Callbacks, specification-expression calls, and generics all follow the ``use`` nature."""
    consumer = f"""\
module consumer
  use, {nature} :: ieee_arithmetic, only: ieee_cb, ieee_scale, ieee_size
  implicit none
  interface ieee_scale
    module procedure scale_int
  end interface ieee_scale
contains
  subroutine scale_int(i)
    integer, intent(inout) :: i
  end subroutine scale_int
  subroutine apply(cb, n, values)
    procedure(ieee_cb) :: cb
    integer, intent(in) :: n
    real, intent(inout) :: values(ieee_size(n))
  end subroutine apply
end module consumer
"""
    module = _modules(tmp_path, USER_IEEE_ARITHMETIC, consumer)["consumer"]
    callback, _count, values = next(function for function in module.functions if function.name == "apply").arguments
    (bound_call,) = values.semantic_type.storage.array.expression_callables[0]

    assert callback.semantic_type.storage.kind == callback_storage
    assert (bound_call.name, bound_call.native_scope) == ("ieee_size", bound_scope)
    assert [procedure.name for procedure in module.overload_sets[0].procedures] == specifics


@pytest.mark.parametrize(
    ("nature", "processor", "wrapped"),
    [
        pytest.param("intrinsic", True, False, id="processor-type"),
        pytest.param("non_intrinsic", False, True, id="user-type"),
    ],
)
def test_a_wildcard_use_resolves_a_derived_type_by_its_nature(tmp_path: Path, nature, processor, wrapped):
    """A type reached through ``use, intrinsic`` is the processor's even beside a same-named user module."""
    user = "module ieee_arithmetic\n  type :: ieee_class_type\n    integer :: v\n  end type ieee_class_type\nend module ieee_arithmetic\n"
    consumer = (
        f"module consumer\n  use, {nature} :: ieee_arithmetic\ncontains\n  subroutine inspect(value)\n"
        "    type(ieee_class_type), intent(in) :: value\n  end subroutine inspect\nend module consumer\n"
    )
    argument = _modules(tmp_path, user, consumer)["consumer"].functions[0].arguments[0]
    reference = argument.semantic_type.metadata["external_type_ref"]

    assert reference["origin_module"] == "ieee_arithmetic"
    assert (bool(reference.get("processor")), reference["wrapped"]) == (processor, wrapped)
