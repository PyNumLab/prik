"""Representative C-parser performance benchmark."""

from __future__ import annotations

import pytest

from prik.parsers.c import parse_c_file


pytestmark = pytest.mark.skip(reason="Benchmarks are parked until benchmark adoption resumes.")

_C_HEADER = "".join(f"int fn_{index}(int x_{index}, double y_{index});\n" for index in range(200))


@pytest.mark.benchmark
def test_parse_representative_c_header(benchmark):
    parsed = benchmark(parse_c_file, _C_HEADER, filename="benchmark.h")

    assert len(parsed.functions) == 200
    assert parsed.diagnostics == []
