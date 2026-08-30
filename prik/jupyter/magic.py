"""Compile Fortran and C notebook cells through PRIK's public build API."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys
import sysconfig
from types import ModuleType

from filelock import FileLock
from IPython.core.error import UsageError
from IPython.core.magic import Magics, cell_magic, magics_class

from prik import __version__
from prik.jupyter import contracts as contract_cells
from prik.pipeline.build import (
    WrapperBuildResult,
    build_c_extension,
    build_fortran_extension,
    build_pyi_extension,
)
from prik.preprocessing import PreprocessingConfig


_BUILD_CONFIGURATION_SCHEMA_VERSION = 1
_BUILD_CACHE_RECORD_SCHEMA_VERSION = 2
_SOURCE_RECORD_SCHEMA_VERSION = 1
_CACHE_RECORD_NAME = "cell-build.json"
_SOURCE_RECORD_NAME = "source.json"


# Options whose value normally starts with a dash, which argparse would
# otherwise read as the next option rather than as this option's value. Only
# the flag groups are split, so only they may carry several flags at once.
_DASH_VALUE_OPTIONS = ("--compiler-arg",)
_DASH_VALUE_FLAG_GROUPS = (
    "--native-compile-flags",
    "--wrapper-fortran-flags",
    "--wrapper-c-flags",
)


class _MagicArgumentParser(argparse.ArgumentParser):
    """Raise an IPython usage error instead of terminating the kernel."""

    def error(self, message: str) -> None:
        raise UsageError(self._with_dash_value_hint(message))

    @staticmethod
    def _with_dash_value_hint(message: str) -> str:
        """Name the equals form when argparse read a flag value as an option."""
        if "expected one argument" not in message:
            return message
        group = next((name for name in _DASH_VALUE_FLAG_GROUPS if name in message), None)
        if group is not None:
            return (
                f"{message}; use the equals form for a dash-prefixed value ({group}=-O3) "
                f'and one quoted group for several flags ({group}="-O3 -march=native")'
            )
        option = next((name for name in _DASH_VALUE_OPTIONS if name in message), None)
        if option is None:
            return message
        return f"{message}; use the equals form for a dash-prefixed value ({option}=-fopenmp)"


@dataclass(frozen=True)
class _CellOptions:
    """Normalized build-affecting and execution-only magic options."""

    language: str
    compiler: str
    compiler_explicit: bool
    compiler_args: tuple[str, ...]
    native_compile_flags: tuple[str, ...]
    wrapper_fortran_flags: tuple[str, ...]
    wrapper_c_flags: tuple[str, ...]
    generate_pyi: bool
    force: bool
    verbose: bool


@dataclass(frozen=True)
class _PendingEditableCells:
    """Generated contracts awaiting terminal IPython's next-input prompt."""

    source_digest: str
    cells: tuple[str, ...]


@dataclass(frozen=True)
class _ManualNativeSources:
    """Existing native source paths supplied by one handwritten contract cell."""

    language: str
    paths: tuple[Path, ...]


def _argument_parser(
    magic_name: str,
    *,
    supports_pyi_generation: bool,
    supports_native_sources: bool = False,
) -> _MagicArgumentParser:
    parser = _MagicArgumentParser(
        prog=f"%%{magic_name}",
        add_help=False,
        description="Compile and publish one notebook cell through PRIK.",
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show this help and do not compile the cell")
    if supports_pyi_generation:
        parser.add_argument(
            "--pyi",
            action="store_true",
            help="Persist this source and insert editable semantic .pyi cells",
        )
    if supports_native_sources:
        parser.add_argument(
            "--native-fortran-sources",
            action="extend",
            nargs="+",
            default=[],
            metavar="PATH",
            help="Existing Fortran implementation sources for a handwritten contract",
        )
        parser.add_argument(
            "--native-c-sources",
            action="extend",
            nargs="+",
            default=[],
            metavar="PATH",
            help="Existing C implementation sources for a handwritten contract",
        )
    parser.add_argument("--compiler", help="Exact Fortran or C compiler executable")
    parser.add_argument(
        "--compiler-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Additional preprocessing argument; repeat as needed",
    )
    parser.add_argument(
        "--native-compile-flags",
        action="append",
        default=[],
        metavar="FLAGS",
        help="Quoted compiler flags for the selected native sources; repeat as needed",
    )
    parser.add_argument(
        "--wrapper-fortran-flags",
        action="append",
        default=[],
        metavar="FLAGS",
        help="Quoted compiler flags for generated Fortran bridge source",
    )
    parser.add_argument(
        "--wrapper-c-flags",
        action="append",
        default=[],
        metavar="FLAGS",
        help="Quoted compiler and link flags for generated C binding source",
    )
    parser.add_argument("--force", action="store_true", help="Recompile even when this exact cell is cached")
    parser.add_argument("--verbose", action="store_true", help="Print PRIK build commands or cache reuse")
    return parser


def _split_flag_groups(groups: list[str], *, option_name: str) -> tuple[str, ...]:
    flags: list[str] = []
    for group in groups:
        try:
            flags.extend(shlex.split(group))
        except ValueError as exc:
            raise UsageError(f"Invalid {option_name} value {group!r}: {exc}") from exc
    return tuple(flags)


def _options_from_namespace(
    parsed: argparse.Namespace,
    *,
    language: str,
    generate_pyi: bool,
) -> _CellOptions:
    """Normalize one successfully parsed magic invocation."""
    compiler = parsed.compiler or ("gfortran" if language == "fortran" else "cc")
    return _CellOptions(
        language=language,
        compiler=compiler,
        compiler_explicit=parsed.compiler is not None,
        compiler_args=tuple(parsed.compiler_arg),
        native_compile_flags=_split_flag_groups(
            parsed.native_compile_flags,
            option_name="--native-compile-flags",
        ),
        wrapper_fortran_flags=_split_flag_groups(
            parsed.wrapper_fortran_flags,
            option_name="--wrapper-fortran-flags",
        ),
        wrapper_c_flags=_split_flag_groups(
            parsed.wrapper_c_flags,
            option_name="--wrapper-c-flags",
        ),
        generate_pyi=generate_pyi,
        force=parsed.force,
        verbose=parsed.verbose,
    )


def _parse_arguments(line: str, parser: _MagicArgumentParser) -> argparse.Namespace | None:
    try:
        arguments = shlex.split(line)
    except ValueError as exc:
        raise UsageError(f"Invalid {parser.prog} arguments: {exc}") from exc
    if "-h" in arguments or "--help" in arguments:
        print(parser.format_help())
        return None
    return parser.parse_args(arguments)


def _parse_source_options(line: str, *, language: str) -> _CellOptions | None:
    parser = _argument_parser(language, supports_pyi_generation=True)
    parsed = _parse_arguments(line, parser)
    if parsed is None:
        return None
    if parsed.pyi and parsed.force:
        parser.error("--pyi only generates editable cells; do not pass --force")
    return _options_from_namespace(parsed, language=language, generate_pyi=parsed.pyi)


def _manual_native_sources(
    parsed: argparse.Namespace,
    parser: _MagicArgumentParser,
) -> _ManualNativeSources | None:
    """Resolve the one native language selected by handwritten-contract options."""
    fortran_values = tuple(parsed.native_fortran_sources)
    c_values = tuple(parsed.native_c_sources)
    if fortran_values and c_values:
        parser.error("%%pyi cannot mix --native-fortran-sources and --native-c-sources")
    values = fortran_values or c_values
    if not values:
        return None
    language = "fortran" if fortran_values else "c"
    paths: list[Path] = []
    for value in values:
        try:
            path = Path(value).expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise UsageError(f"Native source path {value!r} is unavailable: {exc}") from exc
        if not path.is_file():
            raise UsageError(f"Native source path {value!r} is not a file")
        paths.append(path)
    return _ManualNativeSources(language=language, paths=tuple(paths))


def _cell_digest(language: str, cell: str) -> str:
    """Return the documented digest of the language followed by exact cell text."""
    return hashlib.sha256(f"{language}{cell}".encode()).hexdigest()


def _default_cache_root() -> Path:
    """Return the persistent notebook cache root without creating it."""
    if root := os.getenv("PRIK_CACHE_DIR"):
        return Path(root) / "jupyter"
    if root := os.getenv("XDG_CACHE_HOME"):
        return Path(root) / "prik" / "jupyter"
    return Path.home() / ".cache" / "prik" / "jupyter"


def _source_path(entry_dir: Path, language: str) -> Path:
    """Return the native cell path owned by one source-digest entry."""
    return entry_dir / ("cell.f90" if language == "fortran" else "cell.c")


def _editable_magic_command(options: _CellOptions) -> str:
    """Render the readable build options copied into an inserted contract cell."""
    arguments = ["%%pyi"]
    if options.compiler_explicit:
        arguments.extend(("--compiler", options.compiler))
    arguments.extend(f"--compiler-arg={value}" for value in options.compiler_args)
    flag_groups = (
        ("--native-compile-flags", options.native_compile_flags),
        ("--wrapper-fortran-flags", options.wrapper_fortran_flags),
        ("--wrapper-c-flags", options.wrapper_c_flags),
    )
    for option_name, flags in flag_groups:
        if flags:
            arguments.append(f"{option_name}={shlex.join(flags)}")
    if options.verbose:
        arguments.append("--verbose")
    return shlex.join(arguments)


def _build_configuration(options: _CellOptions) -> dict[str, object]:
    """Return the compatibility facts validated inside one source digest entry."""
    return {
        "schema_version": _BUILD_CONFIGURATION_SCHEMA_VERSION,
        "prik_version": __version__,
        "python_cache_tag": sys.implementation.cache_tag,
        "python_soabi": sysconfig.get_config_var("SOABI"),
        "language": options.language,
        "compiler": options.compiler,
        "compiler_args": list(options.compiler_args),
        "native_compile_flags": list(options.native_compile_flags),
        "wrapper_fortran_flags": list(options.wrapper_fortran_flags),
        "wrapper_c_flags": list(options.wrapper_c_flags),
    }


def _file_sha256(path: Path) -> str:
    """Hash one explicit native source without retaining its contents in memory."""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise UsageError(f"Cannot read native source {path}: {exc}") from exc
    return digest.hexdigest()


def _build_fingerprint(
    options: _CellOptions,
    *,
    native_sources: tuple[Path, ...] = (),
) -> str:
    configuration = _build_configuration(options)
    if native_sources:
        configuration["native_sources"] = [{"path": str(path), "sha256": _file_sha256(path)} for path in native_sources]
    payload = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _extension_module_name(language: str, digest: str, fingerprint: str, generation: int) -> str:
    language_marker = "f" if language == "fortran" else "c"
    return f"_prik_{language_marker}_{digest[:12]}_{fingerprint[:8]}_{generation}"


def _read_cache_record(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _write_source_record(path: Path, *, digest: str, language: str) -> None:
    """Persist the language identity needed by a later `%%pyi` cell."""
    record = {
        "schema_version": _SOURCE_RECORD_SCHEMA_VERSION,
        "source_digest": digest,
        "language": language,
    }
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(f"{json.dumps(record, sort_keys=True, indent=2)}\n", encoding="utf-8")
    temporary.replace(path)


def _source_language(path: Path, *, digest: str) -> str:
    """Load the native language owned by one generated source-cache entry."""
    record = _read_cache_record(path)
    if record is None or record.get("schema_version") != _SOURCE_RECORD_SCHEMA_VERSION:
        raise UsageError(
            "The native source for this editable .pyi is unavailable; "
            "execute its %%fortran --pyi or %%c --pyi source cell again"
        )
    language = record.get("language")
    if record.get("source_digest") != digest or language not in {"fortran", "c"}:
        raise UsageError(
            "The cached native source identity does not match this editable .pyi; "
            "execute its %%fortran --pyi or %%c --pyi source cell again"
        )
    assert isinstance(language, str)
    return language


def _generation(record: dict[str, object] | None) -> int:
    value = None if record is None else record.get("generation")
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value < 1_000_000 else -1


def _compatible_generation(
    record: dict[str, object] | None,
    *,
    digest: str,
    fingerprint: str,
) -> int | None:
    if record is None or record.get("schema_version") != _BUILD_CACHE_RECORD_SCHEMA_VERSION:
        return None
    if record.get("digest") != digest or record.get("build_fingerprint") != fingerprint:
        return None
    generation = _generation(record)
    return generation if generation >= 0 else None


def _recorded_shared_library(record: dict[str, object], *, entry_dir: Path, module_name: str) -> Path | None:
    name = record.get("shared_library")
    if not isinstance(name, str) or Path(name).name != name or not name.startswith(f"{module_name}."):
        return None
    shared_library = entry_dir / "build" / name
    return shared_library if shared_library.is_file() else None


def _cached_result(
    record: dict[str, object] | None,
    *,
    entry_dir: Path,
    sources: tuple[Path, ...],
    digest: str,
    fingerprint: str,
    language: str,
) -> WrapperBuildResult | None:
    generation = _compatible_generation(record, digest=digest, fingerprint=fingerprint)
    if record is None or generation is None:
        return None
    module_name = _extension_module_name(language, digest, fingerprint, generation)
    if record.get("module_name") != module_name:
        return None
    shared_library = _recorded_shared_library(record, entry_dir=entry_dir, module_name=module_name)
    if shared_library is None:
        return None
    return WrapperBuildResult(
        sources=sources,
        module_name=module_name,
        output_dir=entry_dir / "build",
        shared_library=shared_library,
        build_makefile=None,
        compiled=True,
        generated_sources=(),
        generated_files=(),
    )


def _write_cache_record(
    path: Path,
    *,
    digest: str,
    fingerprint: str,
    generation: int,
    result: WrapperBuildResult,
) -> None:
    record = {
        "schema_version": _BUILD_CACHE_RECORD_SCHEMA_VERSION,
        "digest": digest,
        "build_fingerprint": fingerprint,
        "generation": generation,
        "module_name": result.module_name,
        "shared_library": result.shared_library.name,
    }
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(f"{json.dumps(record, sort_keys=True, indent=2)}\n", encoding="utf-8")
    temporary.replace(path)


def _build_cell(
    source: Path,
    *,
    output_dir: Path,
    output_name: str,
    options: _CellOptions,
) -> WrapperBuildResult:
    preprocessing = PreprocessingConfig(
        mode="compiler",
        compiler=options.compiler,
        compiler_args=list(options.compiler_args),
    )
    common = {
        "output_dir": output_dir,
        "output_name": output_name,
        "preprocessing": preprocessing,
        "verbose": options.verbose,
        "wrapper_fortran_flags": options.wrapper_fortran_flags,
        "wrapper_c_flags": options.wrapper_c_flags,
    }
    if options.language == "fortran":
        return build_fortran_extension(
            source,
            native_fortran_flags=options.native_compile_flags,
            **common,
        )
    return build_c_extension(
        source,
        input_c_compiler=options.compiler,
        native_c_flags=options.native_compile_flags,
        **common,
    )


def _build_editable_contract(
    contract: Path,
    native_sources: tuple[Path, ...],
    *,
    output_dir: Path,
    output_name: str,
    options: _CellOptions,
) -> WrapperBuildResult:
    """Build one semantic contract against its selected native sources."""
    common = {
        "output_dir": output_dir,
        "output_name": output_name,
        "native_language": options.language,
        "verbose": options.verbose,
        "wrapper_fortran_flags": options.wrapper_fortran_flags,
        "wrapper_c_flags": options.wrapper_c_flags,
    }
    if options.language == "fortran":
        return build_pyi_extension(
            contract,
            input_compiler=options.compiler,
            native_fortran_sources=native_sources,
            native_fortran_flags=options.native_compile_flags,
            **common,
        )
    return build_pyi_extension(
        contract,
        input_c_compiler=options.compiler,
        native_c_sources=native_sources,
        native_c_flags=options.native_compile_flags,
        **common,
    )


def _editable_pyi_contract(
    cell: str,
    manual_sources: _ManualNativeSources | None,
) -> contract_cells.EditableContract:
    """Resolve generated metadata or construct one handwritten cell contract."""
    if not cell.strip():
        raise UsageError("%%pyi requires a non-empty semantic .pyi cell")
    editable = contract_cells.parse_editable_contract(cell)
    if editable is None:
        if manual_sources is None:
            raise UsageError(
                "%%pyi requires generated source metadata or explicit --native-fortran-sources/--native-c-sources"
            )
        return contract_cells.EditableContract(
            source_digest=None,
            filename=None,
            text=cell,
        )
    if editable.source_digest is not None and manual_sources is not None:
        raise UsageError("%%pyi cannot combine generated source-sha256 metadata with explicit native sources")
    if editable.source_digest is None and manual_sources is None:
        raise UsageError("A handwritten %%pyi cell requires --native-fortran-sources or --native-c-sources")
    return editable


def _pyi_native_language(
    editable: contract_cells.EditableContract,
    manual_sources: _ManualNativeSources | None,
    *,
    cache_root: Path,
) -> str:
    """Return the explicit manual language or recover one generated language."""
    if manual_sources is not None:
        return manual_sources.language
    source_digest = editable.source_digest
    assert source_digest is not None
    source_entry_dir = cache_root / source_digest
    return _source_language(
        source_entry_dir / _SOURCE_RECORD_NAME,
        digest=source_digest,
    )


def _public_bindings(module: ModuleType) -> dict[str, object]:
    """Return public root declarations and namespaces named as the notebook shows them.

    A cell's extension is imported under a private cache module name, which
    would otherwise surface in ``repr()``, ``help()``, and ``__module__``. The
    published objects are restated under the names the user actually binds,
    leaving the private name to ``sys.modules`` alone.
    """
    bindings = {name: value for name, value in vars(module).items() if not name.startswith("_")}
    for name, value in bindings.items():
        if isinstance(value, ModuleType):
            _restate_namespace(value, name)
        else:
            # Published directly into the session, so it has no public owner.
            _set_owner_module(value, None)
    return bindings


def _restate_namespace(namespace: ModuleType, public_name: str) -> None:
    """Rename one published namespace and every member it owns."""
    namespace.__name__ = public_name
    # A namespace carrying module variables is an instance of a generated heap
    # type whose name also embeds the private root.
    _set_owner_module(type(namespace), public_name)
    for member_name, member in vars(namespace).items():
        if member_name.startswith("_"):
            continue
        if isinstance(member, ModuleType):
            _restate_namespace(member, f"{public_name}.{member_name}")
        else:
            _set_owner_module(member, public_name)


def _set_owner_module(value: object, owner: str | None) -> None:
    """Set one object's owning-module name, ignoring an immutable target."""
    with suppress(AttributeError, TypeError):
        value.__module__ = owner


@magics_class
class PrikMagics(Magics):
    """Own PRIK's source, contract, cache, import, and publication magics."""

    magic_names = ("fortran", "c", "pyi")
    owns_prik_cell_magics = True

    def __init__(self, shell=None, *, cache_dir: str | Path | None = None) -> None:
        super().__init__(shell=shell)
        self.cache_root = Path(cache_dir) if cache_dir is not None else _default_cache_root()
        self._pending_editable_cells: _PendingEditableCells | None = None

    @cell_magic
    def fortran(self, line: str, cell: str) -> None:
        """Compile Fortran source or generate its editable contract cells."""
        self._run_source_magic(line, cell, language="fortran")

    @cell_magic
    def c(self, line: str, cell: str) -> None:
        """Compile C source or generate its editable contract cell."""
        self._run_source_magic(line, cell, language="c")

    @cell_magic
    def pyi(self, line: str, cell: str) -> None:
        """Compile one generated or handwritten semantic contract."""
        parser = _argument_parser(
            "pyi",
            supports_pyi_generation=False,
            supports_native_sources=True,
        )
        parsed = _parse_arguments(line, parser)
        if parsed is None:
            return
        manual_sources = _manual_native_sources(parsed, parser)
        editable = _editable_pyi_contract(cell, manual_sources)
        language = _pyi_native_language(editable, manual_sources, cache_root=self.cache_root)
        options = _options_from_namespace(parsed, language=language, generate_pyi=False)
        if manual_sources is None:
            module, reused = self._load_or_build_editable(cell, editable, options)
        else:
            module, reused = self._load_or_build_handwritten(
                cell,
                editable,
                manual_sources,
                options,
            )
        self._publish(module, reused=reused, cell=cell, options=options)
        if editable.source_digest is not None:
            self._present_next_editable_cell(editable.source_digest)

    def _run_source_magic(self, line: str, cell: str, *, language: str) -> None:
        """Execute the shared native-source workflow selected by its magic name."""
        options = _parse_source_options(line, language=language)
        if options is None:
            return
        if not cell.strip():
            raise UsageError(f"%%{language} requires a non-empty {language.capitalize()} source cell")

        if options.generate_pyi:
            self._generate_pyi_cells(cell, options)
            return
        module, reused = self._load_or_build_source(cell, options)
        self._publish(module, reused=reused, cell=cell, options=options)

    def _publish(self, module: ModuleType, *, reused: bool, cell: str, options: _CellOptions) -> None:
        """Publish one built extension's public API into the notebook namespace."""
        if reused and options.verbose:
            print(f">> Reuse cached PRIK cell: {_cell_digest(options.language, cell)}")
        self.shell.push(_public_bindings(module))

    def _generate_pyi_cells(self, cell: str, options: _CellOptions) -> None:
        source_digest = _cell_digest(options.language, cell)
        fingerprint = _build_fingerprint(options)
        entry_dir = self.cache_root / source_digest
        source = _source_path(entry_dir, options.language)
        contracts_path = contract_cells.generated_contract_record_path(entry_dir, fingerprint)

        self.cache_root.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.cache_root / f"{source_digest}.lock")):
            entry_dir.mkdir(parents=True, exist_ok=True)
            source.write_text(cell, encoding="utf-8")
            contracts = contract_cells.generate_contracts_from_source(
                source,
                source_digest=source_digest,
                options=options,
            )
            contract_cells.write_generated_contracts(contracts_path, contracts)
            _write_source_record(
                entry_dir / _SOURCE_RECORD_NAME,
                digest=source_digest,
                language=options.language,
            )

        cells = contract_cells.generated_editable_cells(
            contracts,
            magic_command=_editable_magic_command(options),
        )
        remaining = contract_cells.insert_editable_cells(self.shell, cells)
        self._pending_editable_cells = (
            _PendingEditableCells(source_digest=source_digest, cells=remaining) if remaining else None
        )

    def _present_next_editable_cell(self, source_digest: str) -> None:
        """Advance one matching terminal-IPython editable-contract queue."""
        pending = self._pending_editable_cells
        if pending is None or pending.source_digest != source_digest:
            return
        next_cell, *remaining = pending.cells
        contract_cells.insert_editable_cells(self.shell, [next_cell])
        self._pending_editable_cells = (
            _PendingEditableCells(source_digest=source_digest, cells=tuple(remaining)) if remaining else None
        )

    def _load_or_build_source(self, cell: str, options: _CellOptions) -> tuple[ModuleType, bool]:
        digest = _cell_digest(options.language, cell)
        fingerprint = _build_fingerprint(options)
        entry_dir = self.cache_root / digest
        source = _source_path(entry_dir, options.language)

        def build(build_dir: Path, module_name: str) -> WrapperBuildResult:
            source.write_text(cell, encoding="utf-8")
            return _build_cell(
                source,
                output_dir=build_dir,
                output_name=module_name,
                options=options,
            )

        return self._load_or_build_cached(
            digest=digest,
            fingerprint=fingerprint,
            sources=(source,),
            options=options,
            build=build,
        )

    def _load_or_build_editable(
        self,
        cell: str,
        editable: contract_cells.EditableContract,
        options: _CellOptions,
    ) -> tuple[ModuleType, bool]:
        digest = _cell_digest(options.language, cell)
        fingerprint = _build_fingerprint(options)
        source_digest = editable.source_digest
        assert source_digest is not None
        source_entry_dir = self.cache_root / source_digest
        source = _source_path(source_entry_dir, options.language)
        contracts_path = contract_cells.generated_contract_record_path(source_entry_dir, fingerprint)

        self.cache_root.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.cache_root / f"{source_digest}.lock")):
            try:
                source_text = source.read_text(encoding="utf-8")
            except OSError as exc:
                raise UsageError(
                    "The native source for this editable .pyi is unavailable; "
                    "execute its %%fortran --pyi or %%c --pyi source cell again"
                ) from exc
            if _cell_digest(options.language, source_text) != source_digest:
                raise UsageError(
                    "The cached native source does not match this editable .pyi; "
                    "execute its %%fortran --pyi or %%c --pyi source cell again"
                )
            generated = contract_cells.read_generated_contracts(
                contracts_path,
                language=options.language,
                source_digest=source_digest,
            )

        def build(build_dir: Path, module_name: str) -> WrapperBuildResult:
            entry_dir = build_dir.parent
            contract = contract_cells.materialize_editable_contract(entry_dir, editable, generated)
            return _build_editable_contract(
                contract,
                (source,),
                output_dir=build_dir,
                output_name=module_name,
                options=options,
            )

        return self._load_or_build_cached(
            digest=digest,
            fingerprint=fingerprint,
            sources=(source,),
            options=options,
            build=build,
        )

    def _load_or_build_handwritten(
        self,
        cell: str,
        editable: contract_cells.EditableContract,
        native_sources: _ManualNativeSources,
        options: _CellOptions,
    ) -> tuple[ModuleType, bool]:
        """Build one independent handwritten contract against existing files."""
        digest = _cell_digest(options.language, cell)
        fingerprint = _build_fingerprint(options, native_sources=native_sources.paths)

        def build(build_dir: Path, module_name: str) -> WrapperBuildResult:
            contract = contract_cells.materialize_handwritten_contract(
                build_dir.parent,
                editable,
                native_language=options.language,
            )
            return _build_editable_contract(
                contract,
                native_sources.paths,
                output_dir=build_dir,
                output_name=module_name,
                options=options,
            )

        return self._load_or_build_cached(
            digest=digest,
            fingerprint=fingerprint,
            sources=native_sources.paths,
            options=options,
            build=build,
        )

    def _load_or_build_cached(
        self,
        *,
        digest: str,
        fingerprint: str,
        sources: tuple[Path, ...],
        options: _CellOptions,
        build: Callable[[Path, str], WrapperBuildResult],
    ) -> tuple[ModuleType, bool]:
        """Reuse one validated notebook artifact or execute its selected build path."""
        entry_dir = self.cache_root / digest
        record_path = entry_dir / _CACHE_RECORD_NAME
        self.cache_root.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.cache_root / f"{digest}.lock")):
            entry_dir.mkdir(parents=True, exist_ok=True)
            record = _read_cache_record(record_path)
            if not options.force:
                cached = _cached_result(
                    record,
                    entry_dir=entry_dir,
                    sources=sources,
                    digest=digest,
                    fingerprint=fingerprint,
                    language=options.language,
                )
                if cached is not None:
                    return cached.import_module(), True

            generation = _generation(record) + 1
            module_name = _extension_module_name(options.language, digest, fingerprint, generation)
            while module_name in sys.modules:
                generation += 1
                module_name = _extension_module_name(options.language, digest, fingerprint, generation)
            result = build(entry_dir / "build", module_name)
            module = result.import_module()
            _write_cache_record(
                record_path,
                digest=digest,
                fingerprint=fingerprint,
                generation=generation,
                result=result,
            )
            return module, False


__all__ = ("PrikMagics",)
