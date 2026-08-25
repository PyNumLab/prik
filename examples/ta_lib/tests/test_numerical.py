"""Successful array calculations across the maintained TA-Lib surface."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import numpy as np
import pytest

from ..api_inventory import INDICATOR_FUNCTIONS


pytestmark = pytest.mark.real_library


def _protocol_process(executable: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(  # nosec B603 - locally built or checked-in protocol executable
        [str(executable)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _protocol_call(process: subprocess.Popen[str], request: dict[str, object]) -> dict[str, object]:
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(f"{json.dumps(request, separators=(',', ':'))}\n")
    process.stdin.flush()
    return json.loads(process.stdout.readline())


def _close_protocol(process: subprocess.Popen[str]) -> None:
    assert process.stdin is not None
    process.stdin.close()
    assert process.wait(timeout=30) == 0


def _compare_mavp_entrypoints(runner: Path) -> None:
    """Cover the one integer-input family TA-Lib's generic runner skips."""
    prices = np.linspace(10.0, 30.0, 64).tolist()
    periods = np.resize(np.arange(2.0, 7.0), len(prices)).tolist()
    params = {
        "startIdx": 0,
        "endIdx": len(prices) - 1,
        "inReal0": prices,
        "inReal1": periods,
        "optInMinPeriod": 2,
        "optInMaxPeriod": 6,
        "optInMAType": 0,
    }
    wrapper = _protocol_process(runner.with_name("ta_codegen_serve_c"))
    reference = _protocol_process(Path(os.environ["PRIK_TALIB_REFERENCE_SERVER"]))
    try:
        for use_float in (False, True):
            request_params = {**params, **({"use_float": 1} if use_float else {})}
            request = {"method": "TA_MAVP", "params": request_params}
            actual = _protocol_call(wrapper, request)
            expected = _protocol_call(reference, request)

            assert (actual["retCode"], actual["outBegIdx"], actual["outNBElement"]) == (
                expected["retCode"],
                expected["outBegIdx"],
                expected["outNBElement"],
            )
            np.testing.assert_allclose(actual["outReal"], expected["outReal"], rtol=1e-5, atol=1e-6)
    finally:
        _close_protocol(wrapper)
        _close_protocol(reference)


def test_every_indicator_matches_ta_lib_reference_results():
    """TA-Lib's generic runner compares every double and float entrypoint."""
    runner = Path(os.environ["PRIK_TALIB_REGTEST"])
    coverage = Path(os.environ["PRIK_TALIB_COVERAGE"])
    coverage.unlink(missing_ok=True)
    completed = subprocess.run(  # nosec B603 - locally built pinned runner
        [str(runner), "--codegen-only", "--language=c", "--no-unguarded"],
        cwd=runner.parent,
        check=False,
        capture_output=True,
        text=True,
        timeout=900,
    )

    assert completed.returncode == 0, f"{completed.stdout}\n{completed.stderr}"
    assert "All tests succeeded" in completed.stdout
    _compare_mavp_entrypoints(runner)
    assert set(coverage.read_text(encoding="utf-8").splitlines()) == set(INDICATOR_FUNCTIONS)


def test_double_and_float_input_moving_averages(talib):
    prices = np.arange(1.0, 11.0, dtype=np.float64)
    expected = np.arange(3.0, 9.0, dtype=np.float64)

    output = np.empty_like(prices)
    status, begin, count = talib.TA_SMA(
        np.intc(0),
        np.intc(prices.size - 1),
        prices,
        np.intc(5),
        output,
    )
    assert (int(status), int(begin), int(count)) == (0, 4, 6)
    np.testing.assert_allclose(output[:count], expected)

    float_output = np.empty_like(prices)
    status, begin, count = talib.TA_S_SMA(
        np.intc(0),
        np.intc(prices.size - 1),
        prices.astype(np.float32),
        np.intc(5),
        float_output,
    )
    assert (int(status), int(begin), int(count)) == (0, 4, 6)
    np.testing.assert_allclose(float_output[:count], expected)


def test_three_output_bollinger_bands(talib):
    prices = np.arange(1.0, 11.0, dtype=np.float64)
    upper = np.empty_like(prices)
    middle = np.empty_like(prices)
    lower = np.empty_like(prices)

    status, begin, count = talib.TA_BBANDS(
        np.intc(0),
        np.intc(prices.size - 1),
        prices,
        np.intc(5),
        np.float64(2.0),
        np.float64(2.0),
        np.intc(0),
        upper,
        middle,
        lower,
    )

    assert (int(status), int(begin), int(count)) == (0, 4, 6)
    np.testing.assert_allclose(middle[:count], np.arange(3.0, 9.0))
    np.testing.assert_allclose(upper[:count] - middle[:count], middle[:count] - lower[:count])
    assert np.all(upper[:count] > middle[:count])


def test_integer_output_arrays_use_target_c_int_storage(talib):
    values = np.arange(1.0, 11.0, dtype=np.float64)
    minimum_indices = np.empty(values.size, dtype=np.intc)
    maximum_indices = np.empty(values.size, dtype=np.intc)

    status, begin, count = talib.TA_MINMAXINDEX(
        np.intc(0),
        np.intc(values.size - 1),
        values,
        np.intc(5),
        minimum_indices,
        maximum_indices,
    )

    assert (int(status), int(begin), int(count)) == (0, 4, 6)
    np.testing.assert_array_equal(minimum_indices[:count], np.arange(0, 6, dtype=np.intc))
    np.testing.assert_array_equal(maximum_indices[:count], np.arange(4, 10, dtype=np.intc))
