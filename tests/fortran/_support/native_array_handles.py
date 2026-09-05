"""Shared native-array handle test doubles for Fortran feature tests."""

import numpy as np


class _ArrayState:
    def __init__(self, *, shape=None, value=None):
        self.shape = shape
        self.value = value


def _common_ops(state: _ArrayState):
    """Return the operations every generated handle supplies.

    A generated handle answers both of these from its live descriptor, so each
    reports absence itself rather than being asked about it first.
    """
    return {
        "shape": lambda _handle: state.shape,
        "to_numpy": lambda _handle: state.value if state.shape is not None else None,
    }


def _descriptor_facts_for_array(value: np.ndarray, *, lower_bound: int = 1):
    """Return the flat facts a generated pointer reports for one array.

    The layout is the one the generated consumer writes: base address, element
    width, rank, then a lower bound, extent and byte stride per axis.
    """
    return (
        int(value.ctypes.data),
        int(value.dtype.itemsize),
        value.ndim,
        *(
            field
            for extent, stride in zip(value.shape, value.strides, strict=True)
            for field in (lower_bound, int(extent), int(stride))
        ),
    )


def _absent_descriptor_facts(dtype, rank: int):
    """Return the flat facts a generated handle reports for absent storage."""
    itemsize = int(np.dtype(dtype).itemsize)
    return (0, itemsize, rank, *((0, 0, itemsize) * rank))
