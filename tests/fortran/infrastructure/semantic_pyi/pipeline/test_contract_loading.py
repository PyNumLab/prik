"""Contract-package loading, graph, validation, and round-trip evidence."""

from pathlib import Path

import pytest

import prik.pipeline.pyi as pyi_pipeline
from prik import build_pyi_extension
from prik.pipeline import build as build_pipeline
from prik.pipeline.build import _discover_pyi_imports, _pyi_contract_bundle, _pyi_dependency_path
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text
from prik.printers import emit_module

FIXTURES = Path(__file__).parent / "fixtures"
CONTRACT_FIXTURES = FIXTURES / "contracts"
INVALID_NATIVE_CALL_PYI = FIXTURES / "invalid" / "projection_metadata" / "incomplete_native_call.pyi"
CHECKED_CONTRACTS = sorted(CONTRACT_FIXTURES.rglob("*.pyi"))


def test_checked_contract_package_has_reviewed_files():
    assert [str(path.relative_to(CONTRACT_FIXTURES)) for path in CHECKED_CONTRACTS] == [
        "contract_import_graph/generated/__init__.pyi",
        "contract_import_graph/generated/deep.pyi",
        "contract_import_graph/generated/m1.pyi",
        "contract_mixed_module_external/generated/__init__.pyi",
        "contract_mixed_module_external/generated/contract_math_mod.pyi",
        "contract_same_name/generated/__init__.pyi",
        "contract_same_name/generated/contract_same_name.pyi",
        "contract_standalone_only/generated/__init__.pyi",
    ]


@pytest.mark.parametrize(
    "fixture",
    CHECKED_CONTRACTS,
    ids=lambda path: str(path.relative_to(CONTRACT_FIXTURES)),
)
def test_checked_contracts_round_trip_through_semantic_ir(fixture: Path):
    expected = fixture.read_text(encoding="utf-8").strip()
    module_name = fixture.parent.parent.name if fixture.name == "__init__.pyi" else fixture.stem
    module = parse_pyi_text(expected, module_name=module_name, filename=str(fixture))

    assert "Unknown" not in expected
    assert emit_module(module).strip() == expected


@pytest.mark.parametrize(
    "package",
    sorted(path.parent for path in CONTRACT_FIXTURES.glob("*/generated/__init__.pyi")),
    ids=lambda path: path.parent.name,
)
def test_checked_entry_discovers_its_complete_contract_package(package: Path):
    entry = package / "__init__.pyi"

    assert {entry, *_discover_pyi_imports(entry)} == set(package.rglob("*.pyi"))


def test_pyi_contract_bundle_reuses_import_discovery_conversion_cache(monkeypatch, tmp_path: Path):
    entry = tmp_path / "api.pyi"
    dependency = tmp_path / "types_mod.pyi"
    entry.write_text(
        """
from prik.contracts import Float64
from .types_mod import particle

def inspect(item: particle) -> Float64: ...
""",
        encoding="utf-8",
    )
    dependency.write_text(
        """
from prik.contracts import Float64

class particle:
    mass: Float64
""",
        encoding="utf-8",
    )

    original_parse = pyi_pipeline.parse_pyi_text
    parsed_filenames: list[Path] = []

    def parse_once(source: str, *, filename: str = "<pyi>"):
        parsed_filenames.append(Path(filename))
        return original_parse(source, filename=filename)

    monkeypatch.setattr(pyi_pipeline, "parse_pyi_text", parse_once)

    bundle = _pyi_contract_bundle(entry)

    assert bundle.paths == (entry, dependency)
    assert parsed_filenames == [entry, dependency]


def test_relative_contract_dependency_prefers_package_entry(tmp_path: Path):
    package = tmp_path / "types"
    package.mkdir()
    entry = package / "__init__.pyi"
    entry.write_text("", encoding="utf-8")

    assert _pyi_dependency_path(tmp_path, "types") == entry


def test_pyi_contract_bundle_checks_native_contract_before_returning_modules(monkeypatch, tmp_path: Path):
    contract = tmp_path / "native_contract.pyi"
    contract.write_text(
        """
from prik.contracts import Float64

def scale(x: Float64) -> Float64: ...
""",
        encoding="utf-8",
    )

    checked_modules = []

    def fail_native_contract_validation(modules):
        checked_modules.extend(modules)
        raise ValueError("native contract was checked during bundle loading")

    monkeypatch.setattr(build_pipeline, "validate_pyi_native_contract", fail_native_contract_validation)

    with pytest.raises(ValueError, match="native contract was checked during bundle loading"):
        _pyi_contract_bundle(contract)
    assert [module.name for module in checked_modules] == ["native_contract"]


def test_recursive_graph_reports_missing_relative_contract_before_native_validation(tmp_path: Path):
    entry = tmp_path / "api.pyi"
    entry.write_text("from . import missing\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match=r"missing\.pyi"):
        build_pyi_extension(entry, native_objects=[tmp_path / "unused.o"])


def test_recursive_graph_reports_cycles_before_codegen(tmp_path: Path):
    entry = tmp_path / "api.pyi"
    dependency = tmp_path / "dependency.pyi"
    entry.write_text("from . import dependency\n", encoding="utf-8")
    dependency.write_text("from . import api\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"Cyclic relative \.pyi export imports"):
        build_pyi_extension(entry, native_objects=[tmp_path / "unused.o"])


def test_pyi_python_api_rejects_invalid_projection_before_codegen(tmp_path: Path):
    native_object = tmp_path / "native.o"
    native_object.touch()

    with pytest.raises(ValueError, match="native_call argument position is out of range"):
        build_pyi_extension(INVALID_NATIVE_CALL_PYI, native_objects=[native_object], output_dir=tmp_path / "build")

    assert not list((tmp_path / "build").glob("*_wrapper.*"))


STALE_PACKAGE_HOME = (
    "from prik.contracts import Int32\n\ndef calculate(value: Int32) -> Int32: ...\n\n__all__ = [{names}]\n"
)


def _stale_package(tmp_path: Path, home: str, reader: str | None = None) -> Path:
    package = tmp_path / "pkg"
    package.mkdir(parents=True)
    package.joinpath("home_mod.pyi").write_text(home, encoding="utf-8")
    modules = ["home_mod"]
    if reader is not None:
        package.joinpath("reader_mod.pyi").write_text(reader, encoding="utf-8")
        modules.append("reader_mod")
    lines = "".join(f"from . import {name}\n" for name in modules)
    stated = ", ".join(f'"{name}"' for name in modules)
    package.joinpath("__init__.pyi").write_text(f"{lines}\n__all__ = [{stated}]\n", encoding="utf-8")
    return package / "__init__.pyi"


def _loaded_modules(entry: Path) -> dict[Path, object]:
    """Load one contract package the way a wrapper build loads it."""
    cache = pyi_pipeline._PyiSemanticModuleCache()
    paths = tuple(sorted({entry, *_discover_pyi_imports(entry, cache)}))
    return dict(zip(paths, cache.paths_to_semantic_modules(paths), strict=True))


def test_all_naming_a_renamed_declaration_is_rejected(tmp_path: Path):
    """`__all__` asserts a surface, so a name it states has to exist.

    Renaming a declaration renames what the contract publishes. Dropping the
    stale name instead would leave the contract publishing nothing and say so
    nowhere, which is far harder to find than a refused build.
    """
    entry = _stale_package(tmp_path, STALE_PACKAGE_HOME.format(names='"old_name"'))

    with pytest.raises(ValueError, match=r"__all__ names nothing this contract declares or imports"):
        build_pipeline._apply_pyi_python_exports(entry, _loaded_modules(entry))


def test_all_naming_a_stale_imported_alias_is_rejected(tmp_path: Path):
    """An imported name that no longer arrives under that alias is stale too."""
    entry = _stale_package(
        tmp_path,
        STALE_PACKAGE_HOME.format(names='"calculate"'),
        'from .home_mod import calculate as renamed\n\n__all__ = ["calculate"]\n',
    )

    with pytest.raises(ValueError, match=r"__all__ names nothing this contract declares or imports"):
        build_pipeline._apply_pyi_python_exports(entry, _loaded_modules(entry))


def test_all_accepts_an_empty_list_and_repeated_names(tmp_path: Path):
    """Publishing nothing is a statement; naming one entity twice states it once."""
    entry = _stale_package(tmp_path, STALE_PACKAGE_HOME.format(names=""))
    build_pipeline._apply_pyi_python_exports(entry, _loaded_modules(entry))

    entry = _stale_package(tmp_path / "again", STALE_PACKAGE_HOME.format(names='"calculate", "calculate"'))
    build_pipeline._apply_pyi_python_exports(entry, _loaded_modules(entry))
