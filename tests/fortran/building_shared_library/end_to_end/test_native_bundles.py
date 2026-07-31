"""Native artifact topology evidence for semantic `.pyi` wrapper builds."""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from x2py import build_pyi_extension
from tests.fortran.building_shared_library.end_to_end.test_multi_source_builds import (
    _assert_combined_runtime,
    _compile_native_objects,
    _generate_combined_contract,
    _import_extension,
    _write_combined_sources,
)


CONTRACT_IMPORT = "from x2py.contracts import Addr, Arg, Int32, external, native_call\n\n"
NATIVE_CALL_IMPORT = "from x2py.contracts import Addr, Arg, Int32, native_call\n\n"
pytestmark = pytest.mark.fortran_end_to_end


def _compiler() -> str:
    compiler = shutil.which("gfortran")
    if compiler is None:
        pytest.skip("gfortran is required for native bundle tests")
    return compiler


def _archiver() -> str:
    archiver = shutil.which("ar")
    if archiver is None:
        pytest.skip("ar is required for static archive tests")
    return archiver


def _write_source(directory: Path, name: str, text: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def _compile_source(
    path: Path,
    output_dir: Path,
    *,
    module_dir: Path | None = None,
    include_dirs: tuple[Path, ...] = (),
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    object_path = output_dir / f"{path.stem}.o"
    command = [_compiler(), "-fPIC", "-c", str(path), "-o", str(object_path)]
    for include_dir in include_dirs:
        command.extend(["-I", str(include_dir)])
    if module_dir is not None:
        module_dir.mkdir(parents=True, exist_ok=True)
        command.extend(["-J", str(module_dir), "-I", str(module_dir)])
    subprocess.run(command, capture_output=True, text=True, check=True)
    return object_path


def _archive(path: Path, objects: tuple[Path, ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([_archiver(), "rcs", str(path), *(str(obj) for obj in objects)], check=True)
    return path


def _shared_library(
    path: Path,
    objects: tuple[Path, ...],
    *,
    library_dirs: tuple[Path, ...] = (),
    libraries: tuple[str, ...] = (),
    rpath_dirs: tuple[Path, ...] = (),
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    command = [_compiler(), "-shared", "-o", str(path), *(str(obj) for obj in objects)]
    for directory in library_dirs:
        command.extend(["-L", str(directory)])
    for directory in rpath_dirs:
        command.append(f"-Wl,-rpath,{directory}")
    for library in libraries:
        command.append(library if library.startswith("-l") else f"-l{library}")
    subprocess.run(command, capture_output=True, text=True, check=True)
    return path


def _write_contract_package(package: Path, *, entry: str, leaves: dict[str, str] | None = None) -> Path:
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.pyi").write_text(entry, encoding="utf-8")
    for name, text in (leaves or {}).items():
        (package / f"{name}.pyi").write_text(text, encoding="utf-8")
    return package / "__init__.pyi"


def _import_from_build(result):
    sys.modules.pop(result.module_name, None)
    sys.path.insert(0, str(result.output_dir))
    try:
        return importlib.import_module(result.module_name)
    finally:
        sys.path.remove(str(result.output_dir))


def _simple_external_contract(name: str) -> str:
    return f"{CONTRACT_IMPORT}{_simple_external_declaration(name)}"


def _simple_external_declaration(name: str) -> str:
    return f"@external\n@native_call([Addr(Arg(0))])\ndef {name}(value: Int32) -> Int32: ...\n"


def _simple_external_source(name: str, expression: str) -> str:
    return f"""\
integer function {name}(value) result(out)
  integer, intent(in) :: value
  out = {expression}
end function {name}
"""


@pytest.mark.skipif(sys.platform == "win32", reason="shared-library loader behavior differs on Windows")
@pytest.mark.parametrize("artifact_kind", ["archive", "shared_library"])
def test_imported_contracts_resolve_from_one_archive_or_shared_library(
    tmp_path: Path,
    artifact_kind: str,
):
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    sources = _write_combined_sources(source_dir)
    entry = _generate_combined_contract(sources, tmp_path / "contracts")
    native_objects = _compile_native_objects(sources, tmp_path / "native")
    artifact = (
        _archive(tmp_path / "native" / "libcombined.a", native_objects)
        if artifact_kind == "archive"
        else _shared_library(tmp_path / "native" / "libcombined.so", native_objects)
    )

    result = build_pyi_extension(
        entry,
        native_objects=[artifact],
        native_include_dirs=[native_objects[0].parent],
        output_name="combined_from_single_artifact",
        output_dir=tmp_path / "build",
    )
    module = _import_extension(result.module_name, result.output_dir)
    native_plan = result.native_build_plan.to_dict()

    assert native_plan["prebuilt_artifacts"] == [{"kind": artifact_kind, "path": str(artifact)}]
    assert native_plan["link_items"] == [{"kind": artifact_kind, "path": str(artifact)}]
    _assert_combined_runtime(module)


@pytest.mark.skipif(sys.platform == "win32", reason="shared-library loader behavior differs on Windows")
def test_mixed_module_external_bundle_resolves_all_native_input_kinds(tmp_path: Path):
    sources = tmp_path / "sources"
    native = tmp_path / "native"
    libs = tmp_path / "libs"
    module_source = _write_source(
        sources,
        "artifact_mod.f90",
        """\
module artifact_mod
contains
integer function mod_value(value) result(out)
  integer, intent(in) :: value
  out = value + 10
end function mod_value
end module artifact_mod
""",
    )
    object_source = _write_source(sources, "ext_object.f90", _simple_external_source("ext_object", "value + 1"))
    archive_source = _write_source(sources, "ext_archive.f90", _simple_external_source("ext_archive", "value + 2"))
    shared_source = _write_source(sources, "ext_shared.f90", _simple_external_source("ext_shared", "value + 3"))
    named_source = _write_source(sources, "ext_named.f90", _simple_external_source("ext_named", "value + 4"))

    module_object = _compile_source(module_source, native / "objects", module_dir=native / "mods")
    object_artifact = _compile_source(object_source, native / "objects")
    archive = _archive(native / "libarchive_inputs.a", (_compile_source(archive_source, native / "archives"),))
    shared = _shared_library(
        native / "libdirect_input.so",
        (_compile_source(shared_source, native / "shared"),),
    )
    named = _shared_library(
        libs / "libnamed_bundle.so",
        (_compile_source(named_source, native / "named"),),
    )
    entry = _write_contract_package(
        tmp_path / "contracts" / "mixed_native_bundle",
        entry=(
            "from x2py.contracts import Addr, Arg, Int32, external, native_call\n"
            "from . import artifact_mod\n\n"
            f"{_simple_external_declaration('ext_object')}\n"
            f"{_simple_external_declaration('ext_archive')}\n"
            f"{_simple_external_declaration('ext_shared')}\n"
            f"{_simple_external_declaration('ext_named')}"
        ),
        leaves={
            "artifact_mod": (
                f"{NATIVE_CALL_IMPORT}@native_call([Addr(Arg(0))])\ndef mod_value(\n    value: Int32\n) -> Int32: ...\n"
            ),
        },
    )

    result = build_pyi_extension(
        entry,
        native_objects=[module_object, object_artifact, archive, shared],
        native_libraries=["named_bundle"],
        native_library_dirs=[libs],
        native_include_dirs=[native / "mods"],
        output_name="mixed_native_bundle",
        output_dir=tmp_path / "build",
    )
    module = _import_from_build(result)
    native_plan = result.native_build_plan.to_dict()

    assert module.artifact_mod.mod_value(np.int32(5)) == np.int32(15)
    assert module.ext_object(np.int32(5)) == np.int32(6)
    assert module.ext_archive(np.int32(5)) == np.int32(7)
    assert module.ext_shared(np.int32(5)) == np.int32(8)
    assert module.ext_named(np.int32(5)) == np.int32(9)
    assert native_plan["link_items"] == [
        {"kind": "object", "path": str(module_object)},
        {"kind": "object", "path": str(object_artifact)},
        {"kind": "archive", "path": str(archive)},
        {"kind": "shared_library", "path": str(shared)},
        {"kind": "named_library", "name": "named_bundle"},
    ]
    assert native_plan["module_dirs"] == [str(native / "mods")]
    assert str(libs) in native_plan["library_dirs"]
    assert str(shared.parent) in native_plan["library_dirs"]
    assert native_plan["compilation_units"] == []
    assert named.is_file()


def test_static_archive_dependency_order_resolves_transitive_library(tmp_path: Path):
    sources = tmp_path / "sources"
    native = tmp_path / "native"
    entry_source = _write_source(
        sources,
        "ordered_entry.f90",
        """\
integer function ordered_entry(value) result(out)
  integer, intent(in) :: value
  integer, external :: ordered_helper
  out = ordered_helper(value) + 1
end function ordered_entry
""",
    )
    helper_source = _write_source(
        sources,
        "ordered_helper.f90",
        _simple_external_source("ordered_helper", "value + 20"),
    )
    entry_archive = _archive(native / "libordered_entry.a", (_compile_source(entry_source, native / "entry"),))
    helper_archive = _archive(native / "libordered_helper.a", (_compile_source(helper_source, native / "helper"),))
    entry = _write_contract_package(
        tmp_path / "contracts" / "ordered_native_bundle",
        entry=_simple_external_contract("ordered_entry"),
    )

    result = build_pyi_extension(
        entry,
        native_link_items=[
            {"kind": "archive", "path": entry_archive},
            {"kind": "archive", "path": helper_archive},
        ],
        output_name="ordered_native_bundle",
        output_dir=tmp_path / "build",
    )
    module = _import_from_build(result)

    assert result.native_build_plan.to_dict()["link_items"] == [
        {"kind": "archive", "path": str(entry_archive)},
        {"kind": "archive", "path": str(helper_archive)},
    ]
    assert module.ordered_entry(np.int32(1)) == np.int32(22)


@pytest.mark.skipif(sys.platform != "linux", reason="GNU linker archive groups are Linux-specific")
def test_static_archive_groups_resolve_cyclic_archive_dependencies(tmp_path: Path):
    sources = tmp_path / "sources"
    native = tmp_path / "native"
    cycle_entry = _write_source(
        sources,
        "cycle_entry.f90",
        """\
integer function cycle_entry(value) result(out)
  integer, intent(in) :: value
  integer, external :: cycle_b
  out = cycle_b(value) + 1
end function cycle_entry
""",
    )
    cycle_helper = _write_source(
        sources,
        "cycle_a_helper.f90",
        _simple_external_source("cycle_a_helper", "value + 10"),
    )
    cycle_b = _write_source(
        sources,
        "cycle_b.f90",
        """\
integer function cycle_b(value) result(out)
  integer, intent(in) :: value
  integer, external :: cycle_a_helper
  out = cycle_a_helper(value) + 2
end function cycle_b
""",
    )
    archive_a = _archive(
        native / "libcycle_a.a",
        (
            _compile_source(cycle_entry, native / "cycle_a"),
            _compile_source(cycle_helper, native / "cycle_a"),
        ),
    )
    archive_b = _archive(native / "libcycle_b.a", (_compile_source(cycle_b, native / "cycle_b"),))
    entry = _write_contract_package(
        tmp_path / "contracts" / "cyclic_archive_bundle",
        entry=_simple_external_contract("cycle_entry"),
    )

    result = build_pyi_extension(
        entry,
        native_link_items=[
            {"kind": "linker_argument", "argument": "-Wl,--start-group"},
            {"kind": "archive", "path": archive_a},
            {"kind": "archive", "path": archive_b},
            {"kind": "linker_argument", "argument": "-Wl,--end-group"},
        ],
        output_name="cyclic_archive_bundle",
        output_dir=tmp_path / "build",
    )
    module = _import_from_build(result)

    assert module.cycle_entry(np.int32(5)) == np.int32(18)


@pytest.mark.skipif(sys.platform == "win32", reason="shared-library loader behavior differs on Windows")
def test_required_transitive_named_library_resolves_runtime_symbol(tmp_path: Path):
    sources = tmp_path / "sources"
    native = tmp_path / "native"
    libs = tmp_path / "libs"
    entry_source = _write_source(
        sources,
        "transitive_entry.f90",
        """\
integer function transitive_entry(value) result(out)
  integer, intent(in) :: value
  integer, external :: transitive_helper
  out = transitive_helper(value) + 1
end function transitive_entry
""",
    )
    helper_source = _write_source(
        sources,
        "transitive_helper.f90",
        _simple_external_source("transitive_helper", "value + 30"),
    )
    entry_object = _compile_source(entry_source, native / "objects")
    _shared_library(
        libs / "libtransitive_bundle.so",
        (_compile_source(helper_source, native / "helper"),),
    )
    entry = _write_contract_package(
        tmp_path / "contracts" / "transitive_native_bundle",
        entry=_simple_external_contract("transitive_entry"),
    )

    result = build_pyi_extension(
        entry,
        native_objects=[entry_object],
        native_libraries=["transitive_bundle"],
        native_library_dirs=[libs],
        output_name="transitive_native_bundle",
        output_dir=tmp_path / "build",
    )
    module = _import_from_build(result)

    assert result.native_build_plan.to_dict()["link_items"] == [
        {"kind": "object", "path": str(entry_object)},
        {"kind": "named_library", "name": "transitive_bundle"},
    ]
    assert module.transitive_entry(np.int32(1)) == np.int32(32)


def test_missing_symbol_reports_native_link_or_loader_error(tmp_path: Path):
    entry = _write_contract_package(
        tmp_path / "contracts" / "missing_symbol",
        entry=_simple_external_contract("missing_symbol"),
    )
    native_object = _compile_source(
        _write_source(tmp_path / "sources", "unrelated.f90", _simple_external_source("unrelated", "value")),
        tmp_path / "native",
    )
    try:
        result = build_pyi_extension(
            entry,
            native_objects=[native_object],
            output_name="missing_symbol",
            output_dir=tmp_path / "build",
        )
    except RuntimeError as exc:
        assert "missing_symbol" in str(exc)
        return

    with pytest.raises(ImportError, match="missing_symbol"):
        _import_from_build(result)
    assert result.native_build_plan.to_dict()["compilation_units"] == []


def test_duplicate_native_definitions_report_linker_error(tmp_path: Path):
    sources = tmp_path / "sources"
    first = _compile_source(
        _write_source(sources, "duplicate_first.f90", _simple_external_source("duplicate_entry", "value + 1")),
        tmp_path / "native" / "first",
    )
    second = _compile_source(
        _write_source(sources, "duplicate_second.f90", _simple_external_source("duplicate_entry", "value + 2")),
        tmp_path / "native" / "second",
    )
    entry = _write_contract_package(
        tmp_path / "contracts" / "duplicate_symbol",
        entry=_simple_external_contract("duplicate_entry"),
    )

    with pytest.raises(RuntimeError, match=r"multiple definition|duplicate"):
        build_pyi_extension(
            entry,
            native_objects=[first, second],
            output_name="duplicate_symbol",
            output_dir=tmp_path / "build",
        )


def test_incompatible_native_artifact_reports_linker_error(tmp_path: Path):
    invalid_object = tmp_path / "native" / "invalid.o"
    invalid_object.parent.mkdir(parents=True, exist_ok=True)
    invalid_object.write_text("not an object file\n", encoding="utf-8")
    entry = _write_contract_package(
        tmp_path / "contracts" / "invalid_artifact",
        entry=_simple_external_contract("invalid_artifact"),
    )

    with pytest.raises(RuntimeError, match=r"file format|file not recognized|invalid"):
        build_pyi_extension(
            entry,
            native_objects=[invalid_object],
            output_name="invalid_artifact",
            output_dir=tmp_path / "build",
        )


def test_missing_module_directory_reports_compile_error(tmp_path: Path):
    sources = tmp_path / "sources"
    object_dir = tmp_path / "native" / "objects"
    module_dir = tmp_path / "native" / "mods"
    module_object = _compile_source(
        _write_source(
            sources,
            "missing_mod.f90",
            """\
module missing_mod
contains
integer function value_plus_one(value) result(out)
  integer, intent(in) :: value
  out = value + 1
end function value_plus_one
end module missing_mod
""",
        ),
        object_dir,
        module_dir=module_dir,
    )
    entry = _write_contract_package(
        tmp_path / "contracts" / "missing_mod",
        entry="from . import missing_mod\n",
        leaves={
            "missing_mod": (
                f"{NATIVE_CALL_IMPORT}@native_call([Addr(Arg(0))])\n"
                "def value_plus_one(\n    value: Int32\n) -> Int32: ...\n"
            )
        },
    )

    with pytest.raises(RuntimeError, match=r"missing_mod.mod|Cannot open module file"):
        build_pyi_extension(
            entry,
            native_objects=[module_object],
            output_name="missing_mod",
            output_dir=tmp_path / "build",
        )


@pytest.mark.skipif(sys.platform == "win32", reason="shared-library loader behavior differs on Windows")
def test_unavailable_dependent_shared_library_reports_loader_error(tmp_path: Path):
    sources = tmp_path / "sources"
    native = tmp_path / "native"
    deps = tmp_path / "deps"
    dependent_source = _write_source(
        sources,
        "unavailable_entry.f90",
        """\
integer function unavailable_entry(value) result(out)
  integer, intent(in) :: value
  integer, external :: unavailable_helper
  out = unavailable_helper(value) + 1
end function unavailable_entry
""",
    )
    helper_source = _write_source(
        sources,
        "unavailable_helper.f90",
        _simple_external_source("unavailable_helper", "value + 40"),
    )
    helper_library = _shared_library(
        deps / "libmissing_dependency.so",
        (_compile_source(helper_source, native / "helper"),),
    )
    dependent_library = _shared_library(
        native / "libunavailable_bundle.so",
        (_compile_source(dependent_source, native / "dependent"),),
        library_dirs=(deps,),
        libraries=("missing_dependency",),
        rpath_dirs=(deps,),
    )
    entry = _write_contract_package(
        tmp_path / "contracts" / "unavailable_dep",
        entry=_simple_external_contract("unavailable_entry"),
    )

    result = build_pyi_extension(
        entry,
        native_objects=[dependent_library],
        output_name="unavailable_dep",
        output_dir=tmp_path / "build",
    )
    helper_library.unlink()

    with pytest.raises(ImportError, match=r"missing_dependency|cannot open shared object file"):
        _import_from_build(result)
    assert result.native_build_plan.to_dict()["link_items"] == [
        {"kind": "shared_library", "path": str(dependent_library)}
    ]
