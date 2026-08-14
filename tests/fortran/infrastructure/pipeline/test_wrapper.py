"""Internal generated-wrapper handoff contracts."""

from __future__ import annotations

from pathlib import Path

from prik.pipeline.wrapper import GeneratedSource, GeneratedWrapper


def test_generated_wrapper_keeps_compile_and_link_ownership_out_of_the_handoff():
    wrapper = GeneratedWrapper(
        module_name="demo",
        sources=(
            GeneratedSource(Path("bind_c_demo.f90"), "module bind_c_demo\nend module bind_c_demo\n"),
            GeneratedSource(Path("demo.c"), "PyObject *demo;\n"),
            GeneratedSource(Path("demo.h"), "#pragma once\n"),
        ),
        bridge_sources=(Path("bind_c_demo.f90"),),
        binding_sources=(Path("demo.c"),),
        headers=(Path("demo.h"),),
        native_support_keys=("binding_support",),
        required_headers=(),
        extension_init_name="PyInit_demo",
    )

    assert wrapper.compile_sources == (Path("bind_c_demo.f90"), Path("demo.c"))
    assert wrapper.generated_files == (Path("bind_c_demo.f90"), Path("demo.c"), Path("demo.h"))
    assert wrapper.source_paths == wrapper.generated_files
