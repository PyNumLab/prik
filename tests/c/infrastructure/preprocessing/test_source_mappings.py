"""Tests split by stable ownership concept from `test_cli.py`."""

from pathlib import Path

import prik.preprocessing.source as preprocessing
from prik.preprocessing import PreprocessingConfig


def test_preprocess_source_preserves_plain_c_source_mapping(monkeypatch, tmp_path: Path):
    c_source = tmp_path / "api.c"
    c_source.write_text("int api(void);\n", encoding="utf-8")

    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type(
            "Done",
            (),
            {"returncode": 0, "stdout": "int api(void);\n", "stderr": ""},
        )(),
    )

    c_result = preprocessing.preprocess_source(
        c_source,
        language="c",
        config=PreprocessingConfig(mode="compiler", compiler=str(tmp_path / "cc")),
    )
    assert c_result.source_mappings == [
        preprocessing.SourceMapping(
            generated_line=1,
            original_path=str(c_source),
            original_line=1,
            include_stack=[str(c_source)],
        )
    ]
