#!/usr/bin/env python3
"""Expose the PRIK TA-Lib module through TA-Lib's line-oriented test protocol."""

from __future__ import annotations

import ast
import ctypes
from dataclasses import dataclass
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np


_PROXIED_ABSTRACTION_METHODS = frozenset(
    {
        "TA_GetFuncInfo",
        "TA_GetInputParameterInfo",
        "TA_GetOptInputParameterInfo",
        "TA_GetOutputParameterInfo",
        "TA_FunctionDescriptionXML",
        "abstract_call",
        "abstract_get_lookback",
    }
)
_NUMPY_DTYPES = {
    "Float32": np.float32,
    "Float64": np.float64,
    "Int": np.intc,
}
_UNSTABLE_PERIOD_IDS = {
    "TA_ADX": 0,
    "TA_ADXR": 1,
    "TA_ATR": 2,
    "TA_CMO": 3,
    "TA_DX": 4,
    "TA_EMA": 5,
    "TA_HT_DCPERIOD": 6,
    "TA_HT_DCPHASE": 7,
    "TA_HT_PHASOR": 8,
    "TA_HT_SINE": 9,
    "TA_HT_TRENDLINE": 10,
    "TA_HT_TRENDMODE": 11,
    "TA_IMI": 12,
    "TA_KAMA": 13,
    "TA_MAMA": 14,
    "TA_MFI": 15,
    "TA_MINUS_DI": 16,
    "TA_MINUS_DM": 17,
    "TA_NATR": 18,
    "TA_PLUS_DI": 19,
    "TA_PLUS_DM": 20,
    "TA_RSI": 21,
    "TA_STOCHRSI": 22,
    "TA_T3": 23,
}


@dataclass(frozen=True)
class Parameter:
    """One visible native argument from the reviewed semantic contract."""

    name: str
    type_name: str
    array: bool


@dataclass(frozen=True)
class Function:
    """The input and output arrays needed to invoke one wrapped indicator."""

    parameters: tuple[Parameter, ...]

    @property
    def outputs(self) -> tuple[Parameter, ...]:
        return tuple(parameter for parameter in self.parameters if parameter.name.startswith("out"))


def _annotation(annotation: ast.expr | None) -> tuple[str, bool]:
    if isinstance(annotation, ast.Name):
        return annotation.id, False
    if isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
        return annotation.value.id, True
    raise ValueError(f"unsupported TA-Lib contract annotation: {ast.dump(annotation)}")


def load_contract(path: Path) -> dict[str, Function]:
    """Load the checked-in contract as the adapter's only call schema."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name in {"TA_Initialize", "TA_Shutdown"}:
            continue
        parameters = []
        for argument in node.args.args:
            type_name, array = _annotation(argument.annotation)
            if type_name not in _NUMPY_DTYPES:
                raise ValueError(f"unsupported TA-Lib contract type {type_name!r} in {node.name}")
            parameters.append(Parameter(argument.arg, type_name, array))
        functions[node.name] = Function(tuple(parameters))
    return functions


class ReferenceProxy:
    """Forward excluded abstraction-protocol requests to TA-Lib's oracle."""

    def __init__(self, executable: Path) -> None:
        self._process = subprocess.Popen(  # nosec B603 - pinned locally-built executable
            [str(executable)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def call(self, request: str) -> str:
        if self._process.stdin is None or self._process.stdout is None:
            raise RuntimeError("TA-Lib reference proxy has no protocol pipes")
        self._process.stdin.write(f"{request}\n")
        self._process.stdin.flush()
        response = self._process.stdout.readline()
        if not response:
            raise RuntimeError("TA-Lib reference proxy stopped before replying")
        return response.rstrip("\n")

    def close(self) -> None:
        if self._process.stdin is not None:
            self._process.stdin.close()
        self._process.wait(timeout=30)


class NativeSettings:
    """Apply TA-Lib test-runner state without adding settings to the wrapper."""

    def __init__(self, library: Path) -> None:
        self._library = ctypes.CDLL(str(library))
        self._library.TA_SetCompatibility.argtypes = [ctypes.c_int]
        self._library.TA_SetCompatibility.restype = ctypes.c_int
        self._library.TA_SetUnstablePeriod.argtypes = [ctypes.c_int, ctypes.c_uint]
        self._library.TA_SetUnstablePeriod.restype = ctypes.c_int

    def set_compatibility(self, mode: int) -> int:
        return int(self._library.TA_SetCompatibility(mode))

    def apply_unstable_period(self, method: str, params: dict[str, object]) -> None:
        if method not in _UNSTABLE_PERIOD_IDS or "unstablePeriod" not in params:
            return
        status = int(self._library.TA_SetUnstablePeriod(_UNSTABLE_PERIOD_IDS[method], int(params["unstablePeriod"])))
        if status != 0:
            raise RuntimeError(f"TA_SetUnstablePeriod failed with status {status}")


def _argument_value(parameter: Parameter, params: dict[str, object], capacity: int):
    dtype = _NUMPY_DTYPES[parameter.type_name]
    if parameter.name.startswith("out"):
        return np.empty(capacity, dtype=dtype)
    aliases = {"inReal": "inReal0", "inPeriods": "inReal1"}
    value = params.get(parameter.name, params.get(aliases.get(parameter.name, "")))
    if value is None:
        raise ValueError(f"request has no value for {parameter.name}")
    if parameter.array:
        return np.ascontiguousarray(value, dtype=dtype)
    return dtype(value)


def _indicator_response(
    module,
    functions: dict[str, Function],
    settings: NativeSettings,
    request: dict[str, object],
) -> tuple[dict, str]:
    requested_name = str(request["method"])
    params = request.get("params")
    if not isinstance(params, dict):
        raise ValueError(f"{requested_name} request has no parameter object")
    wrapped_name = f"TA_S_{requested_name.removeprefix('TA_')}" if params.get("use_float") else requested_name
    function = functions[wrapped_name]
    settings.apply_unstable_period(requested_name, params)
    capacity = max(1, int(params["endIdx"]) - int(params["startIdx"]) + 1)
    arguments = [_argument_value(parameter, params, capacity) for parameter in function.parameters]

    started = time.perf_counter_ns()
    result = getattr(module, wrapped_name)(*arguments)
    elapsed = max(1, time.perf_counter_ns() - started)
    status, beginning, count = (int(value) for value in result)
    response = {
        "retCode": status,
        "outBegIdx": beginning,
        "outNBElement": count,
        "timing_ns": elapsed,
        "timing_ns_unguarded": 0,
    }
    output_values = {parameter.name: value for parameter, value in zip(function.parameters, arguments, strict=True)}
    for index, output in enumerate(function.outputs):
        family = "outInteger" if output.type_name == "Int" else "outReal"
        field = family if index == 0 else f"{family}{index}"
        response[field] = output_values[output.name][:count].tolist()
    return response, wrapped_name


def _write_coverage(path: Path | None, functions: set[str]) -> None:
    if path is None:
        return
    if path.is_file():
        functions.update(path.read_text(encoding="utf-8").splitlines())
    path.write_text("".join(f"{name}\n" for name in sorted(functions)), encoding="utf-8")


def serve() -> int:
    """Serve requests until TA-Lib's runner closes the protocol pipe."""
    contract = Path(os.environ["PRIK_TALIB_CONTRACT"])
    reference_server = Path(os.environ["PRIK_TALIB_REFERENCE_SERVER"])
    settings = NativeSettings(Path(os.environ["PRIK_TALIB_LIBRARY"]))
    coverage_value = os.environ.get("PRIK_TALIB_COVERAGE")
    coverage_path = Path(coverage_value) if coverage_value else None
    functions = load_contract(contract)
    module = importlib.import_module("prik_reference_talib")
    initialized = int(module.TA_Initialize())
    if initialized != 0:
        raise RuntimeError(f"TA_Initialize failed with status {initialized}")

    proxy = None
    called = set()
    try:
        for line in sys.stdin:
            request_text = line.rstrip("\n")
            try:
                request = json.loads(request_text)
                method = request.get("method")
                if method in _PROXIED_ABSTRACTION_METHODS:
                    if proxy is None:
                        proxy = ReferenceProxy(reference_server)
                    response_text = proxy.call(request_text)
                elif method == "load_data":
                    response_text = json.dumps({"status": "ok"}, separators=(",", ":"))
                elif method == "set_compatibility":
                    params = request.get("params")
                    if not isinstance(params, dict):
                        raise ValueError("set_compatibility request has no parameter object")
                    response_text = json.dumps(
                        {"retCode": settings.set_compatibility(int(params["mode"]))},
                        separators=(",", ":"),
                    )
                else:
                    response, wrapped_name = _indicator_response(module, functions, settings, request)
                    called.add(wrapped_name)
                    response_text = json.dumps(response, separators=(",", ":"), allow_nan=True)
            except Exception as error:  # protocol errors must be reported to the runner
                response_text = json.dumps({"error": str(error)}, separators=(",", ":"))
            print(response_text, flush=True)
    finally:
        if proxy is not None:
            proxy.close()
        _write_coverage(coverage_path, called)
        shutdown = int(module.TA_Shutdown())
        if shutdown != 0:
            raise RuntimeError(f"TA_Shutdown failed with status {shutdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(serve())
