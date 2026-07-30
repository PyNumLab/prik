"""Tests for building already-rendered wrapper-plan artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.compiling.objects import ObjectFile
from x2py.pipeline.build import (
    NativeBuildPlan,
    NativeLinkItem,
    _build_rendered_wrapper_extension,
    _generated_wrapper_plan_artifacts,
)
from x2py.pipeline.wrapper_artifacts import (
    GeneratedSourceFile,
    GeneratedWrapperArtifacts,
    RenderedGeneratedWrapperArtifacts,
)
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.stage_values import FrozenStageRecordError
from x2py.wrapper_codegen import (
    ModulePlan,
    WrapperCodeGenerator,
    WrapperPlanner,
)


class RecordingCompiler:
    """Compiler test double that records compile/link calls and creates files."""

    def __init__(self):
        self.compiled = []
        self.linked = None

    def compile_object(self, object_file, *, verbose=False):
        self.compiled.append((object_file, verbose))
        object_file.object_path.parent.mkdir(parents=True, exist_ok=True)
        object_file.object_path.write_text(f"{object_file.language} object\n", encoding="utf-8")
        if object_file.language == "fortran":
            module_file = object_file.object_path.parent / f"{object_file.source.stem}.mod"
            module_file.write_text("fortran module\n", encoding="utf-8")

    def link_extension(
        self,
        *,
        module_name,
        output_dir,
        language,
        objects,
        link_args=(),
        library_dirs=(),
        libraries=(),
        flags=(),
        tools=("python",),
        verbose=False,
    ):
        shared_library = Path(output_dir) / f"{module_name}.so"
        if verbose:
            print(f">> Create shared library: {shared_library}")
        shared_library.write_text("shared library\n", encoding="utf-8")
        self.linked = (
            module_name,
            Path(output_dir),
            language,
            tuple(objects),
            tuple(link_args),
            tuple(library_dirs),
            tuple(libraries),
            tuple(flags),
            tuple(tools),
            verbose,
        )
        return shared_library


def _module_plan(source: str, *, module_name: str) -> ModulePlan:
    module = parse_pyi_text(source, module_name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _rendered_artifacts(source: str, *, module_name: str) -> RenderedGeneratedWrapperArtifacts:
    return WrapperCodeGenerator().generate(_module_plan(source, module_name=module_name))


def test_real_wrapper_build_path_raises_the_completed_policy_error_directly():
    module = parse_pyi_text(
        'label: String = "ready"\n',
        module_name="labels",
    )

    with pytest.raises(
        ValueError,
        match=r"Semantic variable 'labels\.label'.*module variable initializer requires a write-through native setter",
    ):
        _generated_wrapper_plan_artifacts(module, strict_wrapper_names=False)


def test_build_rendered_wrapper_extension_writes_compiles_runtime_and_links(tmp_path: Path, capsys):
    rendered = _rendered_artifacts(
        """
@bind("SCALE")
@native_call([Addr(Arg(0))])
def scale(x: Float64) -> Float64: ...
""",
        module_name="plan_scalar_build",
    )
    native_dir = tmp_path / "native"
    native_dir.mkdir()
    native_source = native_dir / "scale_native.f90"
    native_source.write_text("native source placeholder\n", encoding="utf-8")
    native_obj = ObjectFile(
        source=native_source,
        object_path=native_dir / "scale_native.o",
        language="fortran",
        include_dirs=(native_dir,),
    )
    native_obj.object_path.write_text("native object\n", encoding="utf-8")
    native_plan = NativeBuildPlan(
        produced_objects=(native_obj.object_path,),
        link_items=(NativeLinkItem("object", native_obj.object_path),),
        module_dirs=(native_dir,),
        library_dirs=(native_dir,),
    )
    compiler = RecordingCompiler()

    result = _build_rendered_wrapper_extension(
        rendered,
        output_dir=tmp_path / "build",
        shared_library_output_dir=tmp_path / "extension",
        sources=(Path("scale_contract.pyi"),),
        native_build_plan=native_plan,
        native_dependencies=(native_obj,),
        native_link_args=("-lm",),
        wrapper_fortran_flags=("-O2",),
        wrapper_c_flags=("-O3",),
        compiler=compiler,
        verbose=True,
    )

    build_dir = tmp_path / "build"
    bridge_source = build_dir / "bind_c_plan_scalar_build_wrapper.f90"
    binding_source = build_dir / "plan_scalar_build_wrapper.c"
    header = build_dir / "plan_scalar_build_wrapper.h"
    native_support_header = build_dir / "binding_support" / "x2py_binding.h"

    assert bridge_source.read_text(encoding="utf-8") == rendered.sources[0].text
    assert binding_source.read_text(encoding="utf-8") == rendered.sources[1].text
    assert header.read_text(encoding="utf-8") == rendered.sources[2].text
    assert native_support_header.exists()
    assert [object_file.language for object_file, _verbose in compiler.compiled] == ["fortran", "c"]

    bridge_obj = compiler.compiled[0][0]
    binding_obj = compiler.compiled[1][0]
    assert native_dir in bridge_obj.include_dirs
    assert binding_obj.tools == frozenset({"python"})
    assert compiler.linked == (
        "plan_scalar_build",
        tmp_path / "extension",
        "fortran",
        (native_obj, bridge_obj, binding_obj),
        ("-lm",),
        (native_dir,),
        (),
        ("-O3",),
        ("python",),
        True,
    )

    assert result.sources == (Path("scale_contract.pyi"),)
    assert result.module_name == "plan_scalar_build"
    assert result.output_dir == build_dir
    assert result.shared_library == tmp_path / "extension" / "plan_scalar_build.so"
    assert result.shared_library.exists()
    assert result.compiled is True
    assert result.build_makefile is None
    assert result.native_build_plan == native_plan
    assert result.generated_sources == (bridge_source, binding_source, header)
    assert bridge_obj.object_path in result.generated_files
    assert binding_obj.object_path in result.generated_files
    assert native_support_header in result.generated_files
    step_lines = [
        line.removeprefix(">> ")
        for line in capsys.readouterr().out.splitlines()
        if line.startswith(">> ") and not line.startswith(">> Timing")
    ]
    assert step_lines == [
        f"Write bridge source: {bridge_source}",
        f"Write binding source: {binding_source}",
        f"Write binding header: {header}",
        f"Write native support: {build_dir / 'binding_support'}",
        f"Compile bridge source: {bridge_source} -> {bridge_obj.object_path}",
        f"Compile binding source: {binding_source} -> {binding_obj.object_path}",
        f"Create shared library: {result.shared_library}",
    ]


def test_build_rendered_wrapper_extension_rejects_unknown_native_support_key(tmp_path: Path):
    rendered = RenderedGeneratedWrapperArtifacts(
        artifacts=GeneratedWrapperArtifacts(
            module_name="bad_runtime",
            binding_sources=(Path("bad_runtime_wrapper.c"),),
            native_support_keys=("unknown_native_support",),
        ),
        sources=(GeneratedSourceFile(Path("bad_runtime_wrapper.c"), "PyObject *unused;\n"),),
        extension_init_name="PyInit_bad_runtime",
    )

    with pytest.raises(ValueError, match="Unsupported wrapper native support key"):
        _build_rendered_wrapper_extension(
            rendered,
            output_dir=tmp_path,
            compiler=RecordingCompiler(),
        )
    with pytest.raises(FrozenStageRecordError):
        rendered.extension_init_name = "PyInit_later"
