"""Import fixture for the TA-Lib wrapper produced by `build_all.sh`."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(scope="session")
def talib():
    """Initialize and return the already-built PRIK TA-Lib module."""
    module = importlib.import_module("prik_reference_talib")
    assert int(module.TA_Initialize()) == 0
    yield module
    assert int(module.TA_Shutdown()) == 0
