"""Pinned native-build preparation for the TA-Lib validation harness."""

import pytest

from ..native_build import _reference_runner_source


def test_abstract_requests_preserve_binary64_inputs_across_json():
    source = 'pos += snprintf(buf + pos, buf_size - pos, "%.15g", data[i]);'
    value = 0.12345678901234566

    prepared = _reference_runner_source(source)

    assert prepared == 'pos += snprintf(buf + pos, buf_size - pos, "%.17g", data[i]);'
    assert _reference_runner_source(prepared) == prepared
    assert float(format(value, ".15g")) != value
    assert float(format(value, ".17g")) == value


def test_abstract_protocol_adjustment_rejects_unreviewed_upstream_source():
    with pytest.raises(RuntimeError, match="no longer matches"):
        _reference_runner_source("unrecognized serializer")
