"""Property-based Fortran parser invariants for generated source subsets."""

from __future__ import annotations


import pytest

pytest.importorskip("hypothesis")

from hypothesis import strategies as st


_FORTRAN_SCALAR_TYPES = st.sampled_from(["integer", "real", "logical"])

_FORTRAN_IDENTIFIER_STEMS = st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True)

_FUZZ_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_()[]{}*,;:#=+-/! \t\n'\"",
    max_size=80,
)


@st.composite
def fortran_subroutines(draw):
    proc_name = f"sub_{draw(st.integers(min_value=0, max_value=9999))}"
    arg_ids = draw(st.lists(st.integers(min_value=0, max_value=99), max_size=5, unique=True))
    arg_names = [f"arg_{value}" for value in arg_ids]
    arg_types = draw(st.lists(_FORTRAN_SCALAR_TYPES, min_size=len(arg_names), max_size=len(arg_names)))

    lines = [f"subroutine {proc_name}({', '.join(arg_names)})"]
    lines.extend(
        f"  {type_spec}, intent(in) :: {arg_name}" for type_spec, arg_name in zip(arg_types, arg_names, strict=True)
    )
    lines.append(f"end subroutine {proc_name}")

    return proc_name, arg_names, "\n".join(lines) + "\n"
