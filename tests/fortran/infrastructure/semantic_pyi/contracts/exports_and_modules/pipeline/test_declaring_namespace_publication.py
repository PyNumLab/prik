"""Which namespace may publish a name, by the kind of declaration it names.

A procedure or a derived type reaches Python as one object, so another
namespace can bind it and PRIK re-exports it through an alias. A module
variable likewise permits multiple publications, but all of them refer to the
one variable plan and its live native state. A generic's Python dispatcher is
also one object that a facade can publish.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from prik.pipeline.build import build_pyi_extension

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

GENERIC_SOURCE = (NATIVE_FIXTURES / "generic.f90").read_text(encoding="utf-8")

HOME_CONTRACT = """\
from prik.contracts import Addr, Arg, Float64, Int32, native_call, overload

counter: Int32

@native_call([Addr(Arg(0))])
def area_i(
    v: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def area_r(
    v: Float64
) -> Float64: ...

@native_call([Addr(Arg(0))])
def scale_value(
    v: Int32
) -> Int32: ...

@overload("area_i")
def area(
    v: Int32
) -> Int32: ...

@overload("area_r")
def area(
    v: Float64
) -> Float64: ...

__all__ = {home_exports}
"""


def _package(tmp_path: Path, *, home_exports: list[str], facade: str) -> Path:
    """Write a two-namespace contract package and return its entry contract."""
    (tmp_path / "home.f90").write_text(GENERIC_SOURCE, encoding="utf-8")
    package = tmp_path / "contracts"
    package.mkdir()
    (package / "home.pyi").write_text(HOME_CONTRACT.format(home_exports=home_exports), encoding="utf-8")
    (package / "facade.pyi").write_text(facade, encoding="utf-8")
    (package / "__init__.pyi").write_text(
        'from . import home\nfrom . import facade\n\n__all__ = ["home", "facade"]\n',
        encoding="utf-8",
    )
    return package / "__init__.pyi"


def _plan(entry: Path, tmp_path: Path, name: str):
    """Plan a build from one contract package without compiling it."""
    return build_pyi_extension(
        entry,
        native_fortran_sources=[str(tmp_path / "home.f90")],
        output_dir=tmp_path / "build",
        output_name=name,
        generate_sources=True,
    )


ALL_NAMES = ["counter", "area_i", "area_r", "scale_value", "area"]


@pytest.mark.parametrize("name", ["counter", "area"])
def test_the_declaring_namespace_may_publish_either_kind(name: str, tmp_path: Path):
    """Publishing one where it is declared is what a source build already does."""
    entry = _package(tmp_path, home_exports=ALL_NAMES, facade="__all__ = []\n")

    result = _plan(entry, tmp_path, f"declaring_only_{name}")

    assert result.output_dir.is_dir()


def test_a_facade_may_publish_the_declaring_namespaces_variable(tmp_path: Path):
    """A second publication reads the declaring variable's completed plan."""
    entry = _package(
        tmp_path,
        home_exports=ALL_NAMES,
        facade='from .home import counter\n\n__all__ = ["counter"]\n',
    )

    result = _plan(entry, tmp_path, "both_counter")

    generated = (result.output_dir / "both_counter_wrapper.c").read_text(encoding="utf-8")
    assert generated.count("static PyObject * module_get_counter(void) {") == 1
    assert generated.count("static int module_set_counter(PyObject * value_obj) {") == 1


def test_a_facade_may_be_the_only_publication_of_a_declared_variable(tmp_path: Path):
    """Withholding the declaring name changes publication, not ownership."""
    entry = _package(
        tmp_path,
        home_exports=[item for item in ALL_NAMES if item != "counter"],
        facade='from .home import counter\n\n__all__ = ["counter"]\n',
    )

    result = _plan(entry, tmp_path, "facade_only_counter")

    generated = (result.output_dir / "facade_only_counter_wrapper.c").read_text(encoding="utf-8")
    assert generated.count("static PyObject * module_get_counter(void) {") == 1
    assert generated.count("static int module_set_counter(PyObject * value_obj) {") == 1


@pytest.mark.parametrize("home_exports", [ALL_NAMES, [item for item in ALL_NAMES if item != "area"]])
def test_a_generic_can_be_published_from_a_facade(home_exports: list[str], tmp_path: Path):
    """One generic dispatcher serves its declaring namespace and facade."""
    entry = _package(
        tmp_path,
        home_exports=home_exports,
        facade='from .home import area\n\n__all__ = ["area"]\n',
    )

    result = _plan(entry, tmp_path, "facade_area")

    generated = (result.output_dir / "facade_area_wrapper.c").read_text(encoding="utf-8")
    assert generated.count('"area"') >= 1


def test_a_procedure_still_reaches_python_through_a_facade(tmp_path: Path):
    """A procedure is one object, so a second namespace binds the same one."""
    entry = _package(
        tmp_path,
        home_exports=ALL_NAMES,
        facade='from .home import scale_value\n\n__all__ = ["scale_value"]\n',
    )

    result = _plan(entry, tmp_path, "procedure_facade")

    assert result.output_dir.is_dir()
