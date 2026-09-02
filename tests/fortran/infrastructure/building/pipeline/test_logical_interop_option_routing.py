"""Every build entrypoint that compiles Fortran must carry the logical-interop choice."""

import pytest

from prik.pipeline import build as pipeline_build


@pytest.fixture
def recorded_compiler_options(monkeypatch):
    """Capture the ``standard_logicals`` each entrypoint hands its compiler."""
    recorded: list[bool | None] = []
    real_new_compiler = pipeline_build._new_compiler

    def _record(*args, **kwargs):
        recorded.append(kwargs.get("standard_logicals"))
        raise _StopBuild

    monkeypatch.setattr(pipeline_build, "_new_compiler", _record)
    assert real_new_compiler is not _record
    return recorded


class _StopBuild(Exception):
    """Raised in place of constructing a compiler, so no build work follows."""


@pytest.mark.parametrize("standard_logicals", [True, False])
def test_fortran_source_build_hands_the_choice_to_its_compiler(
    tmp_path, recorded_compiler_options, standard_logicals: bool
):
    source = tmp_path / "flags.f90"
    source.write_text("module flags\n  logical :: on = .true.\nend module flags\n")

    with pytest.raises(_StopBuild):
        pipeline_build.build_fortran_extension(
            [source], output_dir=tmp_path / "out", standard_logicals=standard_logicals
        )

    assert recorded_compiler_options == [standard_logicals]


@pytest.mark.parametrize("standard_logicals", [True, False])
def test_contract_build_hands_the_choice_to_its_compiler(tmp_path, recorded_compiler_options, standard_logicals: bool):
    """A contract build compiles the native Fortran too, so it must not drop the choice."""
    package = tmp_path / "contract"
    package.mkdir()
    (package / "__init__.pyi").write_text("from . import flags\n")
    (package / "flags.pyi").write_text("from prik.contracts import Bool8\n\non: Bool8\n")
    native = tmp_path / "flags.f90"
    native.write_text("module flags\n  logical :: on = .true.\nend module flags\n")

    with pytest.raises(_StopBuild):
        pipeline_build.build_pyi_extension(
            package / "__init__.pyi",
            output_dir=tmp_path / "out",
            native_fortran_sources=[native],
            standard_logicals=standard_logicals,
        )

    assert recorded_compiler_options == [standard_logicals]


@pytest.mark.parametrize("standard_logicals", [True, False])
def test_c_build_with_fortran_dependencies_hands_the_choice_to_its_compiler(
    tmp_path, recorded_compiler_options, standard_logicals: bool
):
    """A C build that links Fortran compiles it with the same compiler, so the choice applies."""
    source = tmp_path / "api.c"
    source.write_text("int answer(void) { return 1; }\n")
    native = tmp_path / "flags.f90"
    native.write_text("module flags\n  logical :: on = .true.\nend module flags\n")

    with pytest.raises(_StopBuild):
        pipeline_build.build_c_extension(
            source,
            output_dir=tmp_path / "out",
            output_name="c_logical_option",
            native_fortran_sources=[native],
            standard_logicals=standard_logicals,
        )

    assert recorded_compiler_options == [standard_logicals]
