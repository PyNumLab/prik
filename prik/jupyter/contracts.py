"""Generate, identify, persist, and materialize editable notebook contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import shlex

from IPython.core.error import UsageError

from prik.preprocessing import PreprocessingConfig


_GENERATED_CONTRACT_SCHEMA_VERSION = 1
_GENERATED_CONTRACT_RECORD_NAME = "contracts.json"
_EDITABLE_CONTRACT_PREFIX = "# prik:"


@dataclass(frozen=True)
class GeneratedContracts:
    """Generated editable contracts associated with one exact native cell."""

    language: str
    source_digest: str
    module_contracts: dict[str, str]
    direct_contract: str | None
    dependency_contracts: dict[str, str]


@dataclass(frozen=True)
class EditableContract:
    """Notebook metadata plus the editable semantic contract text."""

    source_digest: str | None
    filename: str | None
    text: str


def _contract_filename(module_name: str) -> str:
    """Return the visible `.pyi` path that carries a native module namespace."""
    parts = module_name.split(".")
    if not parts or any(not part.isidentifier() for part in parts):
        raise ValueError(f"Cannot represent generated module name {module_name!r} as a .pyi filename")
    return PurePosixPath(*parts).with_suffix(".pyi").as_posix()


def _validated_contract_filename(value: str) -> str:
    """Validate one generated module contract path without accepting a package entry."""
    path = PurePosixPath(value)
    invalid_part = any(part in {"", ".", ".."} for part in path.parts)
    invalid_identifier = any(not part.isidentifier() for part in path.with_suffix("").parts)
    if path.is_absolute() or path.suffix != ".pyi" or path.name == "__init__.pyi":
        raise UsageError(f"Invalid editable .pyi filename {value!r}")
    if invalid_part or invalid_identifier:
        raise UsageError(f"Invalid editable .pyi filename {value!r}")
    return path.as_posix()


def _read_json_record(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _string_mapping(value: object, *, field_name: str) -> dict[str, str]:
    """Validate a JSON mapping whose keys and values must both be strings."""
    if not isinstance(value, dict):
        raise ValueError(f"Generated contract cache field {field_name!r} is invalid")
    if any(not isinstance(key, str) or not isinstance(text, str) for key, text in value.items()):
        raise ValueError(f"Generated contract cache field {field_name!r} is invalid")
    return dict(value)


def generated_contract_record_path(entry_dir: Path, fingerprint: str) -> Path:
    """Return the target-specific generated-contract record for one source."""
    return entry_dir / "generated-contracts" / fingerprint / _GENERATED_CONTRACT_RECORD_NAME


def write_generated_contracts(path: Path, contracts: GeneratedContracts) -> None:
    """Atomically persist generated contracts needed by later editable cells."""
    record = {
        "schema_version": _GENERATED_CONTRACT_SCHEMA_VERSION,
        "language": contracts.language,
        "source_digest": contracts.source_digest,
        "module_contracts": contracts.module_contracts,
        "direct_contract": contracts.direct_contract,
        "dependency_contracts": contracts.dependency_contracts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(f"{json.dumps(record, sort_keys=True, indent=2)}\n", encoding="utf-8")
    temporary.replace(path)


def _invalid_cache_message(*, invalid: bool) -> str:
    state = "invalid" if invalid else "unavailable or incompatible"
    return (
        f"The generated contract cache is {state} for these compiler and build options; "
        "execute its %%fortran --pyi or %%c --pyi source cell again with the desired options"
    )


def read_generated_contracts(
    path: Path,
    *,
    language: str,
    source_digest: str,
) -> GeneratedContracts:
    """Load and validate the generated contract bundle for one native cell."""
    record = _read_json_record(path)
    identity = (
        None
        if record is None
        else (
            record.get("schema_version"),
            record.get("language"),
            record.get("source_digest"),
        )
    )
    expected = (_GENERATED_CONTRACT_SCHEMA_VERSION, language, source_digest)
    if identity != expected:
        raise UsageError(_invalid_cache_message(invalid=False))
    assert record is not None
    try:
        module_contracts = _string_mapping(record.get("module_contracts"), field_name="module_contracts")
        dependency_contracts = _string_mapping(
            record.get("dependency_contracts"),
            field_name="dependency_contracts",
        )
    except ValueError as exc:
        raise UsageError(_invalid_cache_message(invalid=True)) from exc
    direct = record.get("direct_contract")
    if direct is not None and not isinstance(direct, str):
        raise UsageError(_invalid_cache_message(invalid=True))
    return GeneratedContracts(
        language=language,
        source_digest=source_digest,
        module_contracts=module_contracts,
        direct_contract=direct,
        dependency_contracts=dependency_contracts,
    )


def _metadata_line(filename: str | None, source_digest: str) -> str:
    parts = [_EDITABLE_CONTRACT_PREFIX]
    if filename is not None:
        parts.append(f"file={filename}")
    parts.append(f"source-sha256={source_digest}")
    return " ".join(parts)


def editable_cell_text(
    contract: str,
    *,
    filename: str | None,
    source_digest: str,
    magic_command: str,
) -> str:
    """Render one complete editable cell including its normal magic command."""
    return f"{magic_command}\n\n{_metadata_line(filename, source_digest)}\n\n{contract.rstrip()}\n"


def _metadata_values(marker: str) -> dict[str, str]:
    try:
        fields = shlex.split(marker.removeprefix(_EDITABLE_CONTRACT_PREFIX).strip())
    except ValueError as exc:
        raise UsageError(f"Invalid editable .pyi metadata: {exc}") from exc
    values: dict[str, str] = {}
    for field in fields:
        key, separator, value = field.partition("=")
        if not separator or key in values or key not in {"file", "source-sha256"}:
            raise UsageError(f"Invalid editable .pyi metadata field {field!r}")
        values[key] = value
    return values


def _source_digest(values: Mapping[str, str]) -> str | None:
    digest = values.get("source-sha256")
    if digest is None:
        return None
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise UsageError("Editable .pyi metadata requires a full lowercase source-sha256 digest")
    return digest


def parse_editable_contract(cell: str) -> EditableContract | None:
    """Recognize an editable contract carrying reserved notebook metadata."""
    lines = cell.splitlines(keepends=True)
    marker_indices = [index for index, line in enumerate(lines) if line.strip().startswith(_EDITABLE_CONTRACT_PREFIX)]
    if not marker_indices:
        return None
    if len(marker_indices) > 1:
        raise UsageError("An editable .pyi cell must contain exactly one PRIK metadata line")
    marker_index = marker_indices[0]
    marker = lines[marker_index].strip()
    values = _metadata_values(marker)
    filename = values.get("file")
    if filename is not None:
        filename = _validated_contract_filename(filename)
    del lines[marker_index]
    return EditableContract(
        source_digest=_source_digest(values),
        filename=filename,
        text="".join(lines),
    )


def _generated_contract_mapping(value: object, *, field_name: str) -> dict[str, str]:
    """Convert semantic-pipeline module names into safe relative `.pyi` paths."""
    if not isinstance(value, Mapping):
        raise ValueError(f"Generated semantic payload field {field_name!r} is invalid")
    contracts: dict[str, str] = {}
    for module_name, text in value.items():
        if not isinstance(module_name, str) or not isinstance(text, str):
            raise ValueError(f"Generated semantic payload field {field_name!r} is invalid")
        contracts[_contract_filename(module_name)] = text
    return contracts


def _source_semantic_report(source: Path, options) -> Mapping[str, object]:
    from prik.cli import _semantic_report

    preprocessing = PreprocessingConfig(
        mode="compiler",
        compiler=options.compiler,
        compiler_args=[*options.compiler_args, *options.native_compile_flags],
    )
    reports = _semantic_report([str(source)], preprocessing, language=options.language)
    report = reports.get(str(source))
    if not isinstance(report, Mapping):
        raise ValueError("PRIK did not generate a semantic contract for this source cell")
    return report


def generate_contracts_from_source(
    source: Path,
    *,
    source_digest: str,
    options,
) -> GeneratedContracts:
    """Reuse the CLI source-semantic route to extract editable contracts."""
    report = _source_semantic_report(source, options)
    dependencies = _generated_contract_mapping(
        report.get("pyi_dependencies", {}),
        field_name="pyi_dependencies",
    )
    if options.language == "c":
        contract = report.get("pyi")
        if not isinstance(contract, str) or not contract.strip():
            raise ValueError("PRIK did not generate any editable C declarations from this source cell")
        return GeneratedContracts(
            language=options.language,
            source_digest=source_digest,
            module_contracts={},
            direct_contract=contract,
            dependency_contracts=dependencies,
        )
    return _generated_fortran_contracts(
        report,
        language=options.language,
        source_digest=source_digest,
        dependencies=dependencies,
    )


def _generated_fortran_contracts(
    report: Mapping[str, object],
    *,
    language: str,
    source_digest: str,
    dependencies: dict[str, str],
) -> GeneratedContracts:
    from prik.cli import _source_root_stub

    modules = _generated_contract_mapping(report.get("pyi_modules", {}), field_name="pyi_modules")
    external_sections = report.get("pyi_root_externals", ())
    if not isinstance(external_sections, list) or any(not isinstance(text, str) for text in external_sections):
        raise ValueError("Generated semantic payload field 'pyi_root_externals' is invalid")
    standalone = _source_root_stub([], external_sections) if external_sections else None
    if not modules and not standalone:
        raise ValueError("PRIK did not generate any editable Fortran declarations from this source cell")
    return GeneratedContracts(
        language=language,
        source_digest=source_digest,
        module_contracts=modules,
        direct_contract=standalone,
        dependency_contracts=dependencies,
    )


def generated_editable_cells(
    contracts: GeneratedContracts,
    *,
    magic_command: str,
) -> list[str]:
    """Render one editable notebook cell per visible generated contract."""
    cells = [
        editable_cell_text(
            text,
            filename=filename,
            source_digest=contracts.source_digest,
            magic_command=magic_command,
        )
        for filename, text in contracts.module_contracts.items()
    ]
    if contracts.direct_contract is not None:
        cells.append(
            editable_cell_text(
                contracts.direct_contract,
                filename=None,
                source_digest=contracts.source_digest,
                magic_command=magic_command,
            )
        )
    return cells


def insert_editable_cells(shell, cells: list[str]) -> tuple[str, ...]:
    """Present editable cells and return any awaiting a terminal prompt."""
    if not cells:
        raise UsageError("PRIK did not generate an editable .pyi cell")
    set_next_input = getattr(shell, "set_next_input", None)
    if not callable(set_next_input):
        raise UsageError("This IPython frontend cannot insert an editable .pyi cell")

    first, *remaining = cells
    set_next_input(first, replace=False)
    if getattr(shell, "rl_next_input", None) == first:
        return tuple(remaining)

    payload_manager = getattr(shell, "payload_manager", None)
    write_payload = getattr(payload_manager, "write_payload", None)
    if callable(write_payload):
        for text in remaining:
            write_payload(
                {"source": "set_next_input", "text": text, "replace": False},
                single=False,
            )
        return ()
    for text in remaining:
        set_next_input(text, replace=False)
    return ()


def _write_contract_file(root: Path, relative_name: str, text: str) -> Path:
    """Materialize one validated generated contract below a build-local package."""
    validated = _validated_contract_filename(relative_name)
    target = root.joinpath(*PurePosixPath(validated).parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{text.rstrip()}\n", encoding="utf-8")
    return target


def _merge_contract_files(destination: dict[str, str], additions: Mapping[str, str]) -> None:
    """Merge generated support contracts without silently changing a path."""
    for filename, text in additions.items():
        validated = _validated_contract_filename(filename)
        previous = destination.get(validated)
        if previous is not None and previous != text:
            raise UsageError(f"Generated editable contract dependencies conflict at {validated}")
        destination[validated] = text


def materialize_editable_contract(
    entry_dir: Path,
    editable: EditableContract,
    generated: GeneratedContracts,
) -> Path:
    """Create the hidden contract package consumed by `build_pyi_extension()`."""
    package = entry_dir / "contract"
    package.mkdir(parents=True, exist_ok=True)
    support_contracts: dict[str, str] = {}
    _merge_contract_files(support_contracts, generated.dependency_contracts)
    _merge_contract_files(support_contracts, generated.module_contracts)

    if editable.filename is None:
        entry = _materialize_direct_entry(package, editable, generated)
    else:
        entry = _materialize_module_entry(package, editable, generated, support_contracts)
    for filename, text in support_contracts.items():
        _write_contract_file(package, filename, text)
    return entry


def materialize_handwritten_contract(
    entry_dir: Path,
    editable: EditableContract,
    *,
    native_language: str,
) -> Path:
    """Create one handwritten cell contract for the ordinary `.pyi` build path."""
    if editable.source_digest is not None:
        raise UsageError("A handwritten .pyi contract cannot carry generated source digest metadata")
    package = entry_dir / "contract"
    package.mkdir(parents=True, exist_ok=True)
    if editable.filename is not None:
        _write_contract_file(package, editable.filename, editable.text)
        module_name = editable.filename.removesuffix(".pyi").replace("/", ".")
        entry = package / "__init__.pyi"
        entry.write_text(f"from . import {module_name}\n", encoding="utf-8")
        return entry
    entry = package / ("contract.pyi" if native_language == "c" else "__init__.pyi")
    entry.write_text(f"{editable.text.rstrip()}\n", encoding="utf-8")
    return entry


def _materialize_direct_entry(
    package: Path,
    editable: EditableContract,
    generated: GeneratedContracts,
) -> Path:
    if generated.direct_contract is None:
        raise UsageError("This source cell did not generate an editable direct-declaration .pyi contract")
    entry = package / ("contract.pyi" if generated.language == "c" else "__init__.pyi")
    entry.write_text(f"{editable.text.rstrip()}\n", encoding="utf-8")
    return entry


def _materialize_module_entry(
    package: Path,
    editable: EditableContract,
    generated: GeneratedContracts,
    support_contracts: dict[str, str],
) -> Path:
    assert editable.filename is not None
    if editable.filename not in generated.module_contracts:
        raise UsageError(f"This source cell did not generate the editable module contract {editable.filename!r}")
    support_contracts[editable.filename] = editable.text
    module_name = editable.filename.removesuffix(".pyi").replace("/", ".")
    entry = package / "__init__.pyi"
    entry.write_text(f"from . import {module_name}\n", encoding="utf-8")
    return entry
