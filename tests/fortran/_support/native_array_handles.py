"""Shared native-array handle test doubles for Fortran feature tests."""

import numpy as np


from prik.runtime.handles import (
    _NativeArrayHandoff,
)


class _ArrayState:
    def __init__(self, *, shape=None, value=None):
        self.shape = shape
        self.value = value


def _handoff(address=1):
    return _NativeArrayHandoff(address)


def _required_handoff_ops():
    return {
        "array_actual": lambda _handle: _handoff(101),
        "descriptor": lambda _handle: _handoff(102),
    }


def _common_ops(state: _ArrayState):
    return {
        **_required_handoff_ops(),
        "shape": lambda _handle: state.shape,
        "to_numpy": lambda _handle: state.value if state.shape is not None else None,
    }


def _pointer_descriptor_for_array(value: np.ndarray):
    return {
        "base_addr": int(value.ctypes.data),
        "elem_len": int(value.dtype.itemsize),
        "rank": value.ndim,
        "dim": [
            {
                "lower_bound": 1,
                "extent": int(extent),
                "sm": int(stride),
            }
            for extent, stride in zip(value.shape, value.strides, strict=True)
        ],
    }


class _DescriptorFieldRecord:
    def __init__(self, **fields):
        self.__dict__.update(fields)


def _pointer_descriptor_record_for_array(value: np.ndarray):
    descriptor = _pointer_descriptor_for_array(value)
    return _DescriptorFieldRecord(
        base_addr=descriptor["base_addr"],
        elem_len=descriptor["elem_len"],
        rank=descriptor["rank"],
        dim=[_DescriptorFieldRecord(**dimension) for dimension in descriptor["dim"]],
    )
