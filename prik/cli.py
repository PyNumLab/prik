from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from pathlib import Path

from prik import __version__
from prik.parsers.c.cli import attach_preprocessing_recipe, expand_c_paths, format_c_report, parse_c_report
from prik.parsers.c.models import CParseError
from prik.parsers.c.parser import CParser
from prik.parsers.fortran.cli import _format_report
from prik.parsers.fortran.models import FortranParseError
from prik.parsers.fortran.parser import FortranParser
from prik.semantics.c2ir import c_project_to_semantic_modules, select_c_export_functions
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules
from prik.preprocessing.probes.c_types import (
    CStandardTypeProbeError,
    probe_c_standard_types_cached,
)
from prik.preprocessing.probes.fortran_types import (
    FortranTypeProbeReport,
    probe_fortran_type_expressions_cached,
)
from prik.pipeline.type_mapping_report import (
    c_type_mapping_report,
    expression_probe_markdown,
    fortran_type_mapping_report,
    type_mapping_markdown,
)
from prik.preprocessing import (
    PreprocessingConfig,
    PreprocessingError,
    run_compiler_preprocessor_with_recipe,
    validate_macro_name,
)

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FORTRAN_SOURCE_SUFFIXES = {".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08"}
_C_SOURCE_SUFFIXES = {".c", ".h", ".i"}
_SOURCE_SUFFIXES_BY_LANGUAGE = {
    "fortran": _FORTRAN_SOURCE_SUFFIXES,
    "c": _C_SOURCE_SUFFIXES,
}
_HELP_DIVIDER = "------------------------------ EXAMPLES ------------------------------"
_TOP_LEVEL_USAGE = (
    "%(prog)s INPUT [INPUT ...] [BUILD OPTIONS]\n"
    "       %(prog)s {parse,semantics,generate,probe} [OPTIONS] ...\n"
    "       %(prog)s --version"
)
_BUILD_USAGE = (
    "%(prog)s INPUT [INPUT ...]\n"
    "       [OUTPUT OPTIONS] [COMPILER OPTIONS] [WRAPPER OPTIONS]\n"
    "       [NATIVE OPTIONS] [DIAGNOSTIC OPTIONS]\n"
    "       %(prog)s --build-manifest PATH [MANIFEST OVERRIDES]"
)
_PARSE_USAGE = "%(prog)s INPUT [INPUT ...] [OPTIONS]"
_SEMANTICS_USAGE = "%(prog)s INPUT [INPUT ...] [OPTIONS]"
_GENERATE_USAGE = (
    "%(prog)s (--pyi | --sources | --makefile)\n"
    "                                INPUT [INPUT ...] [OPTIONS]\n"
    "       %(prog)s (--sources | --makefile)\n"
    "                                --build-manifest PATH [OVERRIDES]"
)
_PROBE_USAGE = "%(prog)s --language {fortran,c} --compiler COMPILER [OPTIONS]"
_POINTS_EXAMPLE_HELP = (
    "  See the PRIK homepage for the points.f90 source and generated Python API:\n"
    "    https://pynumlab.github.io/prik/#see-it-in-action\n"
)
_CLI_HELP_DESCRIPTION = (
    "Build Python extensions from Fortran and inspect native interface artifacts.\n\n"
    "commands:\n"
    "  parse       Inspect source declarations and parser facts\n"
    "  semantics   Convert source code to language-neutral semantic IR\n"
    "  generate    Generate contracts or wrapper build files\n"
    "  probe       Probe compiler-target datatype and ABI facts"
)
_CLI_HELP_EPILOG = (
    f"{_HELP_DIVIDER}\n\n"
    "  Basic wrapper build:\n"
    "    python3 -m prik points.f90\n"
    "\n"
    "  Name the Python extension:\n"
    "    python3 -m prik points.f90 --out geometry\n\n"
    "  Generate an editable semantic contract:\n"
    "    python3 -m prik generate --pyi points.f90 --out contracts\n\n"
    f"{_POINTS_EXAMPLE_HELP}\n"
    "  More help:\n"
    "    python3 -m prik --help-build\n"
    "    python3 -m prik parse --help\n"
    "    python3 -m prik semantics --help\n"
    "    python3 -m prik generate --help\n"
    "    python3 -m prik probe --help\n\n"
    "Run `python3 -m prik --help-build` for the full list of build options.\n"
    "Run a subcommand with `--help` for its command-specific options."
)
_BUILD_HELP_EPILOG = (
    f"{_HELP_DIVIDER}\n\n"
    "  Basic wrapper build:\n"
    "    python3 -m prik points.f90\n"
    "\n"
    "  Name the Python extension:\n"
    "    python3 -m prik points.f90 --out geometry\n"
    "\n"
    "  Build from a semantic contract:\n"
    "    python3 -m prik contracts/__init__.pyi --native-fortran-sources points.f90 \\\n"
    "      --out geometry --out-dir build/geometry_from_pyi\n\n"
    "  Replay a build manifest:\n"
    "    python3 -m prik --build-manifest build/prik-build.json\n\n"
    f"{_POINTS_EXAMPLE_HELP}"
    "  See docs/user/reference/cli-commands.md for all build options.\n\n"
    "  Manifest overrides: --out, --compiler, -I/--include-dir, --jobs, --json, --verbose,\n"
    "    --no-color, and --debug."
)
_PARSE_HELP_EPILOG = (
    f"{_HELP_DIVIDER}\n\n"
    "  Basic Fortran inspection:\n"
    "    python3 -m prik parse points.f90\n"
    "\n"
    "  Detailed Fortran report:\n"
    "    python3 -m prik parse points.f90 --show-vars --print-limit 50\n"
    "\n"
    "  C header as JSON:\n"
    "    python3 -m prik parse path/to/api.h --language c --json\n\n"
    f"{_POINTS_EXAMPLE_HELP}"
)
_SEMANTICS_HELP_EPILOG = (
    f"{_HELP_DIVIDER}\n\n"
    "  Basic Fortran conversion:\n"
    "    python3 -m prik semantics points.f90\n"
    "\n"
    "  C header:\n"
    "    python3 -m prik semantics path/to/api.h --language c\n"
    "\n"
    "  Save semantic IR:\n"
    "    python3 -m prik semantics points.f90 --out semantics.json\n\n"
    f"{_POINTS_EXAMPLE_HELP}"
)
_GENERATE_HELP_EPILOG = (
    f"{_HELP_DIVIDER}\n\n"
    "  Editable semantic contract:\n"
    "    python3 -m prik generate --pyi points.f90 --out contracts\n"
    "\n"
    "  Wrapper sources only:\n"
    "    python3 -m prik generate --sources points.f90 --out-dir build\n"
    "\n"
    "  Reproducible Makefile build:\n"
    "    python3 -m prik generate --makefile points.f90 --out-dir build\n\n"
    f"{_POINTS_EXAMPLE_HELP}"
)
_PROBE_HELP_EPILOG = (
    f"{_HELP_DIVIDER}\n\n"
    "  Basic target probes:\n"
    "    python3 -m prik probe --language fortran --compiler gfortran-13\n"
    "    python3 -m prik probe --language c --compiler gcc-13\n"
    "\n"
    "  Human-readable mapping table:\n"
    "    python3 -m prik probe --language fortran --compiler gfortran-13 \\\n"
    "      --format markdown\n"
    "\n"
    "  Measure specific Fortran expressions in either format:\n"
    "    python3 -m prik probe --language fortran --compiler gfortran-13 \\\n"
    '      --expr "selected_real_kind(15,307)" --format markdown\n'
    "\n"
    "  Probe flags that change default kinds:\n"
    "    python3 -m prik probe --language fortran --compiler gfortran-13 \\\n"
    "      --compiler-arg=-fdefault-real-8 --compiler-arg=-fdefault-integer-8\n"
    "\n"
    "  Cross-target probe:\n"
    "    python3 -m prik probe --language c --compiler aarch64-linux-gnu-gcc \\\n"
    "      --runner qemu-aarch64"
)


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _diagnostic_color_enabled(*, disabled: bool) -> bool:
    if disabled:
        return False
    return "NO_COLOR" not in os.environ


def _to_dict_no_parent(obj):
    if is_dataclass(obj):
        out = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            if f.name == "parent" and not isinstance(value, str | type(None)):
                continue
            out[f.name] = _to_dict_no_parent(value)
        return out
    if isinstance(obj, list):
        return [_to_dict_no_parent(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_dict_no_parent(v) for k, v in obj.items()}
    return obj


def _collect_extensions(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.suffix.lower() in _FORTRAN_SOURCE_SUFFIXES)


def _collect_pyi_extensions(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*.pyi") if p.is_file())


def _expand_paths(paths: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            expanded.extend(_collect_extensions(p))
        else:
            expanded.append(p)
    return list(dict.fromkeys(expanded))


def _expand_pyi_paths(paths: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            expanded.extend(_collect_pyi_extensions(p))
        elif p.suffix.lower() == ".pyi":
            expanded.append(p)
    return sorted(set(expanded))


def _resolve_language(
    paths: list[str],
    requested: str | None,
    parser: argparse.ArgumentParser,
) -> str:
    def language_for_suffix(suffix: str) -> str | None:
        return next(
            (language for language, suffixes in _SOURCE_SUFFIXES_BY_LANGUAGE.items() if suffix in suffixes),
            None,
        )

    if requested is not None:
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                continue
            suffix = path.suffix.lower()
            detected = language_for_suffix(suffix)
            if detected is not None and detected != requested:
                parser.error(
                    f"{detected.capitalize()} input {path} is incompatible with --language {requested}; "
                    f"pass --language {detected}. Use --help for examples."
                )
        return requested

    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            parser.error(
                f"Input directory {path} requires an explicit frontend; "
                "pass --language fortran or --language c. Use --help for examples."
            )

        suffix = path.suffix.lower()
        if suffix in _C_SOURCE_SUFFIXES:
            parser.error(f"C input {path} requires explicit --language c. Use --help for examples.")
        if suffix not in _FORTRAN_SOURCE_SUFFIXES and suffix != ".pyi":
            parser.error(
                f"Cannot determine the input language for {path}; "
                "pass --language fortran or --language c. Use --help for examples."
            )
    return "fortran"


def _fortran_source_for_path(
    path: Path,
    preprocessing: PreprocessingConfig,
) -> tuple[str, dict[str, object] | None]:
    if preprocessing.uses_compiler:
        source, recipe = run_compiler_preprocessor_with_recipe(
            path,
            language="fortran",
            config=preprocessing,
        )
        return source, recipe.to_dict()
    return (
        path.read_text(encoding="utf-8"),
        preprocessing.fortran_internal_recipe(path),
    )


def _c_source_loader(preprocessing: PreprocessingConfig):
    if not preprocessing.uses_compiler:
        return None

    def load(path: Path) -> tuple[str, dict[str, object]]:
        source, recipe = run_compiler_preprocessor_with_recipe(
            path,
            language="c",
            config=preprocessing,
        )
        return source, recipe.to_dict()

    return load


def _c_parser_preprocessing_mode(preprocessing: PreprocessingConfig) -> str:
    return "compiler" if preprocessing.uses_compiler else "raw"


def _parse_c_path(
    parser: CParser,
    path: Path,
    preprocessing: PreprocessingConfig,
):
    source_loader = _c_source_loader(preprocessing)
    if source_loader is None:
        return parser.parse_file(
            path,
            filename=str(path),
            include_dirs=preprocessing.include_dirs,
            preprocessing=_c_parser_preprocessing_mode(preprocessing),
        )

    source, preprocessing_recipe = source_loader(path)
    parsed = parser.parse_file(
        source,
        filename=str(path),
        include_dirs=preprocessing.include_dirs,
        preprocessing=_c_parser_preprocessing_mode(preprocessing),
    )
    attach_preprocessing_recipe(parsed, preprocessing_recipe)
    return parsed


def _parse_c_project(
    paths: list[str],
    preprocessing: PreprocessingConfig,
):
    parser = CParser()
    parsed_files = {str(path): _parse_c_path(parser, path, preprocessing) for path in expand_c_paths(paths)}
    return parser._assemble_project(parsed_files)


def _parse_report(paths: list[str], preprocessing: PreprocessingConfig | None = None) -> dict[str, dict]:
    preprocessing = preprocessing or PreprocessingConfig()
    out: dict[str, dict] = {}
    parser = FortranParser()
    for p in _expand_paths(paths):
        code, preprocessing_recipe = _fortran_source_for_path(p, preprocessing)
        parsed = parser.parse_file(code, filename=str(p))
        payload = {
            "signatures": [_to_dict_no_parent(s) for s in parsed.procedures],
            "types": [_to_dict_no_parent(t) for t in parsed.derived_types],
            "modules": [_to_dict_no_parent(m) for m in parsed.modules],
            "submodules": [_to_dict_no_parent(m) for m in parsed.submodules],
            "programs": [_to_dict_no_parent(m) for m in parsed.programs],
            "block_data": [_to_dict_no_parent(m) for m in parsed.block_data_units],
        }
        if preprocessing_recipe is not None:
            payload["preprocessing_recipe"] = preprocessing_recipe
        out[str(p)] = payload
    return out


def _convert_c_project(
    project,
    *,
    c_standard_type_report: dict[str, object] | None,
    export_symbols: tuple[str, ...] | None = None,
):
    modules = (
        c_project_to_semantic_modules(project)
        if c_standard_type_report is None
        else c_project_to_semantic_modules(project, standard_type_report=c_standard_type_report)
    )
    return modules if export_symbols is None else select_c_export_functions(modules, export_symbols)


def _c_standard_type_report(
    preprocessing: PreprocessingConfig,
) -> dict[str, object] | None:
    """Probe target C ABI facts used internally by semantic conversion."""
    if not isinstance(preprocessing, PreprocessingConfig) or not preprocessing.compiler:
        return None
    if preprocessing.compile_commands or preprocessing.command_template:
        raise CStandardTypeProbeError(
            "automatic C ABI probing requires a direct compiler configuration; "
            "select one with --compiler COMPILER and pass target flags with --compiler-arg"
        )
    return probe_c_standard_types_cached(preprocessing).to_dict()


def _fortran_probe_options(
    *,
    report: FortranTypeProbeReport | None,
    runner: list[str] | None,
    cache_dir: str | None,
    refresh: bool,
) -> dict[str, object]:
    options: dict[str, object] = {}
    if report is not None:
        options["report"] = report
    if runner is not None:
        options["runner"] = runner
    if cache_dir is not None:
        options["cache_dir"] = cache_dir
    if refresh:
        options["refresh"] = True
    return options


@dataclass(frozen=True)
class _SemanticPipelineContext:
    paths: list[str]
    source_paths: tuple[Path, ...]
    preprocessing: PreprocessingConfig
    c_standard_type_report: dict[str, object] | None = None
    fortran_type_report: FortranTypeProbeReport | None = None
    fortran_type_probe_runner: list[str] | None = None
    fortran_type_probe_cache_dir: str | None = None
    refresh_fortran_type_probe: bool = False
    assume_intent_in_scalars: bool = False
    export_symbols: tuple[str, ...] | None = None


@dataclass(frozen=True)
class _ParsedSemanticSources:
    source_paths: tuple[Path, ...]
    parsed: object


@dataclass(frozen=True)
class _SourceSemanticPipeline:
    parser: Callable[[_SemanticPipelineContext], _ParsedSemanticSources]
    converter_to_ir: Callable[[_ParsedSemanticSources, _SemanticPipelineContext], list[tuple[Path, list[object]]]]


def _source_paths_for_semantic_pipeline(
    paths: list[str],
    *,
    language: str,
) -> tuple[Path, ...]:
    expanded = expand_c_paths(paths) if language == "c" else _expand_paths(paths)
    return tuple(path for path in expanded if path.suffix.lower() != ".pyi")


def _converted_semantic_files(
    paths: list[str],
    preprocessing: PreprocessingConfig,
    *,
    language: str,
    c_standard_type_report: dict[str, object] | None = None,
    fortran_type_report: FortranTypeProbeReport | None = None,
    fortran_type_probe_runner: list[str] | None = None,
    fortran_type_probe_cache_dir: str | None = None,
    refresh_fortran_type_probe: bool = False,
    assume_intent_in_scalars: bool = False,
    export_symbols: tuple[str, ...] | None = None,
) -> list[tuple[Path, list[object]]]:
    context = _SemanticPipelineContext(
        paths=paths,
        source_paths=_source_paths_for_semantic_pipeline(
            paths,
            language=language,
        ),
        preprocessing=preprocessing,
        c_standard_type_report=c_standard_type_report,
        fortran_type_report=fortran_type_report,
        fortran_type_probe_runner=fortran_type_probe_runner,
        fortran_type_probe_cache_dir=fortran_type_probe_cache_dir,
        refresh_fortran_type_probe=refresh_fortran_type_probe,
        assume_intent_in_scalars=assume_intent_in_scalars,
        export_symbols=export_symbols,
    )
    pipeline = _SOURCE_SEMANTIC_PIPELINES[language]
    parsed = pipeline.parser(context)
    return pipeline.converter_to_ir(parsed, context)


def _semantic_report(
    paths: list[str],
    preprocessing: PreprocessingConfig | None = None,
    *,
    language: str = "fortran",
    c_standard_type_report: dict[str, object] | None = None,
    fortran_type_report: FortranTypeProbeReport | None = None,
    fortran_type_probe_runner: list[str] | None = None,
    fortran_type_probe_cache_dir: str | None = None,
    refresh_fortran_type_probe: bool = False,
    assume_intent_in_scalars: bool = False,
    export_symbols: tuple[str, ...] | None = None,
) -> dict[str, dict]:
    preprocessing = preprocessing or PreprocessingConfig()
    converted_files = _converted_semantic_files(
        paths,
        preprocessing,
        language=language,
        c_standard_type_report=c_standard_type_report,
        fortran_type_report=fortran_type_report,
        fortran_type_probe_runner=fortran_type_probe_runner,
        fortran_type_probe_cache_dir=fortran_type_probe_cache_dir,
        refresh_fortran_type_probe=refresh_fortran_type_probe,
        assume_intent_in_scalars=assume_intent_in_scalars,
        export_symbols=export_symbols,
    )
    return _semantic_payload_for_converted_files(converted_files)


def _parse_fortran_source_files(
    paths: list[Path],
    preprocessing: PreprocessingConfig,
):
    """Parse Fortran sources and apply the parser's shared project resolution.

    Each path is preprocessed and parsed once while retaining its path/model
    pair. The completed models are then passed together to the parser's project
    compile-time coordinator. For example, a kind parameter from the first file
    can resolve a procedure or derived field in the second file without the CLI
    owning a second resolution algorithm. The ordered ``(path, file)`` pairs
    are returned for stage reporting.
    """
    parser = FortranParser()
    parsed_files = []
    for path in paths:
        code, _preprocessing_recipe = _fortran_source_for_path(path, preprocessing)
        parsed_files.append((path, parser.parse_file(code, filename=str(path))))

    parser._resolve_project_compile_time_facts([parsed for _path, parsed in parsed_files])
    return parsed_files


def _parse_c_semantic_sources(context: _SemanticPipelineContext) -> _ParsedSemanticSources:
    if not context.source_paths:
        return _ParsedSemanticSources(context.source_paths, None)
    return _ParsedSemanticSources(context.source_paths, _parse_c_project(context.paths, context.preprocessing))


def _convert_c_semantic_sources(
    parsed_sources: _ParsedSemanticSources,
    context: _SemanticPipelineContext,
) -> list[tuple[Path, list[object]]]:
    if parsed_sources.parsed is None:
        return []
    c_standard_type_report = context.c_standard_type_report
    if c_standard_type_report is None:
        c_standard_type_report = _c_standard_type_report(context.preprocessing)
    modules_by_source = {
        module.origin.native_name: [module]
        for module in _convert_c_project(
            parsed_sources.parsed,
            c_standard_type_report=c_standard_type_report,
            export_symbols=context.export_symbols,
        )
    }
    return [(path, modules_by_source[str(path)]) for path in parsed_sources.source_paths]


def _parse_fortran_semantic_sources(context: _SemanticPipelineContext) -> _ParsedSemanticSources:
    if not context.source_paths:
        return _ParsedSemanticSources(context.source_paths, [])
    return _ParsedSemanticSources(
        context.source_paths,
        _parse_fortran_source_files(list(context.source_paths), context.preprocessing),
    )


def _convert_fortran_semantic_sources(
    parsed_sources: _ParsedSemanticSources,
    context: _SemanticPipelineContext,
) -> list[tuple[Path, list[object]]]:
    parsed_files = list(parsed_sources.parsed)
    if not parsed_files:
        return []
    wrapped_derived_types = _fortran_wrapped_derived_types(fobj for _p, fobj in parsed_files)
    probe_options = _fortran_probe_options(
        report=context.fortran_type_report,
        runner=context.fortran_type_probe_runner,
        cache_dir=context.fortran_type_probe_cache_dir,
        refresh=context.refresh_fortran_type_probe,
    )
    converted_files = []
    for p, fobj in parsed_files:
        compile_time_values = _fortran_compile_time_values(fobj, context.preprocessing, **probe_options)
        type_facts = _fortran_type_facts(
            fobj,
            context.preprocessing,
            compile_time_values=compile_time_values,
            **probe_options,
        )
        modules = fortran_file_to_semantic_modules(
            fobj,
            standalone_module_name=p.stem,
            compile_time_values=compile_time_values,
            wrapped_derived_types=wrapped_derived_types,
            assume_intent_in_scalars=context.assume_intent_in_scalars,
            **({"type_facts": type_facts} if type_facts is not None else {}),
        )
        converted_files.append((p, modules))
    return converted_files


_SOURCE_SEMANTIC_PIPELINES = {
    "c": _SourceSemanticPipeline(
        parser=_parse_c_semantic_sources,
        converter_to_ir=_convert_c_semantic_sources,
    ),
    "fortran": _SourceSemanticPipeline(
        parser=_parse_fortran_semantic_sources,
        converter_to_ir=_convert_fortran_semantic_sources,
    ),
}


def _semantic_payload_for_converted_files(converted_files) -> dict[str, dict]:
    from prik.pipeline.pyi import emit_module_stubs
    from prik.printers import emit_module

    out: dict[str, dict] = {}
    available_modules = [module for _p, modules in converted_files for module in modules]
    primary_names = {module.name for module in available_modules}
    for p, modules in converted_files:
        if _is_fortran_semantic_file(modules):
            out[str(p)] = _fortran_contract_payload(Path(p), modules, available_modules)
            continue
        if _is_c_semantic_file(modules):
            # A generated C starter contract preserves raw source facts, even
            # for a form that the direct-only wrapper policy will later block.
            # ``--pyi`` is contract extraction, not wrapper planning.
            module_stubs = {module.name: emit_module(module).strip() for module in modules}
            out[str(p)] = {
                "semantic_modules": [asdict(module) for module in modules],
                "pyi": "\n\n".join(module_stubs.values()).strip(),
                "pyi_modules": module_stubs,
            }
            continue
        stubs = emit_module_stubs(modules, available_modules=available_modules)
        module_stubs = {module.name: stubs[module.name] for module in modules}
        out[str(p)] = {
            "semantic_modules": [asdict(m) for m in modules],
            "pyi": "\n\n".join(module_stubs.values()).strip(),
            "pyi_modules": module_stubs,
        }
        dependencies = {module_name: text for module_name, text in stubs.items() if module_name not in primary_names}
        if dependencies:
            out[str(p)]["pyi_dependencies"] = dependencies
    return out


def _is_fortran_semantic_file(modules) -> bool:
    return any(getattr(getattr(module, "origin", None), "source_language", None) == "fortran" for module in modules)


def _is_c_semantic_file(modules) -> bool:
    """Return whether modules came from C source contract extraction."""
    return any(getattr(getattr(module, "origin", None), "source_language", None) == "c" for module in modules)


def _fortran_contract_payload(path: Path, modules, available_modules) -> dict[str, object]:
    from prik.pipeline.pyi import emit_module_stubs

    native_modules = [module for module in modules if module.origin.source_kind == "module"]
    external_modules = [module for module in modules if module.origin.source_kind != "module"]
    root_modules = [module.name for module in native_modules]
    emitted = (
        emit_module_stubs(
            native_modules,
            available_modules=available_modules,
            normalize_fortran_public_names=True,
        )
        if native_modules
        else {}
    )
    module_stubs = {module.name: emitted.pop(module.name) for module in native_modules}
    dependencies = dict(emitted)
    external_text = []
    for module in external_modules:
        external_stubs = emit_module_stubs(
            [module],
            available_modules=available_modules,
            normalize_fortran_public_names=True,
        )
        external_text.append(external_stubs.pop(module.name))
        for name, text in external_stubs.items():
            if name in dependencies and dependencies[name] != text:
                raise ValueError(f"Conflicting generated dependency stub for {name}")
            dependencies[name] = text

    root_stub = _source_root_stub(root_modules, external_text)
    payload: dict[str, object] = {
        "semantic_modules": [asdict(module) for module in modules],
        "pyi": "\n\n".join([*module_stubs.values(), *external_text]).strip(),
        "pyi_modules": module_stubs,
        "pyi_root": root_stub,
        "pyi_root_modules": root_modules,
        "pyi_root_externals": external_text,
    }
    if dependencies:
        payload["pyi_dependencies"] = dependencies
    return payload


def _source_root_stub(module_names: list[str], external_text: list[str]) -> str:
    contract_imports: set[str] = set()
    external_sections = []
    for text in external_text:
        imports, body = _split_contract_imports(text)
        contract_imports.update(imports)
        if body:
            external_sections.append(body)
    contract_section = f"from prik.contracts import {', '.join(sorted(contract_imports))}" if contract_imports else ""
    lines = [f"from . import {name}" for name in module_names]
    import_section = "\n".join(line for line in [contract_section, *lines] if line)
    sections = [import_section, *external_sections]
    return "\n\n".join(section for section in sections if section).strip()


def _split_contract_imports(text: str) -> tuple[set[str], str]:
    imports: set[str] = set()
    body_lines = []
    for line in text.splitlines():
        if line.startswith("from prik.contracts import "):
            imports.update(item.strip() for item in line.removeprefix("from prik.contracts import ").split(","))
            continue
        body_lines.append(line)
    return imports, "\n".join(body_lines).strip()


def _format_pyi_report(semantic_report: dict[str, dict]) -> str:
    lines: list[str] = []
    emitted_dependencies: set[str] = set()
    for fname, payload in semantic_report.items():
        lines.append(f"File: {fname}")
        root = payload.get("pyi_root")
        if root:
            entry_name = (
                "__init__.pyi" if Path(fname).stem in payload.get("pyi_modules", {}) else f"{Path(fname).stem}.pyi"
            )
            lines.append(f"Root contract: {Path(fname).stem}/{entry_name}")
            lines.append(root)
            lines.append("")
        for module_name, text in payload.get("pyi_modules", {}).items():
            lines.append(f"Module contract: {module_name}.pyi")
            lines.append(text)
            lines.append("")
        if not payload.get("pyi_modules"):
            lines.append(payload.get("pyi") or "<no module declarations found>")
        lines.append("")
        for module_name, text in payload.get("pyi_dependencies", {}).items():
            if module_name in emitted_dependencies:
                continue
            emitted_dependencies.add(module_name)
            lines.append(f"Dependency stub: {module_name}.pyi")
            lines.append(text)
            lines.append("")
    return "\n".join(lines).rstrip()


def _write_pyi_dependencies(
    semantic_report: dict[str, dict],
    *,
    output_dir: Path | None = None,
) -> None:
    outputs: dict[Path, str] = {}
    for fname, payload in semantic_report.items():
        parent = output_dir or Path(fname).parent
        for module_name, text in payload.get("pyi_dependencies", {}).items():
            path = parent.joinpath(*module_name.split(".")).with_suffix(".pyi")
            existing = outputs.get(path)
            if existing is not None and existing != text:
                raise ValueError(f"Conflicting generated dependency stub for {path}")
            outputs[path] = text
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def _fortran_wrapped_derived_types(parsed_files) -> set[tuple[str, str]]:
    return {
        (dtype.module.lower(), dtype.name.lower())
        for parsed in parsed_files
        for module in parsed.modules
        for dtype in module.derived_types
        if dtype.module
    }


def _fortran_compile_time_values(
    parsed,
    preprocessing: PreprocessingConfig,
    *,
    report: FortranTypeProbeReport | None = None,
    runner: list[str] | None = None,
    cache_dir: str | None = None,
    refresh: bool = False,
) -> dict[str, int] | None:
    """Evaluate compiler-dependent Fortran values when a compiler is configured."""
    if report is None and (
        not isinstance(preprocessing, PreprocessingConfig)
        or not preprocessing.uses_compiler
        or not preprocessing.compiler
    ):
        return None

    from prik.semantics.fortran2ir import collect_semantic_compile_time_requirements
    from prik.preprocessing.probes.fortran_types import evaluate_fortran_type_requirements

    requirements = collect_semantic_compile_time_requirements(parsed)
    if not requirements:
        return None
    probe_options = _fortran_probe_options(report=report, runner=runner, cache_dir=cache_dir, refresh=refresh)
    return evaluate_fortran_type_requirements(preprocessing, requirements, **probe_options)


def _fortran_type_facts(
    parsed,
    preprocessing: PreprocessingConfig,
    *,
    compile_time_values: dict[str, int] | None = None,
    report: FortranTypeProbeReport | None = None,
    runner: list[str] | None = None,
    cache_dir: str | None = None,
    refresh: bool = False,
) -> dict[tuple[str, str | None], dict[str, object]] | None:
    """Measure compiler-dependent storage for intrinsic types used by one source."""
    if report is None and (
        not isinstance(preprocessing, PreprocessingConfig)
        or not preprocessing.uses_compiler
        or not preprocessing.compiler
    ):
        return None

    from prik.semantics.fortran2ir import collect_fortran_type_storage_requirements
    from prik.preprocessing.probes.fortran_types import evaluate_fortran_type_facts

    requirements = collect_fortran_type_storage_requirements(parsed, compile_time_values=compile_time_values)
    if not requirements:
        return None
    probe_options = _fortran_probe_options(report=report, runner=runner, cache_dir=cache_dir, refresh=refresh)
    return evaluate_fortran_type_facts(preprocessing, requirements, **probe_options)


def _build_preprocessing_config(args: argparse.Namespace, parser: argparse.ArgumentParser) -> PreprocessingConfig:
    """Build and validate the shared preprocessing CLI configuration."""
    defines = list(args.defines or [])
    undefs = list(args.undefs or [])
    compiler = args.compiler
    if compiler is None and args.compile_commands is None and args.preprocess_template is None:
        compiler = "cc" if args.language == "c" else "gfortran"
    for define in defines:
        try:
            validate_macro_name(define, "--define/-D")
        except PreprocessingError as exc:
            parser.error(str(exc))
    for undef in undefs:
        try:
            validate_macro_name(undef, "--undef/-U")
        except PreprocessingError as exc:
            parser.error(str(exc))

    config = PreprocessingConfig(
        mode="compiler",
        compiler=compiler,
        compile_commands=args.compile_commands,
        adapter=args.preprocessor_adapter,
        command_template=args.preprocess_template,
        include_dirs=list(args.include_dirs or []),
        defines=defines,
        undefs=undefs,
        std=args.std,
        compiler_args=list(args.compiler_args or []),
        include_exposure=args.include_exposure,
        public_includes=list(args.public_includes or []),
        private_includes=list(args.private_includes or []),
    )

    if config.uses_compiler and config.command_template and config.adapter != "command-template":
        parser.error("--preprocess-template requires --preprocessor-adapter command-template")
    return config


def _path_is_fortran_source(path: str) -> bool:
    return Path(path).suffix.lower() in _FORTRAN_SOURCE_SUFFIXES


def _path_is_c_source(path: str) -> bool:
    return Path(path).suffix.lower() == ".c"


def _path_is_pyi_contract(path: str) -> bool:
    return Path(path).suffix.lower() == ".pyi"


def _wrapper_build_uses_manifest(args: argparse.Namespace) -> bool:
    return _is_wrapper_build(args) and getattr(args, "build_manifest", None) is not None


def _wrapper_build_uses_pyi_contract(args: argparse.Namespace) -> bool:
    return (
        _is_wrapper_build(args)
        and not _wrapper_build_uses_manifest(args)
        and any(_path_is_pyi_contract(path) for path in args.paths)
    )


def _native_link_options_used(args: argparse.Namespace) -> bool:
    return bool(
        getattr(args, "no_compile_input_sources", False)
        or getattr(args, "native_fortran_sources", None)
        or getattr(args, "native_c_sources", None)
        or getattr(args, "native_compile_flags", None)
        or getattr(args, "native_c_compile_flags", None)
        or getattr(args, "native_objects", None)
        or getattr(args, "native_libraries", None)
        or getattr(args, "native_link_items", None)
        or getattr(args, "native_library_dirs", None)
    )


def _prebuilt_native_link_input_used(args: argparse.Namespace) -> bool:
    return bool(
        getattr(args, "native_objects", None)
        or getattr(args, "native_libraries", None)
        or getattr(args, "native_link_items", None)
    )


def _wrapper_compile_options_used(args: argparse.Namespace) -> bool:
    return bool(
        getattr(args, "wrapper_compiler_debug", False)
        or getattr(args, "wrapper_fortran_flags", None)
        or getattr(args, "wrapper_c_flags", None)
    )


def _is_wrapper_build(args: argparse.Namespace) -> bool:
    """Return whether the command projects and renders a wrapper plan."""
    return args.command == "build" or (args.command == "generate" and (args.generate_sources or args.makefile))


def _has_semantic_stage(args: argparse.Namespace) -> bool:
    return bool(args.semantics or args.pyi or _is_wrapper_build(args))


def _validate_pyi_wrapper_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if any(Path(path).is_dir() for path in args.paths):
        parser.error("A .pyi wrapper build expects semantic contract files, not directories")
    if any(not _path_is_pyi_contract(path) for path in args.paths):
        parser.error("A .pyi wrapper build cannot mix positional native sources; pass native artifacts with flags")
    if len(args.paths) != 1:
        parser.error("A .pyi wrapper build accepts exactly one entry contract")
    if getattr(args, "no_compile_input_sources", False):
        parser.error("--no-compile-input-sources applies only to source-driven wrapper builds")
    if getattr(args, "assume_intent_in_scalars", False):
        parser.error(
            "--assume-intent-in-scalars interprets a missing Fortran intent; a semantic .pyi contract "
            "already states its own results, so edit the contract instead"
        )
    if getattr(args, "export_symbols", None):
        parser.error(
            "--export-symbols selects declarations while reading C source; a semantic .pyi contract "
            "already states its public functions"
        )
    if not (
        getattr(args, "native_fortran_sources", None)
        or getattr(args, "native_c_sources", None)
        or getattr(args, "native_objects", None)
        or getattr(args, "native_libraries", None)
        or getattr(args, "native_link_items", None)
    ):
        parser.error(
            "A .pyi wrapper build requires --native-fortran-sources, --native-c-sources, --native-objects, "
            "--native-library, or --native-link-item"
        )


def _validate_manifest_wrapper_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.paths:
        parser.error("--build-manifest replays the saved entry contract; do not pass positional inputs")
    if getattr(args, "out_dir", None) is not None:
        parser.error("--build-manifest replays its saved output directory; do not pass --out-dir")
    if getattr(args, "_explicit_language", False):
        parser.error("--build-manifest replays its saved input language; do not pass --language")
    if bool(
        getattr(args, "_explicit_preprocessor_adapter", False)
        or getattr(args, "preprocess_template", None)
        or getattr(args, "defines", None)
        or getattr(args, "undefs", None)
        or getattr(args, "std", None)
        or getattr(args, "compiler_args", None)
    ):
        parser.error(
            "--build-manifest replays its saved preprocessing recipe; "
            "only --compiler and -I/--include-dir are compiler overrides"
        )
    if _native_link_options_used(args):
        parser.error("--build-manifest replays saved native inputs; do not pass native build flags")
    if (
        getattr(args, "strict_wrapper_names", False)
        or getattr(args, "assume_intent_in_scalars", False)
        or getattr(args, "export_symbols", None)
        or _wrapper_compile_options_used(args)
    ):
        parser.error("--build-manifest replays saved wrapper behavior and compiler flags")


def _validate_source_wrapper_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    language = args.language
    label = "C" if language == "c" else "Fortran"
    source_check = _path_is_c_source if language == "c" else _path_is_fortran_source
    if not args.paths:
        parser.error(
            f"A wrapper build expects at least one {label} source, source directory, or semantic .pyi contract"
        )
    unsupported = [path for path in args.paths if not Path(path).is_dir() and not source_check(path)]
    if unsupported:
        parser.error(
            f"A wrapper build expects recognized {label} source suffixes or one semantic .pyi contract; "
            f"unsupported input: {unsupported[0]}"
        )
    collect = (lambda path: sorted(path.rglob("*.c"))) if language == "c" else _collect_extensions
    empty_directories = [path for path in args.paths if Path(path).is_dir() and not collect(Path(path))]
    if empty_directories:
        parser.error(f"A wrapper build found no recognized {label} sources under: {empty_directories[0]}")
    if not getattr(args, "no_compile_input_sources", False):
        return
    if not (
        getattr(args, "native_fortran_sources", None)
        or getattr(args, "native_c_sources", None)
        or _prebuilt_native_link_input_used(args)
    ):
        parser.error(
            "--no-compile-input-sources requires --native-fortran-sources, --native-c-sources, --native-objects, "
            "--native-library, or --native-link-item"
        )


def _validate_wrapper_out(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.out is None:
        return
    if args.out == "":
        parser.error("--out for wrapper builds requires an output name")
    output_path = Path(args.out)
    if output_path.suffix and output_path.suffix != ".so":
        parser.error("--out for wrapper builds expects NAME or NAME.so")
    if not output_path.stem.isidentifier():
        parser.error("--out for wrapper builds expects a valid Python module name")


def _validate_wrapper_build_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not _is_wrapper_build(args):
        return
    if args.command == "generate" and args.out is not None:
        parser.error("generate --sources/--makefile uses --out-dir, not --out")
    if args.command == "build":
        _validate_wrapper_out(args, parser)

    if _wrapper_build_uses_manifest(args):
        _validate_manifest_wrapper_options(args, parser)
        return

    if _wrapper_build_uses_pyi_contract(args):
        _validate_pyi_wrapper_options(args, parser)
        return

    _validate_source_wrapper_options(args, parser)


def _validate_c_main_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.language != "c":
        if getattr(args, "export_symbols", None):
            parser.error("--export-symbols is supported only with --language c")
        return
    if args.command == "parse" and args.show_vars:
        parser.error("--show-vars is Fortran-only and is not supported for --language c")


def _read_c_export_symbols(path: str | Path) -> tuple[str, ...]:
    """Read one fail-closed C function allowlist from a UTF-8 text file."""
    source = Path(path)
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"Cannot read --export-symbols file {source}: {exc}") from exc

    symbols = []
    locations: dict[str, int] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        symbol = raw_line.split("#", 1)[0].strip()
        if not symbol:
            continue
        valid = (
            symbol.isascii()
            and (symbol[0].isalpha() or symbol[0] == "_")
            and all(character.isalnum() or character == "_" for character in symbol)
        )
        if not valid:
            raise ValueError(f"Invalid C identifier in --export-symbols file {source}:{line_number}: {symbol!r}")
        previous = locations.get(symbol)
        if previous is not None:
            raise ValueError(
                f"Repeated C function name in --export-symbols file {source}:{line_number}: "
                f"{symbol!r} first appeared on line {previous}"
            )
        locations[symbol] = line_number
        symbols.append(symbol)
    if not symbols:
        raise ValueError(f"--export-symbols file contains no C function names: {source}")
    return tuple(symbols)


def _complete_c_export_symbol_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Resolve the CLI file once for every downstream semantic/build path."""
    path = getattr(args, "export_symbols", None)
    args._resolved_export_symbols = None
    if path is None:
        return
    try:
        args._resolved_export_symbols = _read_c_export_symbols(path)
    except ValueError as exc:
        parser.error(str(exc))


def _validate_output_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.print_limit is not None and args.print_limit < 0:
        parser.error("--print-limit must be >= 0")


def _validate_pyi_generation_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not args.pyi:
        return
    invalid = []
    if args.out_dir is not None:
        invalid.append("--out-dir")
    if args.build_manifest is not None:
        invalid.append("--build-manifest")
    if _native_link_options_used(args):
        invalid.append("native link options")
    if _wrapper_compile_options_used(args) or args.strict_wrapper_names:
        invalid.append("wrapper compiler options")
    if invalid:
        parser.error(f"generate --pyi cannot use {', '.join(invalid)}")


def _validate_semantic_stage_source_inputs(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Require source-stage commands to receive at least one source file.

    Wrapper builds separately accept a semantic ``.pyi`` contract.  The
    ``semantics`` and ``generate --pyi`` commands instead create their output
    from native source, so filtering a contract out of their source list must
    be a diagnostic rather than an empty report.
    """
    if not (args.semantics or args.pyi):
        return

    source_suffixes = _SOURCE_SUFFIXES_BY_LANGUAGE[args.language]
    unsupported = tuple(
        Path(raw) for raw in args.paths if not Path(raw).is_dir() and Path(raw).suffix.lower() not in source_suffixes
    )
    command = "semantics" if args.semantics else "generate --pyi"
    if unsupported:
        parser.error(
            f"{command} expects recognized {args.language} source suffixes; unsupported input: {unsupported[0]}"
        )

    if not _source_paths_for_semantic_pipeline(args.paths, language=args.language):
        parser.error(f"{command} found no recognized {args.language} sources in the supplied inputs")


def _validate_main_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int | None:
    if not args.paths and getattr(args, "build_manifest", None) is None:
        parser.error("Source input is required unless --build-manifest is used")

    _validate_pyi_generation_options(args, parser)
    _validate_semantic_stage_source_inputs(args, parser)
    _validate_wrapper_build_options(args, parser)
    _validate_c_main_options(args, parser)

    _validate_output_options(args, parser)
    _complete_c_export_symbol_options(args, parser)
    return args.print_limit


def _c_type_facts_for_stages(args: argparse.Namespace, preprocessing: PreprocessingConfig):
    if args.language != "c" or not _has_semantic_stage(args):
        return None
    return _c_standard_type_report(preprocessing)


def _semantic_stage_options(
    args: argparse.Namespace,
    *,
    c_standard_type_report: dict[str, object] | None,
) -> dict[str, object]:
    options: dict[str, object] = {"language": args.language}
    if c_standard_type_report is not None:
        options["c_standard_type_report"] = c_standard_type_report
    if getattr(args, "assume_intent_in_scalars", False):
        options["assume_intent_in_scalars"] = True
    if getattr(args, "_resolved_export_symbols", None) is not None:
        options["export_symbols"] = args._resolved_export_symbols
    return options


def _cli_native_link_items(raw_items: list[str] | None) -> tuple[dict[str, object], ...]:
    if not raw_items:
        return ()
    aliases = {
        "arg": "linker_argument",
        "archive": "archive",
        "linker-argument": "linker_argument",
        "linker_argument": "linker_argument",
        "library": "named_library",
        "named-library": "named_library",
        "named_library": "named_library",
        "object": "object",
        "shared-library": "shared_library",
        "shared_library": "shared_library",
    }
    parsed = []
    for raw in raw_items:
        kind_text, separator, value = raw.partition(":")
        kind = aliases.get(kind_text)
        if separator != ":" or kind is None or not value:
            raise ValueError(
                "--native-link-item expects KIND:VALUE where KIND is object, archive, shared-library, library, or arg"
            )
        if kind in {"object", "archive", "shared_library"}:
            parsed.append({"kind": kind, "path": value})
        elif kind == "named_library":
            parsed.append({"kind": kind, "name": value})
        else:
            parsed.append({"kind": kind, "argument": value})
    return tuple(parsed)


def _cli_compiler_flags(raw_flags: list[str] | None, *, option_name: str) -> tuple[str, ...]:
    if not raw_flags:
        return ()
    flags = []
    for raw in raw_flags:
        try:
            flags.extend(shlex.split(raw))
        except ValueError as exc:
            raise ValueError(f"Invalid {option_name} value {raw!r}: {exc}") from exc
    return tuple(flags)


def _cli_native_compile_flags(raw_flags: list[str] | None) -> tuple[str, ...]:
    return _cli_compiler_flags(raw_flags, option_name="--native-compile-flags")


def _cli_native_c_compile_flags(raw_flags: list[str] | None) -> tuple[str, ...]:
    return _cli_compiler_flags(raw_flags, option_name="--native-c-compile-flags")


def _positive_compile_jobs(value: str) -> int:
    try:
        jobs = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("jobs must be a positive integer") from exc
    if jobs < 1:
        raise argparse.ArgumentTypeError("jobs must be a positive integer")
    return jobs


def _cli_build_include_dirs(args: argparse.Namespace) -> tuple[str, ...]:
    """Return build-wide CLI include paths in user order."""
    return tuple(args.include_dirs or ())


def _cli_wrapper_fortran_flags(raw_flags: list[str] | None) -> tuple[str, ...]:
    return _cli_compiler_flags(raw_flags, option_name="--wrapper-fortran-flags")


def _cli_wrapper_c_flags(raw_flags: list[str] | None) -> tuple[str, ...]:
    return _cli_compiler_flags(raw_flags, option_name="--wrapper-c-flags")


def _with_link_time_optimization(flags: tuple[str, ...], args) -> tuple[str, ...]:
    """Append ``-flto`` when the build asked for link-time optimization.

    Requested flags follow the compiler profile, so this adds LTO without
    replacing the selected optimization profile.
    """
    if not getattr(args, "lto", False) or "-flto" in flags:
        return flags
    return (*flags, "-flto")


def _wrapper_shared_library_alias_path(result, raw_out: str | None) -> Path:
    if raw_out in (None, ""):
        return Path.cwd() / f"{result.module_name}.so"

    path = Path(raw_out)
    target = path if path.suffix else path.with_suffix(".so")
    if not target.is_absolute() and target.parent == Path("."):
        return Path.cwd() / target.name
    return target


def _wrapper_output_name(args: argparse.Namespace) -> str | None:
    if getattr(args, "out", None) is None:
        return None
    return Path(args.out).stem


def _copy_wrapper_shared_library_alias(args: argparse.Namespace, result):
    if not result.compiled:
        return result

    target = _wrapper_shared_library_alias_path(result, getattr(args, "out", None))
    if target != result.shared_library:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result.shared_library, target)

    generated_files = result.generated_files
    if target not in generated_files:
        generated_files = (*generated_files, target)
    return replace(result, shared_library=target, generated_files=generated_files)


def _cli_native_libraries(raw_libraries: list[str] | None) -> tuple[str, ...]:
    if not raw_libraries:
        return ()
    libraries = []
    for raw in raw_libraries:
        try:
            libraries.extend(shlex.split(raw))
        except ValueError as exc:
            raise ValueError(f"Invalid --native-library value {raw!r}: {exc}") from exc
    return tuple(libraries)


def _parse_stage_report(args: argparse.Namespace, preprocessing: PreprocessingConfig):
    if not args.parse:
        return None
    if args.language == "c":
        return parse_c_report(
            args.paths,
            include_dirs=preprocessing.include_dirs,
            preprocessing=_c_parser_preprocessing_mode(preprocessing),
            source_loader=_c_source_loader(preprocessing),
        )
    return _parse_report(args.paths, preprocessing)


def _run_stage_reports(args: argparse.Namespace, preprocessing: PreprocessingConfig):
    c_standard_type_report = _c_type_facts_for_stages(args, preprocessing)
    semantic_options = _semantic_stage_options(
        args,
        c_standard_type_report=c_standard_type_report,
    )
    parse_payload = _parse_stage_report(args, preprocessing)
    semantic_payload = (
        _semantic_report(args.paths, preprocessing, **semantic_options) if (args.semantics or args.pyi) else None
    )
    return parse_payload, semantic_payload


def _run_stage_reports_with_diagnostics(args: argparse.Namespace, preprocessing: PreprocessingConfig):
    try:
        return _run_stage_reports(args, preprocessing)
    except CParseError as exc:
        if args.debug or _env_flag("C_PARSER_DEBUG"):
            raise
        print(
            exc.format_diagnostic(color=_diagnostic_color_enabled(disabled=args.no_color), debug=False), file=sys.stderr
        )
    except FortranParseError as exc:
        if args.debug or _env_flag("FORTRAN_PARSER_DEBUG"):
            raise
        print(
            exc.format_diagnostic(color=_diagnostic_color_enabled(disabled=args.no_color), debug=False), file=sys.stderr
        )
    except PreprocessingError as exc:
        if args.debug or _env_flag("PRIK_DEBUG"):
            raise
        if exc.diagnostics:
            for diagnostic in exc.diagnostics:
                location = diagnostic.path or "<preprocessor>"
                if diagnostic.line is not None:
                    location = f"{location}:{diagnostic.line}"
                print(f"{location}: error[{diagnostic.category}]: {diagnostic.message}", file=sys.stderr)
        else:
            print(f"prik: error[{exc.category}]: {exc}", file=sys.stderr)
    except (SyntaxError, ValueError) as exc:
        if args.debug or _env_flag("PRIK_DEBUG"):
            raise
        print(f"prik: error: {exc}", file=sys.stderr)
    return None


def _run_wrap_build(args: argparse.Namespace, preprocessing: PreprocessingConfig):
    from prik.pipeline.build import (
        build_c_extension,
        build_fortran_extension,
        build_pyi_extension,
        build_pyi_extension_from_manifest,
    )

    def record_total_build_time(elapsed: float) -> None:
        args._verbose_total_build_time = elapsed

    total_build_time_reporter = record_total_build_time if getattr(args, "verbose", False) else None
    if _wrapper_build_uses_manifest(args):
        result = build_pyi_extension_from_manifest(
            args.build_manifest,
            output_name=_wrapper_output_name(args),
            input_compiler=getattr(args, "compiler", None),
            input_c_compiler=getattr(args, "compiler", None),
            include_dirs=getattr(args, "include_dirs", None),
            makefile=getattr(args, "makefile", False),
            generate_sources=getattr(args, "generate_sources", False),
            jobs=getattr(args, "jobs", None),
            verbose=1 if getattr(args, "verbose", False) else 0,
            _on_total_build_time=total_build_time_reporter,
        )
        return _copy_wrapper_shared_library_alias(args, result)

    if _wrapper_build_uses_pyi_contract(args):
        result = build_pyi_extension(
            args.paths[0],
            input_compiler=preprocessing.compiler or "gfortran",
            input_c_compiler=(preprocessing.compiler or "cc") if args.language == "c" else "cc",
            native_language=args.language,
            native_fortran_sources=getattr(args, "native_fortran_sources", None),
            native_fortran_flags=_with_link_time_optimization(
                _cli_native_compile_flags(getattr(args, "native_compile_flags", None)), args
            ),
            native_c_sources=getattr(args, "native_c_sources", None),
            native_c_flags=_with_link_time_optimization(
                _cli_native_c_compile_flags(getattr(args, "native_c_compile_flags", None)), args
            ),
            native_objects=getattr(args, "native_objects", None),
            native_libraries=_cli_native_libraries(getattr(args, "native_libraries", None)),
            native_link_items=_cli_native_link_items(getattr(args, "native_link_items", None)),
            native_library_dirs=getattr(args, "native_library_dirs", None),
            native_include_dirs=_cli_build_include_dirs(args),
            output_name=_wrapper_output_name(args),
            output_dir=getattr(args, "out_dir", None),
            strict_wrapper_names=getattr(args, "strict_wrapper_names", False),
            collision_adapters=getattr(args, "collision_adapters", None),
            collision_adapter_all=getattr(args, "collision_adapter_all", False),
            positional_only=getattr(args, "positional_only", False),
            makefile=getattr(args, "makefile", False),
            generate_sources=getattr(args, "generate_sources", False),
            jobs=getattr(args, "jobs", None),
            verbose=1 if getattr(args, "verbose", False) else 0,
            wrapper_compiler_debug=getattr(args, "wrapper_compiler_debug", False),
            wrapper_fortran_flags=_with_link_time_optimization(
                _cli_wrapper_fortran_flags(getattr(args, "wrapper_fortran_flags", None)), args
            ),
            wrapper_c_flags=_with_link_time_optimization(
                _cli_wrapper_c_flags(getattr(args, "wrapper_c_flags", None)), args
            ),
            _on_total_build_time=total_build_time_reporter,
        )
        return _copy_wrapper_shared_library_alias(args, result)

    if args.language == "c":
        result = build_c_extension(
            args.paths,
            output_dir=getattr(args, "out_dir", None),
            output_name=_wrapper_output_name(args),
            input_c_compiler=preprocessing.compiler or "cc",
            preprocessing=preprocessing,
            export_symbols=getattr(args, "_resolved_export_symbols", None),
            input_compiler="gfortran",
            native_c_sources=getattr(args, "native_c_sources", None),
            native_c_flags=_with_link_time_optimization(
                _cli_native_c_compile_flags(getattr(args, "native_c_compile_flags", None)), args
            ),
            native_fortran_sources=getattr(args, "native_fortran_sources", None),
            native_fortran_flags=_with_link_time_optimization(
                _cli_native_compile_flags(getattr(args, "native_compile_flags", None)), args
            ),
            native_objects=getattr(args, "native_objects", None),
            native_libraries=_cli_native_libraries(getattr(args, "native_libraries", None)),
            native_link_items=_cli_native_link_items(getattr(args, "native_link_items", None)),
            native_library_dirs=getattr(args, "native_library_dirs", None),
            native_include_dirs=_cli_build_include_dirs(args),
            strict_wrapper_names=getattr(args, "strict_wrapper_names", False),
            collision_adapters=getattr(args, "collision_adapters", None),
            collision_adapter_all=getattr(args, "collision_adapter_all", False),
            positional_only=getattr(args, "positional_only", False),
            makefile=getattr(args, "makefile", False),
            generate_sources=getattr(args, "generate_sources", False),
            jobs=getattr(args, "jobs", None),
            verbose=1 if getattr(args, "verbose", False) else 0,
            wrapper_compiler_debug=getattr(args, "wrapper_compiler_debug", False),
            wrapper_fortran_flags=_with_link_time_optimization(
                _cli_wrapper_fortran_flags(getattr(args, "wrapper_fortran_flags", None)), args
            ),
            wrapper_c_flags=_with_link_time_optimization(
                _cli_wrapper_c_flags(getattr(args, "wrapper_c_flags", None)), args
            ),
            _on_total_build_time=total_build_time_reporter,
        )
        return _copy_wrapper_shared_library_alias(args, result)

    result = build_fortran_extension(
        args.paths,
        output_dir=getattr(args, "out_dir", None),
        output_name=_wrapper_output_name(args),
        preprocessing=preprocessing,
        strict_wrapper_names=getattr(args, "strict_wrapper_names", False),
        collision_adapters=getattr(args, "collision_adapters", None),
        collision_adapter_all=getattr(args, "collision_adapter_all", False),
        positional_only=getattr(args, "positional_only", False),
        assume_intent_in_scalars=getattr(args, "assume_intent_in_scalars", False),
        compile_input_sources=not getattr(args, "no_compile_input_sources", False),
        native_fortran_sources=getattr(args, "native_fortran_sources", None),
        native_fortran_flags=_with_link_time_optimization(
            _cli_native_compile_flags(getattr(args, "native_compile_flags", None)), args
        ),
        native_c_sources=getattr(args, "native_c_sources", None),
        native_c_flags=_with_link_time_optimization(
            _cli_native_c_compile_flags(getattr(args, "native_c_compile_flags", None)), args
        ),
        native_objects=getattr(args, "native_objects", None),
        native_libraries=_cli_native_libraries(getattr(args, "native_libraries", None)),
        native_link_items=_cli_native_link_items(getattr(args, "native_link_items", None)),
        native_library_dirs=getattr(args, "native_library_dirs", None),
        native_include_dirs=_cli_build_include_dirs(args),
        makefile=getattr(args, "makefile", False),
        generate_sources=getattr(args, "generate_sources", False),
        jobs=getattr(args, "jobs", None),
        verbose=1 if getattr(args, "verbose", False) else 0,
        wrapper_compiler_debug=getattr(args, "wrapper_compiler_debug", False),
        wrapper_fortran_flags=_with_link_time_optimization(
            _cli_wrapper_fortran_flags(getattr(args, "wrapper_fortran_flags", None)), args
        ),
        wrapper_c_flags=_with_link_time_optimization(
            _cli_wrapper_c_flags(getattr(args, "wrapper_c_flags", None)), args
        ),
        _on_total_build_time=total_build_time_reporter,
    )
    return _copy_wrapper_shared_library_alias(args, result)


def _run_wrap_build_with_diagnostics(args: argparse.Namespace, preprocessing: PreprocessingConfig):
    try:
        return _run_wrap_build(args, preprocessing)
    except FortranParseError as exc:
        if args.debug or _env_flag("FORTRAN_PARSER_DEBUG"):
            raise
        print(
            exc.format_diagnostic(color=_diagnostic_color_enabled(disabled=args.no_color), debug=False), file=sys.stderr
        )
    except PreprocessingError as exc:
        if args.debug or _env_flag("PRIK_DEBUG"):
            raise
        if exc.diagnostics:
            for diagnostic in exc.diagnostics:
                location = diagnostic.path or "<preprocessor>"
                if diagnostic.line is not None:
                    location = f"{location}:{diagnostic.line}"
                print(f"{location}: error[{diagnostic.category}]: {diagnostic.message}", file=sys.stderr)
        else:
            print(f"prik: error[{exc.category}]: {exc}", file=sys.stderr)
    except (FileNotFoundError, RuntimeError, SyntaxError, ValueError) as exc:
        if args.debug or _env_flag("PRIK_DEBUG"):
            raise
        print(f"prik: error: {exc}", file=sys.stderr)
    return None


def _select_main_payload(args: argparse.Namespace, parse_payload, semantic_payload):
    if args.parse:
        return parse_payload or {}
    if args.semantics or args.pyi:
        return semantic_payload or {}
    return {}


def _write_pyi_output(args: argparse.Namespace, semantic_payload: dict[str, dict]) -> None:
    if any("pyi_root" in report for report in semantic_payload.values()):
        output_parent = Path(args.out) if args.out else None
        if output_parent is not None and output_parent.suffix.lower() == ".pyi":
            raise ValueError(
                "--out for Fortran --pyi expects a directory, not a single .pyi file; "
                "generated contracts use one file per module"
            )
        _write_fortran_contract_packages(semantic_payload, output_parent=output_parent)
        return
    if args.out:
        roots = [report.get("pyi_root") for report in semantic_payload.values() if report.get("pyi_root")]
        pyi_text = "\n\n".join(roots).strip()
        if not pyi_text:
            pyi_text = "\n\n".join((report.get("pyi") or "") for report in semantic_payload.values()).strip()
        Path(args.out).write_text(pyi_text + "\n", encoding="utf-8")
        _write_pyi_modules(semantic_payload, output_dir=Path(args.out).parent, skip=Path(args.out))
        _write_pyi_dependencies(semantic_payload, output_dir=Path(args.out).parent)
        return
    _write_pyi_modules(semantic_payload)
    for fname, report in semantic_payload.items():
        root = report.get("pyi_root")
        if root:
            Path(fname).with_suffix(".pyi").write_text(root + "\n", encoding="utf-8")
    _write_pyi_dependencies(semantic_payload)


def _write_fortran_contract_packages(
    semantic_payload: dict[str, dict],
    *,
    output_parent: Path | None,
) -> None:
    if output_parent is not None:
        for relative_path, text in _combined_fortran_contract_files(semantic_payload).items():
            target = output_parent / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text + "\n", encoding="utf-8")
        return

    for fname, report in semantic_payload.items():
        source = Path(fname)
        for relative_path, text in _fortran_contract_files(source, report).items():
            target = source.parent / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text + "\n", encoding="utf-8")


def _combined_fortran_contract_files(semantic_payload: dict[str, dict]) -> dict[Path, str]:
    module_names: list[str] = []
    external_text: list[str] = []
    files: dict[Path, str] = {}
    dependency_files: dict[Path, str] = {}

    for report in semantic_payload.values():
        for module_name in report.get("pyi_root_modules", ()):
            if module_name not in module_names:
                module_names.append(module_name)
        external_text.extend(str(text) for text in report.get("pyi_root_externals", ()))
        _merge_contract_mapping(files, Path(), report.get("pyi_modules", {}))
        _merge_contract_mapping(dependency_files, Path(), report.get("pyi_dependencies", {}))

    package_files = {Path("__init__.pyi"): _source_root_stub(module_names, external_text)}
    package_files.update(files)
    for path, text in dependency_files.items():
        existing = package_files.get(path)
        if existing is not None and existing != text:
            raise ValueError(f"Conflicting generated contract for {path}")
        package_files[path] = text
    return package_files


def _fortran_contract_files(source: Path, report: dict[str, object]) -> dict[Path, str]:
    package_dir = Path(source.stem)
    entry_name = "__init__.pyi" if source.stem in report.get("pyi_modules", {}) else f"{source.stem}.pyi"
    files = {package_dir / entry_name: str(report.get("pyi_root", ""))}
    _add_contract_mapping(files, package_dir, report.get("pyi_modules", {}))
    _add_contract_mapping(files, package_dir, report.get("pyi_dependencies", {}))
    return files


def _add_contract_mapping(files: dict[Path, str], package_dir: Path, contracts: object) -> None:
    _merge_contract_mapping(files, package_dir, contracts)


def _merge_contract_mapping(files: dict[Path, str], package_dir: Path, contracts: object) -> None:
    if not isinstance(contracts, dict):
        raise TypeError("Generated contract mapping must be a dictionary")
    for module_name, text in contracts.items():
        target = package_dir.joinpath(*str(module_name).split(".")).with_suffix(".pyi")
        contract_text = str(text)
        existing = files.get(target)
        if existing is not None and existing != contract_text:
            raise ValueError(f"Conflicting generated contract for {target}")
        files[target] = contract_text


def _write_pyi_modules(
    semantic_payload: dict[str, dict],
    *,
    output_dir: Path | None = None,
    skip: Path | None = None,
) -> None:
    for fname, report in semantic_payload.items():
        target_dir = output_dir or Path(fname).parent
        for module_name, text in report.get("pyi_modules", {}).items():
            target = target_dir.joinpath(module_name).with_suffix(".pyi")
            if skip is not None and target.resolve() == skip.resolve():
                continue
            target.write_text(text + "\n", encoding="utf-8")


def _write_json_output(args: argparse.Namespace, payload: dict) -> None:
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return
    for fname, report in payload.items():
        Path(fname).with_suffix(".json").write_text(json.dumps({fname: report}, indent=2), encoding="utf-8")


def _write_main_output(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    payload: dict,
    semantic_payload: dict[str, dict] | None,
) -> bool:
    if args.out is None:
        return False
    if args.json and args.pyi:
        parser.error("--out cannot be used with both --json and --pyi")
    if args.pyi:
        _write_pyi_output(args, semantic_payload or {})
    else:
        _write_json_output(args, payload)
    return True


def _print_parse_output(args: argparse.Namespace, parse_payload: dict, print_limit: int | None) -> None:
    if args.language == "c":
        print(format_c_report(parse_payload, print_limit=print_limit))
        return
    print(
        _format_report(
            parse_payload,
            show_vars=args.show_vars or args.vars_limit is not None,
            print_limit=print_limit,
        )
    )


def _print_main_output(
    args: argparse.Namespace,
    payload: dict,
    parse_payload: dict[str, dict] | None,
    semantic_payload: dict[str, dict] | None,
    print_limit: int | None,
) -> None:
    if args.pyi and not args.json:
        print_pyi_output(_format_pyi_report(semantic_payload or {}))
    elif args.parse and not (args.semantics or args.json or args.pyi):
        _print_parse_output(args, parse_payload or {}, print_limit)
    else:
        print(json.dumps(payload, indent=2))


def _print_wrap_build_output(args: argparse.Namespace, result) -> None:
    payload = result.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
        _print_verbose_total_build_time(args)
        return

    if payload.get("compiled", True):
        print(f"Built extension: {payload['shared_library']}")
    elif payload.get("build_makefile"):
        if payload.get("build_manifest"):
            print(f"Generated build manifest: {payload['build_manifest']}")
        print(f"Generated Makefile: {payload['build_makefile']}")
        print(f"Shared library target: {payload['shared_library']}")
        print(f"Build with: make -f {payload['build_makefile']} -j")
    else:
        print(f"Generated wrapper sources in: {payload['output_dir']}")
    generated_sources = payload.get("generated_sources") or []
    if generated_sources:
        print("Generated sources:")
        for path in generated_sources:
            print(f"  - {path}")
    _print_verbose_total_build_time(args)


def _print_verbose_total_build_time(args: argparse.Namespace) -> None:
    """Print the delayed CLI total after its final artifact summary line."""
    elapsed = getattr(args, "_verbose_total_build_time", None)
    if elapsed is not None:
        print(f">> Total build time: {elapsed:.3f}s")


def print_pyi_output(code: str) -> None:
    # Safe fallback for files, pipes, CI, unsupported terminals, etc.
    if not sys.stdout.isatty():
        print(code)
        return

    try:
        from rich.console import Console
        from rich.syntax import Syntax
    except ImportError:
        print(code)
        return

    try:
        console = Console(force_terminal=True, color_system="auto")
        syntax = Syntax(
            code,
            "python",
            theme="ansi_dark",  # terminal-friendly
            background_color="default",
            line_numbers=False,
            word_wrap=False,
        )
        console.print(syntax)
    except Exception:
        # Never let colored output crash the CLI.
        print(code)


def _help_formatter_class(argv: list[str]):
    """Select optional Rich help without changing the plain-text contract."""
    if "--no-color" in argv or "NO_COLOR" in os.environ:
        return argparse.RawDescriptionHelpFormatter
    try:
        from rich_argparse import RawDescriptionRichHelpFormatter
    except ImportError:
        return argparse.RawDescriptionHelpFormatter

    class _LowercaseRichHelpFormatter(RawDescriptionRichHelpFormatter):
        group_name_formatter = staticmethod(str)

    return _LowercaseRichHelpFormatter


def _help_epilog(text: str) -> str:
    """Append one installation hint only when pretty help is unavailable."""
    try:
        import rich_argparse  # noqa: F401
    except ImportError:
        return (
            f"{text}\n\nOptional: python3 -m pip install 'prik[pretty]' enables colored help "
            "and highlighted generated contracts."
        )
    return text


def _new_cli_parser(
    *,
    prog: str,
    description: str,
    epilog: str,
    argv: list[str],
    usage: str | None = None,
) -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=prog,
        usage=usage,
        description=description,
        formatter_class=_help_formatter_class(argv),
        epilog=_help_epilog(epilog),
    )


def _add_paths(
    parser: argparse.ArgumentParser,
    *,
    allow_manifest: bool = False,
    build_inputs: bool = False,
    help_text: str | None = None,
    metavar: str | None = None,
) -> None:
    if help_text is None:
        help_text = "Source file(s) or a source directory"
        if build_inputs:
            help_text = "Fortran source file(s) or one semantic .pyi contract; omit with --build-manifest"
        elif allow_manifest:
            help_text = "Source file(s), one .pyi contract, or a source directory; omit with --build-manifest"
    parser.add_argument(
        "paths",
        nargs="*",
        metavar=metavar,
        help=help_text,
    )


def _add_language_option(
    group: argparse._ArgumentGroup,
    *,
    choices: tuple[str, ...] = ("fortran", "c"),
    help_text: str | None = None,
) -> None:
    if help_text is None:
        if choices == ("fortran",):
            help_text = (
                "Wrapper frontend language; compiled wrapping is currently Fortran-only and is usually inferred."
            )
        else:
            help_text = (
                "Frontend language. Recognizable Fortran and .pyi inputs infer it; "
                "C, directories, and unknown suffixes require it."
            )
    group.add_argument(
        "--language",
        choices=choices,
        default=None,
        help=help_text,
    )


def _add_preprocessing_options(
    parser: argparse.ArgumentParser,
    *,
    languages: tuple[str, ...] = ("fortran", "c"),
    group_title: str = "compiler preprocessing",
    compiler_help: str = (
        "Exact compiler or preprocessor executable used for source analysis and internal datatype measurement; "
        "default: gfortran for Fortran, cc for C"
    ),
    include_help: str = "Add DIR to preprocessing include search paths; repeat to preserve search order",
) -> None:
    group = parser.add_argument_group(group_title)
    adapters = ["auto"]
    if "c" in languages:
        adapters.append("gcc-compatible-c")
    if "fortran" in languages:
        adapters.append("gnu-fortran")
    adapters.append("command-template")
    adapter_help = "Preprocessing mode (default: auto)"
    group.add_argument(
        "--preprocessor-adapter",
        choices=tuple(adapters),
        default="auto",
        help=adapter_help,
    )
    group.add_argument(
        "--compiler",
        help=compiler_help,
    )
    if "c" in languages:
        group.add_argument(
            "--compile-commands",
            metavar="PATH",
            help="Read per-file C preprocessing commands from PATH; C only",
        )
    group.add_argument(
        "--preprocess-template",
        metavar="TEMPLATE",
        help="Custom preprocessing command using placeholders such as {source}",
    )
    group.add_argument(
        "-I",
        "--include-dir",
        dest="include_dirs",
        action="append",
        metavar="DIR",
        help=include_help,
    )
    group.add_argument(
        "-D",
        "--define",
        dest="defines",
        action="append",
        metavar="NAME[=VALUE]",
        help="Define a preprocessing macro; repeat as needed",
    )
    group.add_argument(
        "-U",
        "--undef",
        dest="undefs",
        action="append",
        metavar="NAME",
        help="Undefine a preprocessing macro; repeat as needed",
    )
    standards = "f2008 or f2018" if languages == ("fortran",) else "c11, f2008, or f2018"
    group.add_argument(
        "--std",
        metavar="STANDARD",
        help=f"Language standard (for example, {standards})",
    )
    group.add_argument(
        "--compiler-arg",
        dest="compiler_args",
        action="append",
        metavar="ARG",
        help="Additional preprocessing argument; use --compiler-arg=-target for dash-prefixed values",
    )


def _add_include_exposure_options(
    parser: argparse.ArgumentParser,
    *,
    group_title: str = "C include exposure",
) -> None:
    group = parser.add_argument_group(group_title)
    group.add_argument(
        "--include-exposure",
        choices=("reachable-project", "roots-only"),
        default="reachable-project",
        help="C include exposure policy (default: reachable-project)",
    )
    group.add_argument(
        "--public-include",
        dest="public_includes",
        action="append",
        metavar="PATH_OR_PATTERN",
        help="Expose declarations from a matching C include path or glob; repeat as needed",
    )
    group.add_argument(
        "--private-include",
        dest="private_includes",
        action="append",
        metavar="PATH_OR_PATTERN",
        help="Hide declarations from a matching C include path or glob; repeat as needed",
    )


def _add_semantic_interpretation_options(
    parser: argparse.ArgumentParser,
    *,
    group_title: str = "semantic interpretation options",
) -> None:
    """Add options that change how source facts are read into semantic IR.

    These belong to every command that produces semantic IR, because they
    change the IR itself rather than a later wrapper or build choice.
    """
    group = parser.add_argument_group(group_title)
    group.add_argument(
        "--assume-intent-in-scalars",
        action="store_true",
        help=(
            "Treat a primitive scalar dummy that declares no intent as intent(in) instead of the "
            "conservative intent(inout) default, so its value is not returned; a declared intent always wins"
        ),
    )
    group.add_argument(
        "--export-symbols",
        metavar="FILE",
        help="Select exact reachable C functions from a UTF-8 name file; C semantic commands only",
    )


def _add_wrapper_behavior_options(
    parser: argparse.ArgumentParser,
    *,
    group_title: str = "wrapper behavior",
) -> None:
    group = parser.add_argument_group(group_title)
    group.add_argument(
        "--strict-wrapper-names",
        action="store_true",
        help="Reject Python names that require escaping or collision suffixes",
    )
    group.add_argument(
        "--wrapper-compiler-debug",
        action="store_true",
        help="Use debug compiler settings",
    )
    group.add_argument(
        "--wrapper-fortran-flags",
        dest="wrapper_fortran_flags",
        action="extend",
        nargs="+",
        metavar="FLAG",
        help="Compiler flags for generated Fortran bridge sources (for example, -fcheck=bounds)",
    )
    group.add_argument(
        "--wrapper-c-flags",
        dest="wrapper_c_flags",
        action="extend",
        nargs="+",
        metavar="FLAG",
        help="Compiler and extension-link flags for generated C binding sources (for example, -fopenmp)",
    )


def _add_build_manifest_option(
    group: argparse._ArgumentGroup,
    *,
    help_text: str = "Rebuild the extension from an existing prik-build.json",
) -> None:
    group.add_argument(
        "--build-manifest",
        metavar="PATH",
        help=help_text,
    )


def _add_native_compilation_options(group: argparse._ArgumentGroup) -> None:
    group.add_argument(
        "--no-compile-input-sources",
        action="store_true",
        help="Read positional sources without compiling them; require an explicit native implementation",
    )
    group.add_argument(
        "--native-fortran-sources",
        dest="native_fortran_sources",
        action="extend",
        nargs="+",
        metavar="PATH",
        help="Additional Fortran sources to compile without exposing them in the Python API",
    )
    group.add_argument(
        "--native-c-sources",
        dest="native_c_sources",
        action="extend",
        nargs="+",
        metavar="PATH",
        help="Additional C sources to compile without exposing them in the Python API",
    )
    group.add_argument(
        "--native-compile-flags",
        dest="native_compile_flags",
        action="extend",
        nargs="+",
        metavar="FLAG",
        help='Native compiler flags (for example, "-O3 -fopenmp")',
    )
    group.add_argument(
        "--native-c-compile-flags",
        dest="native_c_compile_flags",
        action="extend",
        nargs="+",
        metavar="FLAG",
        help='C implementation compiler flags (for example, "-O3 -std=c11")',
    )


def _add_extension_link_options(group: argparse._ArgumentGroup) -> None:
    group.add_argument(
        "--native-objects",
        dest="native_objects",
        action="extend",
        nargs="+",
        metavar="PATH",
        help="Objects, static libraries, or shared libraries to link",
    )
    group.add_argument(
        "--native-library",
        dest="native_libraries",
        action="extend",
        nargs="+",
        metavar="NAME",
        help="Link NAME as -lNAME; for example, openblas adds -lopenblas",
    )
    group.add_argument(
        "--native-link-item",
        dest="native_link_items",
        action="extend",
        nargs="+",
        metavar="KIND:VALUE",
        help="Add ordered link items: object, archive, shared-library, library, or arg",
    )
    group.add_argument(
        "--native-library-dir",
        dest="native_library_dirs",
        action="extend",
        nargs="+",
        metavar="DIR",
        help="Library search and runtime directories",
    )
    group.add_argument(
        "--lto",
        action="store_true",
        help="Add -flto to generated and native compilation and to the extension link",
    )
    group.add_argument(
        "--collision-adapter",
        dest="collision_adapters",
        action="extend",
        nargs="+",
        metavar="NAME",
        help="Call native symbol NAME through a forwarder defined outside the binding unit",
    )
    group.add_argument(
        "--collision-adapter-all",
        action="store_true",
        help="Call every direct C symbol through a forwarder, not only selected names",
    )
    group.add_argument(
        "--positional-only",
        action="store_true",
        help="Expose wrappers whose arguments are all required as positional-only arg0..argN",
    )


def _add_output_options(
    group: argparse._ArgumentGroup,
    *,
    allow_json: bool = True,
    allow_out: bool = True,
    allow_out_dir: bool = False,
    out_help: str = "Write command output or select its public name",
    out_metavar: str | None = None,
    json_help: str = "Print JSON to standard output",
    out_value_optional: bool = True,
    out_dir_help: str = "Write generated or compiled artifacts under DIR",
) -> None:
    if allow_out:
        out_options = {"nargs": "?", "const": ""} if out_value_optional else {}
        group.add_argument("--out", metavar=out_metavar, help=out_help, **out_options)
    if allow_out_dir:
        group.add_argument("--out-dir", metavar="DIR", help=out_dir_help)
    if allow_json:
        group.add_argument("--json", action="store_true", help=json_help)


def _add_diagnostic_controls(group: argparse._ArgumentGroup, *, allow_verbose: bool = False) -> None:
    if allow_verbose:
        group.add_argument("--verbose", action="store_true", help="Print compiler commands and timed build steps")
    group.add_argument("--no-color", action="store_true", help="Disable ANSI colors in help and diagnostics")
    group.add_argument(
        "--debug",
        action="store_true",
        help="Re-raise command failures and print the full Python traceback",
    )


_PIPELINE_DEFAULTS = {
    "command": "build",
    "parse": False,
    "semantics": False,
    "pyi": False,
    "generate_sources": False,
    "makefile": False,
    "show_vars": False,
    "print_limit": None,
    "vars_limit": None,
    "build_manifest": None,
    "no_compile_input_sources": False,
    "native_fortran_sources": None,
    "native_c_sources": None,
    "native_compile_flags": None,
    "native_c_compile_flags": None,
    "jobs": None,
    "native_objects": None,
    "native_libraries": None,
    "native_link_items": None,
    "native_library_dirs": None,
    "strict_wrapper_names": False,
    "lto": False,
    "collision_adapters": None,
    "collision_adapter_all": False,
    "positional_only": False,
    "assume_intent_in_scalars": False,
    "wrapper_compiler_debug": False,
    "wrapper_fortran_flags": None,
    "wrapper_c_flags": None,
    "out": None,
    "out_dir": None,
    "verbose": False,
    "json": False,
    "no_color": False,
    "debug": False,
    "include_exposure": "reachable-project",
    "compile_commands": None,
    "public_includes": None,
    "private_includes": None,
    "export_symbols": None,
}


def _set_pipeline_defaults(parser: argparse.ArgumentParser, **overrides: object) -> None:
    parser.set_defaults(**(_PIPELINE_DEFAULTS | overrides))


def _add_build_arguments(parser: argparse.ArgumentParser) -> None:
    _set_pipeline_defaults(parser, command="build")
    positional_group = parser.add_argument_group("positional arguments")
    _add_paths(
        positional_group,
        metavar="INPUT",
        help_text="Fortran or C source file(s), one source directory, or exactly one semantic .pyi contract",
    )
    input_group = parser.add_argument_group("input selection")
    _add_language_option(
        input_group,
        choices=("fortran", "c"),
        help_text="Input language (default: fortran; use c for direct C wrappers)",
    )
    parser.set_defaults(language="fortran")
    _add_build_manifest_option(input_group)

    output_group = parser.add_argument_group("output options")
    _add_output_options(
        output_group,
        allow_out_dir=True,
        out_help="Name the Python extension and stable NAME.so library; PATH/NAME.so is also accepted",
        out_metavar="NAME",
        json_help="Print build paths and metadata as JSON",
        out_value_optional=False,
        out_dir_help="Directory for generated sources, objects, and extension (default: ./__prik__)",
    )

    _add_preprocessing_options(
        parser,
        languages=("fortran", "c"),
        group_title="compiler options",
        compiler_help="Fortran or C compiler used throughout the extension build (default: gfortran or cc)",
        include_help="Add a compiler include search directory; repeat as needed",
    )
    _add_semantic_interpretation_options(parser)
    _add_wrapper_behavior_options(parser, group_title="wrapper options")
    native_group = parser.add_argument_group("native options")
    _add_native_compilation_options(native_group)
    native_group.add_argument(
        "--jobs",
        type=_positive_compile_jobs,
        metavar="N",
        help="Limit concurrent compiler processes (default: available CPUs)",
    )
    _add_extension_link_options(native_group)

    diagnostic_group = parser.add_argument_group("diagnostic options")
    _add_diagnostic_controls(diagnostic_group, allow_verbose=True)


def _add_top_level_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--version",
        action="version",
        version=f"prik {__version__}",
        help="Print the installed PRIK version and exit",
    )
    input_group = parser.add_argument_group("positional arguments")
    input_group.add_argument(
        "paths",
        nargs="*",
        metavar="INPUT",
        help="Fortran source file(s) or one semantic .pyi contract",
    )

    build_group = parser.add_argument_group("build options")
    build_group.add_argument(
        "--out",
        metavar="NAME",
        help="Python module name and stable .so alias",
    )
    build_group.add_argument(
        "--out-dir",
        metavar="DIR",
        help="Output directory for generated sources and the extension",
    )
    build_group.add_argument(
        "--compiler",
        metavar="COMPILER",
        help="Input-language compiler used throughout the extension build; default: gfortran",
    )
    build_group.add_argument(
        "-I",
        "--include-dir",
        dest="include_dirs",
        action="append",
        metavar="DIR",
        help="Add an include directory used throughout the extension build",
    )
    build_group.add_argument(
        "--native-compile-flags",
        dest="native_compile_flags",
        action="extend",
        nargs="+",
        metavar="FLAG",
        help="Native implementation compiler flags, for example --native-compile-flags=-O3",
    )
    build_group.add_argument(
        "--jobs",
        type=_positive_compile_jobs,
        metavar="N",
        help="Limit concurrent compiler processes (default: available CPUs)",
    )
    build_group.add_argument(
        "--native-library",
        dest="native_libraries",
        action="extend",
        nargs="+",
        metavar="NAME",
        help=("Link against NAME; for example, --native-library openblas passes -lopenblas to the linker"),
    )
    build_group.add_argument(
        "--lto",
        action="store_true",
        help=(
            "Add -flto to generated and native compilation and to the extension link, "
            "so a collision adapter can be inlined away"
        ),
    )
    build_group.add_argument(
        "--collision-adapter",
        dest="collision_adapters",
        action="extend",
        nargs="+",
        metavar="NAME",
        help=(
            "Call native symbol NAME through a forwarder in a separate translation unit, "
            "so the binding never declares a name Python.h already declares"
        ),
    )
    build_group.add_argument(
        "--collision-adapter-all",
        action="store_true",
        help="Apply --collision-adapter to every direct C symbol",
    )
    build_group.add_argument(
        "--positional-only",
        action="store_true",
        help=(
            "Expose wrappers whose arguments are all required as positional-only, naming them "
            "arg0..argN so a native declaration's parameter names stay out of the Python API"
        ),
    )
    build_group.add_argument(
        "--assume-intent-in-scalars",
        action="store_true",
        help="Treat a scalar dummy with no declared intent as intent(in), so its value is not returned",
    )
    build_group.add_argument(
        "--verbose",
        action="store_true",
        help="Print build commands and timed steps",
    )
    build_group.add_argument(
        "--help-build",
        action="store_true",
        help="Show the full list of build options and exit",
    )


def _top_level_parser(argv: list[str]) -> argparse.ArgumentParser:
    parser = _new_cli_parser(
        prog="python3 -m prik",
        usage=_TOP_LEVEL_USAGE,
        description=_CLI_HELP_DESCRIPTION,
        epilog=_CLI_HELP_EPILOG,
        argv=argv,
    )
    _add_top_level_arguments(parser)
    return parser


def _build_parser(argv: list[str]) -> argparse.ArgumentParser:
    parser = _new_cli_parser(
        prog="python3 -m prik",
        usage=_BUILD_USAGE,
        description="Build a Python extension from Fortran source or a semantic .pyi contract.",
        epilog=_BUILD_HELP_EPILOG,
        argv=argv,
    )
    _add_build_arguments(parser)
    return parser


def _parse_parser(argv: list[str]) -> argparse.ArgumentParser:
    parser = _new_cli_parser(
        prog="python3 -m prik parse",
        usage=_PARSE_USAGE,
        description="Inspect Fortran or C source declarations before semantic conversion.",
        epilog=_PARSE_HELP_EPILOG,
        argv=argv,
    )
    _set_pipeline_defaults(parser, command="parse", parse=True)
    positional_group = parser.add_argument_group("positional arguments")
    _add_paths(
        positional_group,
        metavar="INPUT",
        help_text="One or more Fortran or C source files, or one source directory",
    )
    input_group = parser.add_argument_group("input options")
    _add_language_option(
        input_group,
        help_text="Input language (default: fortran; use c for C inputs)",
    )
    _add_preprocessing_options(
        parser,
        group_title="preprocessing options",
        compiler_help="Compiler used for preprocessing (default: gfortran; cc with --language c)",
        include_help="Add a preprocessing include search directory; repeat as needed",
    )
    _add_include_exposure_options(parser, group_title="C include options")
    report = parser.add_argument_group("report options")
    report.add_argument(
        "--show-vars",
        action="store_true",
        help="Include Fortran scope variables in the human-readable report; Fortran only",
    )
    report.add_argument(
        "--print-limit",
        type=int,
        metavar="N",
        help="Show at most N items in each repeated human-readable report section",
    )
    output_group = parser.add_argument_group("output options")
    _add_output_options(
        output_group,
        json_help="Print the parse report as JSON instead of human-readable text",
        out_help="Write combined JSON to PATH; with no PATH, write one .json file beside each input source",
        out_metavar="PATH",
    )
    diagnostic_group = parser.add_argument_group("diagnostic options")
    _add_diagnostic_controls(diagnostic_group)
    return parser


def _semantics_parser(argv: list[str]) -> argparse.ArgumentParser:
    parser = _new_cli_parser(
        prog="python3 -m prik semantics",
        usage=_SEMANTICS_USAGE,
        description="Convert Fortran or C source code into language-neutral semantic IR models.",
        epilog=_SEMANTICS_HELP_EPILOG,
        argv=argv,
    )
    _set_pipeline_defaults(parser, command="semantics", semantics=True)
    positional_group = parser.add_argument_group("positional arguments")
    _add_paths(
        positional_group,
        metavar="INPUT",
        help_text="One or more Fortran or C source files, or one source directory",
    )
    input_group = parser.add_argument_group("input options")
    _add_language_option(
        input_group,
        help_text="Input language (default: fortran; use c for C inputs)",
    )
    _add_preprocessing_options(
        parser,
        group_title="preprocessing options",
        compiler_help=(
            "Compiler used for preprocessing and datatype measurement (default: gfortran; cc with --language c)"
        ),
        include_help="Add a preprocessing include search directory; repeat as needed",
    )
    _add_include_exposure_options(parser, group_title="C include options")
    _add_semantic_interpretation_options(parser)
    output_group = parser.add_argument_group("output options")
    _add_output_options(
        output_group,
        allow_json=False,
        out_help=("Write combined JSON to PATH; with no PATH, write one .json file beside each input source"),
        out_metavar="PATH",
    )
    diagnostic_group = parser.add_argument_group("diagnostic options")
    _add_diagnostic_controls(diagnostic_group)
    return parser


def _generate_parser(argv: list[str]) -> argparse.ArgumentParser:
    parser = _new_cli_parser(
        prog="python3 -m prik generate",
        usage=_GENERATE_USAGE,
        description="Generate semantic .pyi contracts or wrapper build artifacts without compiling.",
        epilog=_GENERATE_HELP_EPILOG,
        argv=argv,
    )
    _set_pipeline_defaults(parser, command="generate")
    modes = parser.add_argument_group("generation modes").add_mutually_exclusive_group(required=True)
    modes.add_argument(
        "--pyi",
        action="store_true",
        help="Generate semantic .pyi contracts from Fortran or C source",
    )
    modes.add_argument(
        "--sources",
        dest="generate_sources",
        action="store_true",
        help="Generate wrapper sources without compiling",
    )
    modes.add_argument(
        "--makefile",
        action="store_true",
        help="Generate wrapper sources and Makefile.prik without compiling",
    )
    positional_group = parser.add_argument_group("positional arguments")
    _add_paths(
        positional_group,
        metavar="INPUT",
        help_text="Source input(s), or one semantic .pyi contract for --sources/--makefile",
    )
    input_group = parser.add_argument_group("input options")
    _add_language_option(
        input_group,
        help_text="Input language (default: fortran; use c only with --pyi)",
    )
    _add_build_manifest_option(
        input_group,
        help_text="Read an existing prik-build.json and regenerate wrapper artifacts",
    )
    _add_preprocessing_options(
        parser,
        group_title="compiler and preprocessing options",
        compiler_help=(
            "Compiler used for source analysis and wrapper build files (default: gfortran; cc with --language c)"
        ),
        include_help="Add an include search directory; repeat as needed",
    )
    _add_include_exposure_options(parser, group_title="C include options")
    _add_semantic_interpretation_options(parser)
    _add_wrapper_behavior_options(parser, group_title="wrapper options")
    native_group = parser.add_argument_group("native options")
    _add_native_compilation_options(native_group)
    _add_extension_link_options(native_group)
    output_group = parser.add_argument_group("output options")
    _add_output_options(
        output_group,
        allow_out_dir=True,
        json_help="Print generated artifact metadata as JSON",
        out_help="Contract package directory for --pyi; bare --out writes beside inputs",
        out_metavar="PATH",
        out_dir_help="Artifact directory for --sources/--makefile",
    )
    diagnostic_group = parser.add_argument_group("diagnostic options")
    _add_diagnostic_controls(diagnostic_group)
    return parser


def _probe_parser(argv: list[str]) -> argparse.ArgumentParser:
    parser = _new_cli_parser(
        prog="python3 -m prik probe",
        usage=_PROBE_USAGE,
        description="Probe compiler-target datatype sizes, alignment, and ABI facts.",
        epilog=_PROBE_HELP_EPILOG,
        argv=argv,
    )
    parser.set_defaults(command="probe")
    target = parser.add_argument_group("probe options")
    target.add_argument(
        "--language",
        choices=("fortran", "c"),
        required=True,
        help="Language to probe",
    )
    target.add_argument(
        "--compiler",
        required=True,
        help="Native or cross compiler used to build the probe",
    )
    target.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Render the measured report as JSON or as a Markdown table",
    )
    target.add_argument(
        "--expr",
        "--expression",
        dest="expressions",
        action="append",
        default=[],
        metavar="EXPR",
        help="Measure a Fortran integer expression instead of the mapping table; repeat as needed",
    )
    compiler = parser.add_argument_group("execution options")
    compiler.add_argument(
        "-I",
        "--include-dir",
        dest="include_dirs",
        action="append",
        default=[],
        metavar="DIR",
        help="Add a probe include search directory; repeat as needed",
    )
    compiler.add_argument(
        "-D",
        "--define",
        dest="defines",
        action="append",
        default=[],
        metavar="NAME[=VALUE]",
        help="Define a probe macro; repeat as needed",
    )
    compiler.add_argument(
        "-U",
        "--undef",
        dest="undefs",
        action="append",
        default=[],
        metavar="NAME",
        help="Undefine a probe macro; repeat as needed",
    )
    compiler.add_argument(
        "--std",
        metavar="STANDARD",
        help="Language standard (for example, c11 or f2018)",
    )
    compiler.add_argument(
        "--compiler-arg",
        dest="compiler_args",
        action="append",
        default=[],
        metavar="ARG",
        help="Additional compiler argument; use --compiler-arg=-target for dash-prefixed values",
    )
    compiler.add_argument(
        "--runner",
        action="append",
        default=[],
        metavar="ARG",
        help="Prepend a cross-target runner argument; repeat in command order",
    )
    compiler.add_argument("--cache-dir", metavar="DIR", help="Read and write reusable probe results under DIR")
    compiler.add_argument("--refresh", action="store_true", help="Ignore reusable results and probe again")
    output = parser.add_argument_group("output options")
    output.add_argument("--out", metavar="PATH", help="Write the probe report to PATH instead of standard output")
    diagnostic = parser.add_argument_group("diagnostic options")
    _add_diagnostic_controls(diagnostic)
    return parser


_COMMAND_PARSERS = {
    "parse": _parse_parser,
    "semantics": _semantics_parser,
    "generate": _generate_parser,
    "probe": _probe_parser,
}


def _parser_for_argv(argv: list[str]) -> tuple[argparse.ArgumentParser, list[str]]:
    if "--help-build" in argv:
        build_help_argv = ["--help" if value == "--help-build" else value for value in argv]
        return _build_parser(argv), build_help_argv
    if not argv or argv[0] in {"-h", "--help", "--version"}:
        return _top_level_parser(argv), argv
    command = argv[0]
    if command in _COMMAND_PARSERS:
        command_argv = argv[1:]
        return _COMMAND_PARSERS[command](command_argv), command_argv
    return _build_parser(argv), argv


def _argv_uses_option(argv: list[str], option: str) -> bool:
    return any(value == option or value.startswith(f"{option}=") for value in argv)


def _probe_expression_output(args: argparse.Namespace, target_options: dict[str, object]) -> str:
    """Measure the requested Fortran expressions and render the chosen format.

    Preprocessing options apply here because each expression is compiled from
    generated source. The measured report is the record; Markdown converts it.
    """
    if args.language == "c":
        raise ValueError("--expr is supported only for --language fortran")
    config = PreprocessingConfig(
        mode="compiler",
        compiler=args.compiler,
        include_dirs=args.include_dirs,
        defines=args.defines,
        undefs=args.undefs,
        std=args.std,
        compiler_args=args.compiler_args,
    )
    report = probe_fortran_type_expressions_cached(config, args.expressions, **target_options)
    if args.format == "markdown":
        return expression_probe_markdown(report)
    return json.dumps(report.to_dict(), indent=2)


def _probe_mapping_output(args: argparse.Namespace, target_options: dict[str, object]) -> str:
    """Measure the standard type mapping table and render the chosen format.

    The mapping inventory is fixed, so preprocessing options cannot affect it
    and are rejected instead of silently ignored. The measured report is the
    record; Markdown converts it.
    """
    if args.include_dirs or args.defines or args.undefs or args.std:
        raise ValueError(
            "the type mapping report accepts compiler, compiler arguments, runner, cache, "
            "and refresh only; add --expr to probe preprocessed expressions"
        )
    builder = c_type_mapping_report if args.language == "c" else fortran_type_mapping_report
    report = builder(compiler=args.compiler, compiler_args=args.compiler_args, **target_options)
    if args.format == "markdown":
        return type_mapping_markdown(report)
    return json.dumps(report, indent=2)


def _probe_output(args: argparse.Namespace) -> str:
    """Select the probe report and serialize it in the requested format.

    ``--expr`` selects the measured expression report; without it the standard
    type mapping table is measured. Both reports support both formats.
    """
    target_options = {
        "runner": args.runner or None,
        "cache_dir": args.cache_dir,
        "refresh": args.refresh,
    }
    if args.expressions:
        return _probe_expression_output(args, target_options)
    return _probe_mapping_output(args, target_options)


def _run_probe_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        for define in args.defines:
            validate_macro_name(define, "--define/-D")
        for undef in args.undefs:
            validate_macro_name(undef, "--undef/-U")
        output = _probe_output(args)
    except (PreprocessingError, ValueError) as exc:
        if args.debug or _env_flag("PRIK_DEBUG"):
            raise
        parser.error(str(exc))
    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


def main(argv: list[str] | None = None) -> int:
    active_argv = list(sys.argv[1:] if argv is None else argv)
    parser, parser_argv = _parser_for_argv(active_argv)
    args = parser.parse_args(parser_argv)
    args._explicit_language = _argv_uses_option(parser_argv, "--language")
    args._explicit_preprocessor_adapter = _argv_uses_option(parser_argv, "--preprocessor-adapter")
    if not active_argv:
        parser.print_help()
        return 0
    if args.command == "probe":
        return _run_probe_command(args, parser)
    args.language = _resolve_language(args.paths, args.language, parser)
    preprocessing = _build_preprocessing_config(args, parser)
    print_limit = _validate_main_options(args, parser)
    if _is_wrapper_build(args):
        result = _run_wrap_build_with_diagnostics(args, preprocessing)
        if result is None:
            return 1
        _print_wrap_build_output(args, result)
        return 0
    reports = _run_stage_reports_with_diagnostics(args, preprocessing)
    if reports is None:
        return 1
    parse_payload, semantic_payload = reports
    payload = _select_main_payload(args, parse_payload, semantic_payload)
    if _write_main_output(args, parser, payload, semantic_payload):
        return 0
    _print_main_output(args, payload, parse_payload, semantic_payload, print_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
