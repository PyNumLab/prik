"""Representative parser and code-generation performance benchmarks."""

from __future__ import annotations


import pytest

from prik.semantics.fortran2ir import fortran_file_to_semantic_modules
from prik.pipeline.pyi import emit_module_stubs
from prik.parsers.fortran import parse_fortran_file
from tests.fortran._support.paths import REPO_ROOT

pytestmark = pytest.mark.skip(reason="Benchmarks are parked until benchmark adoption resumes.")


_FORTRAN_MODULE = (
    "module generated\n"
    "contains\n"
    + "".join(
        f"subroutine step_{index}(x)\n  integer, intent(in) :: x\nend subroutine step_{index}\n" for index in range(50)
    )
    + "end module generated\n"
)


def _parse_convert_emit_fortran(source: str) -> dict[str, str]:
    parsed = parse_fortran_file(source, filename="benchmark.f90")
    return emit_module_stubs(fortran_file_to_semantic_modules(parsed))


@pytest.mark.benchmark
def test_parse_convert_emit_representative_fortran_module(benchmark):
    stubs = benchmark(_parse_convert_emit_fortran, _FORTRAN_MODULE)

    assert stubs["generated"].count("def step_") == 50


@pytest.mark.benchmark
def test_parse_real_lapack_dgesv(benchmark):
    source = (REPO_ROOT / "examples" / "fortran" / "lapack" / "native" / "dgesv.f").read_text(
        encoding="utf-8",
    )
    parsed = benchmark(parse_fortran_file, source, filename="lapack/dgesv.f")

    assert [procedure.name for procedure in parsed.procedures] == ["DGESV"]
    assert parsed.diagnostics == []
