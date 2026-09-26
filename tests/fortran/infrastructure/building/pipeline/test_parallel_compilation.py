"""Dependency and concurrency tests for direct extension compilation."""

from __future__ import annotations

from pathlib import Path
import threading
import time

import pytest

from prik.compiler.objects import ObjectFile
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import (
    _compile_extension_objects,
    _normalize_compile_jobs,
    _project_compile_batches,
)


class TrackingCompiler:
    """Record the greatest number of simultaneous object compilations."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.active = 0
        self.maximum_active = 0

    def compile_object(self, object_file: ObjectFile, *, verbose: bool = False):
        del verbose
        with self._lock:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)
        time.sleep(0.03)
        object_file.object_path.parent.mkdir(parents=True, exist_ok=True)
        object_file.object_path.write_text("object\n", encoding="utf-8")
        with self._lock:
            self.active -= 1
        return ("compiler", str(object_file.source))


def _object(source: Path, build_dir: Path, *, language: str = "fortran") -> ObjectFile:
    return ObjectFile(source, build_dir / f"{source.stem}.o", language)


def test_project_compile_batches_respect_module_dependencies_and_group_ready_sources(tmp_path: Path) -> None:
    producer = tmp_path / "types.f90"
    consumer = tmp_path / "solver.f90"
    independent = tmp_path / "utility.f90"
    sources = {
        str(consumer): "module solver\nuse types\nend module solver\n",
        str(independent): "subroutine utility()\nend subroutine utility\n",
        str(producer): "module types\nend module types\n",
    }
    project = parse_fortran_project(sources)
    objects = tuple(_object(Path(source), tmp_path / "build") for source in sources)

    batches = _project_compile_batches(project, objects)

    assert [{item.source for item in batch} for batch in batches] == [
        {independent, producer},
        {consumer},
    ]


def test_project_compile_batches_follow_use_natures_and_submodule_identities(tmp_path: Path) -> None:
    """An intrinsic use waits on no project source, and a submodule waits on its own parent.

    ``a:impl`` and ``b:impl`` share a name; each nested ``leaf`` compiles after
    its own ``impl``, and a scope using the processor's ``ieee_arithmetic``
    does not wait on a user source of that name.
    """
    paths = {
        name: tmp_path / f"{name}.f90"
        for name in ("ieee", "processor", "a", "b", "a_impl", "b_impl", "a_leaf", "b_leaf")
    }
    sources = {
        str(paths["ieee"]): "module ieee_arithmetic\nend module ieee_arithmetic\n",
        str(paths["processor"]): "module processor\nuse, intrinsic :: ieee_arithmetic\nend module processor\n",
        str(paths["a"]): "module a\nend module a\n",
        str(paths["b"]): "module b\nend module b\n",
        str(paths["a_impl"]): "submodule (a) impl\nend submodule impl\n",
        str(paths["b_impl"]): "submodule (b) impl\nend submodule impl\n",
        str(paths["a_leaf"]): "submodule (a:impl) leaf\nend submodule leaf\n",
        str(paths["b_leaf"]): "submodule (b:impl) leaf\nend submodule leaf\n",
    }
    project = parse_fortran_project(sources)
    objects = tuple(_object(Path(source), tmp_path / "build") for source in sources)

    batches = _project_compile_batches(project, objects)

    batch_of = {item.source: index for index, batch in enumerate(batches) for item in batch}
    assert batch_of[paths["processor"]] == batch_of[paths["ieee"]] == 0
    for ancestor in ("a", "b"):
        assert batch_of[paths[ancestor]] < batch_of[paths[f"{ancestor}_impl"]] < batch_of[paths[f"{ancestor}_leaf"]]


def test_project_compile_batches_fall_back_to_input_order_for_unparsed_native_sources(tmp_path: Path) -> None:
    wrapped = tmp_path / "wrapped.f90"
    supplemental = tmp_path / "supplemental.f90"
    project = parse_fortran_project({str(wrapped): "subroutine wrapped()\nend subroutine wrapped\n"})
    objects = (
        _object(wrapped, tmp_path / "build"),
        _object(supplemental, tmp_path / "build"),
    )

    batches = _project_compile_batches(project, objects)

    assert batches == ((objects[0],), (objects[1],))


def test_independent_native_and_binding_objects_compile_concurrently(tmp_path: Path) -> None:
    compiler = TrackingCompiler()
    native_a = _object(tmp_path / "a.f90", tmp_path / "build")
    native_b = _object(tmp_path / "b.f90", tmp_path / "build")
    binding = _object(tmp_path / "binding.c", tmp_path / "build", language="c")

    _compile_extension_objects(
        compiler,
        native_batches=((native_a, native_b),),
        bridge_objects=(),
        binding_objects=(binding,),
        jobs=3,
        verbose=False,
    )

    assert compiler.maximum_active == 3


def test_compile_job_limit_accepts_auto_or_positive_values_and_rejects_invalid_values(monkeypatch) -> None:
    monkeypatch.setattr("prik.pipeline.build._available_compile_jobs", lambda: 7)

    assert _normalize_compile_jobs(None) == 7
    assert _normalize_compile_jobs(2) == 2
    for invalid in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="positive integer"):
            _normalize_compile_jobs(invalid)
