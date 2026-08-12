"""Generate/update golden files for grouped C parser fixture projects."""

from __future__ import annotations

import json
import re
import shutil
import sys
from contextlib import suppress
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


_C_DATA_DIR = Path(__file__).resolve().parents[1] / "native"
_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
_FIXTURE_GROUPS = ("general", "json", "tinyexpr", "linmath", "nanosvg", "stb")
_SOURCE_SUFFIXES = {".c", ".h", ".i"}
_SOURCE_ORDER = {".c": 0, ".h": 1, ".i": 2}
_PROJECT_OVERRIDES = {
    "nanosvg": {
        "nanosvg": ("nanosvg.h", "nanosvgrast.h"),
    },
}
_DEFINE_OVERRIDES = {
    "nanosvg.h": ("NANOSVG_IMPLEMENTATION",),
    "nanosvgrast.h": ("NANOSVGRAST_IMPLEMENTATION",),
    "stb_ds.h": ("STB_DS_IMPLEMENTATION",),
    "stb_dxt.h": ("STB_DXT_IMPLEMENTATION",),
    "stb_image.h": ("STB_IMAGE_IMPLEMENTATION",),
    "stb_rect_pack.h": ("STB_RECT_PACK_IMPLEMENTATION",),
}
_DECLARATION_SECTIONS = ("functions", "structs", "unions", "enums", "typedefs", "variables", "enum_constants")
_FILE_DECLARATION_SECTIONS = ("functions", "structs", "unions", "enums", "typedefs", "variables")
_TAG_PREFIXES = {"structs": "struct", "unions": "union", "enums": "enum"}
_SYSTEM_ANONYMOUS_ID = re.compile(r"@/[^:]+:\d+:\d+")


def _parser_filename_for_fixture(fixture: Path) -> str:
    return fixture.relative_to(_C_DATA_DIR).as_posix()


def _fixture_sort_key(fixture: Path) -> tuple[int, str]:
    return (_SOURCE_ORDER.get(fixture.suffix.lower(), 99), fixture.as_posix())


def _project_key(fixture: Path) -> Path:
    relative = fixture.relative_to(_C_DATA_DIR)
    group = relative.parts[0]
    for project_name, filenames in _PROJECT_OVERRIDES.get(group, {}).items():
        if relative.name in filenames:
            return Path(group) / project_name
    return relative.with_suffix("")


def _group_projects(fixtures: list[Path]) -> list[tuple[Path, list[Path]]]:
    grouped: dict[Path, list[Path]] = {}
    for fixture in sorted(fixtures, key=_fixture_sort_key):
        grouped.setdefault(_project_key(fixture), []).append(fixture)
    return [
        (project_key, _ordered_project_fixtures(project_key, project_fixtures))
        for project_key, project_fixtures in sorted(grouped.items())
    ]


def _ordered_project_fixtures(project_key: Path, fixtures: list[Path]) -> list[Path]:
    group = project_key.parts[0]
    override = _PROJECT_OVERRIDES.get(group, {}).get(project_key.name)
    if override is not None:
        order = {filename: index for index, filename in enumerate(override)}
        return sorted(fixtures, key=lambda fixture: order[fixture.name])
    return sorted(fixtures, key=_fixture_sort_key)


def _normalize_resolved_paths(value):
    if isinstance(value, dict):
        resolved_path = value.get("resolved_path")
        if resolved_path:
            with suppress(ValueError):
                value["resolved_path"] = Path(resolved_path).relative_to(_C_DATA_DIR).as_posix()
        for key, nested in value.items():
            if key == "source_text" and isinstance(nested, str):
                value[key] = " ".join(nested.split())
            else:
                value[key] = _normalize_resolved_paths(nested)
    elif isinstance(value, list):
        return [_normalize_resolved_paths(nested) for nested in value]
    elif isinstance(value, str):
        try:
            path = Path(value)
            if path.is_absolute():
                return path.relative_to(_C_DATA_DIR).as_posix()
        except ValueError:
            pass
    return value


def _is_project_filename(filename: object) -> bool:
    return isinstance(filename, str) and not Path(filename).is_absolute()


def _is_project_location(location: object) -> bool:
    return isinstance(location, dict) and _is_project_filename(location.get("filename"))


def _project_source_line(filename: object, line: object) -> str | None:
    if not _is_project_filename(filename) or not isinstance(line, int) or line <= 0:
        return None
    source = _C_DATA_DIR / filename
    if not source.is_file():
        return None
    try:
        return source.read_text(encoding="utf-8").splitlines()[line - 1]
    except IndexError:
        return None


def _stable_project_location(location: dict) -> dict:
    source_line = _project_source_line(location.get("filename"), location.get("line"))
    if source_line is None:
        return location
    return {**location, "source_line": source_line}


def _has_project_source_location(declaration: object) -> bool:
    return isinstance(declaration, dict) and _is_project_location(declaration.get("source_location"))


def _declaration_identifiers(section: str, declaration: object, fallback: str | None = None) -> set[str]:
    if not isinstance(declaration, dict):
        return {fallback} if fallback is not None else set()

    identifiers = {fallback} if fallback is not None else set()
    for key in ("name", "reference", "anonymous_id"):
        value = declaration.get(key)
        if isinstance(value, str):
            identifiers.add(value)

    prefix = _TAG_PREFIXES.get(section)
    name = declaration.get("name")
    reference = declaration.get("reference")
    if prefix is not None:
        if isinstance(name, str):
            identifiers.add(f"{prefix} {name}")
        if isinstance(reference, str) and reference.startswith(f"{prefix} "):
            identifiers.add(reference.removeprefix(f"{prefix} "))

    return {identifier for identifier in identifiers if identifier}


def _collect_project_symbols(payload: dict) -> dict[str, set[str]]:
    symbols = {section: set() for section in _DECLARATION_SECTIONS}

    def collect(section: str, declaration: object, fallback: str | None = None) -> None:
        if _has_project_source_location(declaration):
            symbols[section].update(_declaration_identifiers(section, declaration, fallback))

    for file_payload in payload.get("files", {}).values():
        if not isinstance(file_payload, dict):
            continue
        for section in _FILE_DECLARATION_SECTIONS:
            for declaration in file_payload.get(section, []):
                collect(section, declaration)
        for enum_declaration in file_payload.get("enums", []):
            if isinstance(enum_declaration, dict) and _has_project_source_location(enum_declaration):
                for constant in enum_declaration.get("constants", []):
                    collect("enum_constants", constant)

    for section in _DECLARATION_SECTIONS:
        declarations = payload.get(section, {})
        if not isinstance(declarations, dict):
            continue
        for name, declaration in declarations.items():
            collect(section, declaration, name)

    return symbols


def _is_project_declaration(
    section: str,
    declaration: object,
    symbols: dict[str, set[str]],
    fallback: str | None = None,
) -> bool:
    if _has_project_source_location(declaration):
        return True
    return bool(_declaration_identifiers(section, declaration, fallback) & symbols[section])


def _is_project_diagnostic(diagnostic: object) -> bool:
    if not isinstance(diagnostic, dict):
        return True
    location = diagnostic.get("location")
    if not isinstance(location, dict):
        return True
    filename = location.get("filename")
    return filename is None or _is_project_filename(filename)


def _system_declaration_reference(declaration: dict) -> str | None:
    source_location = declaration.get("source_location")
    if _is_project_location(source_location):
        return None
    if not isinstance(source_location, dict) or _is_project_filename(source_location.get("filename")):
        return None

    model = declaration.get("model")
    name = declaration.get("name")
    anonymous_id = declaration.get("anonymous_id")
    if model == "CTypedef" and isinstance(name, str):
        return name
    if model == "CStruct":
        return f"struct {name}" if isinstance(name, str) else str(anonymous_id or "<system-header>")
    if model == "CUnion":
        return f"union {name}" if isinstance(name, str) else str(anonymous_id or "<system-header>")
    if model == "CEnum":
        return f"enum {name}" if isinstance(name, str) else str(anonymous_id or "<system-header>")
    return None


def _stable_bool_payload(qualifiers: object = None) -> dict:
    return {"model": "CBool", "qualifiers": list(qualifiers or []), "source_text": "bool"}


def _stable_bool_type_payload(declaration: dict) -> dict | None:
    if declaration.get("reference") == "bool":
        return _stable_bool_payload()
    if declaration.get("model") == "CBool":
        return _stable_bool_payload(declaration.get("qualifiers"))
    if (
        declaration.get("model") == "CTypedef"
        and declaration.get("name") == "bool"
        and not _is_project_location(declaration.get("source_location"))
    ):
        return _stable_bool_payload(declaration.get("qualifiers"))
    return None


def _stable_payload_value(value, symbols: dict[str, set[str]]):
    if isinstance(value, dict):
        bool_payload = _stable_bool_type_payload(value)
        if bool_payload is not None:
            return bool_payload

        reference = _system_declaration_reference(value)
        if reference is not None:
            return {"reference": _stable_payload_value(reference, symbols)}

        stable = {}
        for key, nested in value.items():
            if key == "source_text" and isinstance(nested, str):
                stable[key] = " ".join(nested.split())
                continue
            if key in _DECLARATION_SECTIONS and isinstance(nested, dict):
                stable[key] = {
                    name: _stable_payload_value(item, symbols)
                    for name, item in nested.items()
                    if _is_project_declaration(key, item, symbols, name)
                }
                continue
            if key in _FILE_DECLARATION_SECTIONS and isinstance(nested, list):
                stable[key] = [
                    _stable_payload_value(item, symbols)
                    for item in nested
                    if _is_project_declaration(key, item, symbols)
                ]
                continue
            if key == "functions_by_file" and isinstance(nested, dict):
                stable[key] = {
                    filename: [name for name in names if name in symbols["functions"]]
                    for filename, names in nested.items()
                }
                continue
            if key == "diagnostics" and isinstance(nested, list):
                stable[key] = [_stable_payload_value(item, symbols) for item in nested if _is_project_diagnostic(item)]
                continue
            if key == "original_source_paths" and isinstance(nested, list):
                stable[key] = [_stable_payload_value(item, symbols) for item in nested if _is_project_filename(item)]
                continue
            if key in {"location", "source_location", "start", "end"} and isinstance(nested, dict):
                filename = nested.get("filename")
                if filename is not None and not _is_project_filename(filename):
                    stable[key] = {
                        **nested,
                        "filename": "<system-header>",
                        "line": 0,
                        "column": 0,
                        "source_line": None,
                    }
                    continue
                if _is_project_filename(filename):
                    stable[key] = _stable_project_location(nested)
                    continue
            stable[key] = _stable_payload_value(nested, symbols)
        return stable
    if isinstance(value, list):
        return [_stable_payload_value(item, symbols) for item in value]
    if isinstance(value, str):
        if Path(value).is_absolute():
            return "<system-header>"
        return _SYSTEM_ANONYMOUS_ID.sub("@<system-header>:0:0", value)
    return value


def _stable_project_payload(payload: dict) -> dict:
    return _stable_payload_value(payload, _collect_project_symbols(payload))


def _serialize_project(fixtures: list[Path]) -> dict:
    from prik.parsers.c import CParser

    parser = CParser()
    include_dirs = sorted({fixture.parent for fixture in fixtures})
    parsed_files = {}
    for fixture in sorted(fixtures, key=_fixture_sort_key):
        filename = _parser_filename_for_fixture(fixture)
        parsed_files[filename] = _parse_fixture(parser, fixture, filename=filename, include_dirs=include_dirs)
    project = parser._assemble_project(parsed_files)
    return _stable_project_payload(_normalize_resolved_paths(project.to_dict()))


def _parse_fixture(parser, fixture: Path, *, filename: str, include_dirs: list[Path]):
    from prik.preprocessing import PreprocessingConfig, preprocess_source

    compiler = shutil.which("cc")
    if compiler is None:
        raise SystemExit("cc is required to preprocess C fixtures") from None
    preprocessed = preprocess_source(
        fixture,
        language="c",
        config=PreprocessingConfig(
            mode="compiler",
            compiler=compiler,
            include_dirs=[str(path) for path in include_dirs],
            defines=list(_DEFINE_OVERRIDES.get(fixture.name, ())),
        ),
    )
    return parser.parse_file(
        preprocessed.source,
        filename=filename,
        include_dirs=include_dirs,
        preprocessing="compiler",
    )


def _sibling_fixtures(fixture: Path) -> list[Path]:
    relative = fixture.relative_to(_C_DATA_DIR)
    group = relative.parts[0]
    for filenames in _PROJECT_OVERRIDES.get(group, {}).values():
        if fixture.name in filenames:
            return [fixture.parent / filename for filename in filenames]
    return sorted(
        (
            sibling
            for sibling in fixture.parent.glob(f"{fixture.stem}.*")
            if sibling.is_file() and sibling.suffix.lower() in _SOURCE_SUFFIXES
        ),
        key=_fixture_sort_key,
    )


def _default_projects() -> list[tuple[Path, list[Path]]]:
    fixtures = [
        fixture
        for group in _FIXTURE_GROUPS
        for fixture in (_C_DATA_DIR / group).rglob("*")
        if fixture.is_file() and fixture.suffix.lower() in _SOURCE_SUFFIXES
    ]
    return _group_projects(fixtures)


def _requested_projects(items: list[str]) -> list[tuple[Path, list[Path]]]:
    fixtures: list[Path] = []
    for item in items:
        fixture = Path(item)
        if not fixture.is_absolute():
            fixture = _C_DATA_DIR / fixture
        if fixture.suffix.lower() not in _SOURCE_SUFFIXES:
            raise SystemExit(f"C fixtures must use .c, .h, or .i: {fixture}")
        if not fixture.exists():
            raise SystemExit(f"Fixture does not exist: {fixture}")
        fixtures.extend(_sibling_fixtures(fixture))
    return _group_projects(fixtures)


def _output_path_for_project(project_key: Path) -> Path:
    return (_FIXTURES_DIR / project_key).with_suffix(".json")


def main() -> None:
    requested = sys.argv[1:]
    projects = _requested_projects(requested) if requested else _default_projects()
    if not projects:
        raise SystemExit("No C parser fixtures found")

    failures = []
    for project_key, fixtures in projects:
        try:
            payload = _serialize_project(fixtures)
            out = _output_path_for_project(project_key)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"updated {out}")
        except Exception as exc:
            failures.append((project_key, exc))

    if failures:
        for project_key, exc in failures:
            print(f"failed {project_key}: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
