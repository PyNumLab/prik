"""An unedited semantic contract is authoritative runtime build input."""

import importlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture
from tests.fortran._support.wrapper_build import _compiler, _import_from_build_dir
from prik import build_pyi_extension
from prik.compiler.objects import ObjectFile
from prik.pipeline.build import _new_compiler

FEATURE_ROOT = Path(__file__).parents[1]
FIXTURES = FEATURE_ROOT / "pipeline" / "fixtures"
SOURCE = FIXTURES / "native" / "contract_mixed_module_external.f90"
EXPECTED_CONTRACT = FIXTURES / "contracts" / "contract_mixed_module_external" / "generated"
pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


def _import_extension(module_name: str, build_dir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(build_dir))


def _remove_imported_module_tree(module_name: str):
    """Remove one temporary extension and any native child modules it loaded."""
    prefix = f"{module_name}."
    for name in tuple(sys.modules):
        if name == module_name or name.startswith(prefix):
            sys.modules.pop(name, None)


@pytest.fixture
def compiled_contract_rebuild(tmp_path: Path):
    native_dir = tmp_path / "native"
    native_dir.mkdir()
    native_object = native_dir / "contract_mixed_module_external.o"
    compiler = _new_compiler(input_compiler=_compiler())
    compiler.compile_object(
        ObjectFile(
            source=SOURCE,
            object_path=native_object,
            language="fortran",
            include_dirs=(native_dir,),
        )
    )

    contract_package = tmp_path / "contract"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(SOURCE),
            "--out",
            str(contract_package),
            "--compiler",
            _compiler(),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert_generated_pyi_package_matches_fixture(contract_package, EXPECTED_CONTRACT)

    build_dir = tmp_path / "build"
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_dir],
        output_dir=build_dir,
    )
    module = _import_extension(result.module_name, build_dir)
    try:
        yield module, result
    finally:
        _remove_imported_module_tree(result.module_name)


def test_generated_contract_rebuilds_without_native_source_fallback(compiled_contract_rebuild):
    module, result = compiled_contract_rebuild

    assert result.module_name == "contract"
    assert not hasattr(module, "module_increment")
    assert module.contract_math_mod.module_increment(np.int32(4)) == np.int32(5)
    assert module.external_double(np.int32(4)) == np.int32(8)


WILDCARD_SOURCE = (NATIVE_FIXTURES / "wildcard_home.f90").read_text(encoding="utf-8")


def _wildcard_contracts(tmp_path: Path, consumer: str) -> Path:
    """Generate contracts, withhold `two` from the home surface, add a consumer."""
    source = tmp_path / "wild.f90"
    source.write_text(WILDCARD_SOURCE, encoding="utf-8")
    package = tmp_path / "contracts"
    subprocess.run(
        [sys.executable, "-m", "prik", "generate", "--pyi", str(source), "--out", str(package)],
        capture_output=True,
        text=True,
        check=True,
    )
    home = package / "wild_home.pyi"
    home.write_text(home.read_text(encoding="utf-8").replace('["one", "two"]', '["one"]'), encoding="utf-8")
    package.joinpath("wild_reader.pyi").write_text(consumer, encoding="utf-8")
    package.joinpath("__init__.pyi").write_text(
        'from . import wild_home\nfrom . import wild_reader\n\n__all__ = ["wild_home", "wild_reader"]\n',
        encoding="utf-8",
    )
    return package / "__init__.pyi"


def _build_wildcard(entry: Path, tmp_path: Path, name: str):
    result = build_pyi_extension(
        entry,
        input_compiler=_compiler(),
        native_fortran_sources=[str(tmp_path / "wild.f90")],
        output_dir=tmp_path / name,
        output_name=name,
    )
    return _import_from_build_dir(result.module_name, result.output_dir)


def test_wildcard_import_reads_only_the_surface_its_dependency_publishes(tmp_path: Path):
    """A wildcard takes what a contract publishes, not everything it holds.

    The dependency stated its surface, and a name left off it is not part of
    what writing `*` asks for.
    """
    entry = _wildcard_contracts(tmp_path, "from .wild_home import *\n")
    module = _build_wildcard(entry, tmp_path, "wildcard_star")

    assert hasattr(module.wild_home, "one")
    assert not hasattr(module.wild_home, "two")
    assert hasattr(module.wild_reader, "one")
    assert not hasattr(module.wild_reader, "two")


def test_explicit_import_reaches_and_can_republish_a_withheld_name(tmp_path: Path):
    """A withheld name stays reachable, because a contract may still need it.

    Expressing a declaration or publishing the name again both require asking
    for it, which is exactly what naming it in an import does.
    """
    entry = _wildcard_contracts(tmp_path, 'from .wild_home import two\n\n__all__ = ["two"]\n')
    module = _build_wildcard(entry, tmp_path, "wildcard_named")

    assert not hasattr(module.wild_home, "two")
    assert module.wild_reader.two(np.int32(5)) == np.int32(7)
