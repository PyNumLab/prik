"""Rank-zero callback storage: writable scalar dummies reach native memory."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_generated_pyi_and_import,
    _build_inline_pyi_contract_module,
    _build_source_and_import,
)

pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

SOURCE = (NATIVE_FIXTURES / "fcallback_scalar_storage_f90.f90").read_text(encoding="utf-8")

CONTRACT = """
from prik.contracts import Addr, Arg, Float64, In, InOut, Out, Return, Returns, native_call, prototype

@prototype
def directions_callback(
    read_value: In(Float64[()]),
    update_value: InOut(Float64[()]),
    write_value: Out(Float64[()])
) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Return('write_value', 1)])
def apply_directions(
    callback: directions_callback,
    read_value: Float64,
    update_value: Float64
) -> tuple[Returns["update_value", Float64], Float64]: ...
"""


def test_rank_zero_callback_storage_writes_through_to_the_native_caller(tmp_path: Path):
    """A rank-zero storage dummy exposes native memory with direction-correct access.

    The default `Addr(T)` spelling hands Python an independent value, so a
    contract that needs an `out` or `inout` callback dummy to reach the native
    caller asks for storage instead.
    """
    module, _result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="fcallback_scalar_storage_f90",
        source_text=SOURCE,
        contract_text=CONTRACT,
    )
    observed = {}

    def callback(read_value, update_value, write_value):
        observed["read_writeable"] = read_value.flags.writeable
        observed["update_writeable"] = update_value.flags.writeable
        observed["write_writeable"] = write_value.flags.writeable
        observed["read"] = float(read_value)
        observed["update_in"] = float(update_value)
        update_value[...] = float(update_value) * 10.0
        write_value[...] = float(read_value) + float(update_value)

    updated, written = module.apply_directions(callback, np.float64(3.0), np.float64(4.0))

    assert observed == {
        "read_writeable": False,
        "update_writeable": True,
        "write_writeable": True,
        "read": 3.0,
        "update_in": 4.0,
    }
    assert updated == np.float64(40.0)
    assert written == np.float64(43.0)


SOURCE_DEFAULT = NATIVE_FIXTURES / "fcallback_default_storage_f90.f90"


def test_out_scalar_callback_writes_back_without_editing_the_contract(tmp_path: Path):
    """Wrapping Fortran source directly produces a callback that can answer.

    The generated default must be the spelling that works: an `intent(out)`
    scalar reaches Python as writable storage, so the value the callable
    computes reaches the native caller with no contract edit.
    """
    module = _build_source_and_import(
        SOURCE_DEFAULT,
        tmp_path / "build",
        {
            "bind_c_fcallback_default_storage_f90_wrapper.f90",
            "fcallback_default_storage_f90_wrapper.c",
            "fcallback_default_storage_f90_wrapper.h",
        },
    )

    def objective(x):
        return float(np.sum(x * x))

    def objective_prik(x, f):
        f[...] = objective(x)

    assert module.evaluate(objective_prik, np.array([1.0, 2.0, 3.0])) == np.float64(14.0)


def test_callback_docstring_states_the_callable_signature_and_write_through(tmp_path: Path):
    """The docstring is the only callback description in the source-only workflow.

    Guessing a callback signature wrong is fatal at the callback boundary, so
    `help()` must state the arity, direction, and how an output is delivered.
    """
    module = _build_source_and_import(
        SOURCE_DEFAULT,
        tmp_path / "build",
        {
            "bind_c_fcallback_default_storage_f90_wrapper.f90",
            "fcallback_default_storage_f90_wrapper.c",
            "fcallback_default_storage_f90_wrapper.h",
        },
    )
    documentation = module.evaluate.__doc__

    assert "Called as: calfun(x, f) -> None" in documentation
    assert "x : ndarray[float64], rank 1, shape (::), intent(in)" in documentation
    assert "f : ndarray[float64], intent(out); assign through it (f[...] = value)" in documentation
    assert "An exception or an invalid return value terminates the process." in documentation


SOURCE_UNDECLARED = NATIVE_FIXTURES / "fcallback_undeclared_intent_f90.f90"


def _undeclared_intent_module(tmp_path: Path):
    return _build_source_and_import(
        SOURCE_UNDECLARED,
        tmp_path / "build",
        {
            "bind_c_fcallback_undeclared_intent_f90_wrapper.f90",
            "fcallback_undeclared_intent_f90_wrapper.c",
            "fcallback_undeclared_intent_f90_wrapper.h",
        },
    )


def test_callback_scalar_without_declared_intent_is_read_and_written(tmp_path: Path):
    """An undeclared ``intent`` is conservatively both read and written.

    Fortran permits the callee to modify such a dummy, so the callable must
    observe the incoming value and see its own write reach the native caller.
    """
    module = _undeclared_intent_module(tmp_path)
    observed = []

    def tweak(value):
        observed.append(float(value))
        assert value.flags.writeable
        value[...] = float(value) * 3.0

    assert module.drive(tweak, np.float64(7.0)) == np.float64(21.0)
    assert observed == [7.0]


def test_undeclared_intent_survives_the_generated_contract_round_trip(tmp_path: Path):
    """The absent ``intent`` must survive source, contract, codegen and runtime.

    Building through PRIK's own generated contract proves the bare
    ``Float64[()]`` spelling carries the conservative read/write transfer all
    the way to the trampoline, rather than only appearing in the contract text.
    """
    workdir = tmp_path / "round_trip"
    module = _build_generated_pyi_and_import(SOURCE_UNDECLARED, workdir)

    contract = (workdir / "contracts" / SOURCE_UNDECLARED.stem / f"{SOURCE_UNDECLARED.stem}.pyi").read_text(
        encoding="utf-8"
    )
    assert "value: Float64[()]" in contract
    assert "In(" not in contract and "Out(" not in contract and "InOut(" not in contract

    bridge = next((workdir / "pyi_build").glob("bind_c_*_wrapper.f90")).read_text(encoding="utf-8")
    assert "real(c_double) :: value" in bridge
    assert not any(f"intent({direction}) :: value" in bridge for direction in ("in", "out", "inout"))
    assert "value = value_callback_storage" in bridge

    def tweak(value):
        value[...] = float(value) * 3.0

    assert module.drive(tweak, np.float64(7.0)) == np.float64(21.0)


def test_assume_intent_in_scalars_makes_an_undeclared_callback_scalar_input_only(tmp_path: Path):
    """The flag narrows the default without declaring a direction.

    The contract still carries no direction wrapper, because the source still
    declares none; only the projection and the copy direction change.
    """
    module = _build_source_and_import(
        SOURCE_UNDECLARED,
        tmp_path / "build",
        {
            "bind_c_fcallback_undeclared_intent_f90_wrapper.f90",
            "fcallback_undeclared_intent_f90_wrapper.c",
            "fcallback_undeclared_intent_f90_wrapper.h",
        },
        assume_intent_in_scalars=True,
    )
    contract = (tmp_path / "build" / "contracts" / "fcallback_undeclared_intent_f90.pyi").read_text(encoding="utf-8")
    assert "value: Addr(Float64)" in contract
    assert "In(" not in contract and "Out(" not in contract and "InOut(" not in contract

    bridge = (tmp_path / "build" / "bind_c_fcallback_undeclared_intent_f90_wrapper.f90").read_text(encoding="utf-8")
    assert "real(c_double) :: value" in bridge
    assert not any(f"intent({direction}) :: value" in bridge for direction in ("in", "out", "inout"))
    # Input-only: nothing is copied back out of the call-local storage.
    assert "value = value_callback_storage" not in bridge

    observed = []

    def tweak(value):
        observed.append(float(value))

    assert module.drive(tweak, np.float64(7.0)) == np.float64(7.0)
    assert observed == [7.0]
