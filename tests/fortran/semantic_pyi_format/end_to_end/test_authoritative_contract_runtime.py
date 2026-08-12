"""An unedited semantic contract is authoritative runtime build input."""

import importlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture
from tests.fortran._support.wrapper_build import _compiler
from prik import build_pyi_extension
from prik.compiler.objects import ObjectFile
from prik.pipeline.build import _new_compiler

FEATURE_ROOT = Path(__file__).parents[1]
FIXTURES = FEATURE_ROOT / "pipeline" / "fixtures"
SOURCE = FIXTURES / "native" / "contract_mixed_module_external.f90"
EXPECTED_CONTRACT = FIXTURES / "contracts" / "contract_mixed_module_external" / "generated"
pytestmark = pytest.mark.fortran_end_to_end


def _import_extension(module_name: str, build_dir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(build_dir))


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
    return module, result


def test_generated_contract_rebuilds_without_native_source_fallback(compiled_contract_rebuild):
    module, result = compiled_contract_rebuild

    assert result.module_name == "contract"
    assert not hasattr(module, "module_increment")
    assert module.contract_math_mod.module_increment(np.int32(4)) == np.int32(5)
    assert module.external_double(np.int32(4)) == np.int32(8)
