import json
from dataclasses import asdict
from pathlib import Path

from prik.parsers.fortran import parse_fortran_file
from prik.semantics.fortran2ir import fortran_module_to_semantic_module

FORTRAN_ROOT = Path(__file__).resolve().parents[1]
PARSER_FIXTURE_ROOT = FORTRAN_ROOT / "infrastructure" / "parsing" / "fixtures"
GENERAL_FORTRAN_DIR = PARSER_FIXTURE_ROOT / "general"
SEMANTICS_FIXTURE_DIR = (
    FORTRAN_ROOT / "infrastructure" / "semantic_ir" / "semantics" / "fixtures" / "general" / "expected"
)
FORTRAN_SUFFIXES = {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"}


def iter_general_fortran_fixtures():
    return sorted(
        path for path in GENERAL_FORTRAN_DIR.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES
    )


def fortran_fixture_requires_compiler_preprocessing(path: Path) -> bool:
    return any(line.lstrip().startswith("#") for line in path.read_text(encoding="utf-8").splitlines())


def parse_fixture(path: Path):
    source = path.read_text(encoding="utf-8")
    return parse_fortran_file(source, filename=path.name)


def semantic_modules_for_fixture(path: Path):
    parsed = parse_fixture(path)
    return [fortran_module_to_semantic_module(module) for module in parsed.modules]


def _prune_empty_nested_class_lists(value):
    if isinstance(value, list):
        return [_prune_empty_nested_class_lists(item) for item in value]
    if not isinstance(value, dict):
        return value

    is_class_payload = {"fields", "methods", "base_classes"}.issubset(value)
    return {
        key: _prune_empty_nested_class_lists(item)
        for key, item in value.items()
        if not (is_class_payload and key == "classes" and item == [])
    }


def semantic_payload_for_fixture(path: Path) -> dict:
    return {
        "semantic_modules": [
            _prune_empty_nested_class_lists(asdict(module)) for module in semantic_modules_for_fixture(path)
        ]
    }


def semantics_fixture_path(path: Path) -> Path:
    return (SEMANTICS_FIXTURE_DIR / path.name).with_suffix(".json")


def write_semantics_fixture(path: Path) -> Path:
    out = semantics_fixture_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(semantic_payload_for_fixture(path), indent=2) + "\n", encoding="utf-8")
    return out
