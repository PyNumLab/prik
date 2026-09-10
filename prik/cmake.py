"""Generate small CMake projects that use PRIK's packaged CMake helper."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import sys
import sysconfig


@dataclass(frozen=True)
class CMakeProjectResult:
    """Describe a generated standalone CMake project."""

    module_name: str
    output_dir: Path
    cmake_lists: Path

    def to_dict(self) -> dict[str, object]:
        """Return the generated project paths in the CLI result shape."""
        return {
            "cmake_project": str(self.cmake_lists),
            "module_name": self.module_name,
            "output_dir": str(self.output_dir),
        }


@dataclass(frozen=True)
class _CMakeModuleInputs:
    """Normalized source declarations for one generated helper call."""

    module_name: str
    semantic_sources: tuple[Path, ...]
    contract: Path | None
    native_fortran: tuple[Path, ...]
    native_c: tuple[Path, ...]


def _absolute_paths(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    return tuple(Path(path).resolve() for path in paths)


def _cmake_string(value: str | Path) -> str:
    """Quote one literal for a generated CMake string."""
    return '"' + str(value).replace("\\", "/").replace('"', '\\"') + '"'


def _relative_path(path: Path, base: Path) -> str:
    return Path(os.path.relpath(path, base)).as_posix()


def _helper_path() -> Path:
    """Find the helper in a checkout or in the installed data directory."""
    candidates = [Path(__file__).resolve().parent.parent / "cmake" / "UsePRIK.cmake"]
    data_root = sysconfig.get_path("data")
    if data_root:
        candidates.append(Path(data_root) / "share" / "prik" / "cmake" / "UsePRIK.cmake")
    candidates.append(Path(sys.prefix) / "share" / "prik" / "cmake" / "UsePRIK.cmake")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("Packaged PRIK CMake helper not found: cmake/UsePRIK.cmake")


def cmake_module_dir() -> Path:
    """Return the directory containing PRIK's packaged CMake helper."""
    return _helper_path().parent


def _append_block(lines: list[str], keyword: str, values: Iterable[str], *, base: Path) -> None:
    resolved = tuple(Path(value) for value in values)
    if not resolved:
        return
    lines.append(f"    {keyword}")
    lines.extend(f"        {_cmake_string(_relative_path(path, base))}" for path in resolved)


def _append_values(lines: list[str], keyword: str, values: Iterable[str]) -> None:
    values = tuple(str(value) for value in values)
    if not values:
        return
    lines.append(f"    {keyword}")
    lines.extend(f"        {_cmake_string(value)}" for value in values)


def _flag_values(raw_flags: Iterable[str] | None) -> tuple[str, ...]:
    values: list[str] = []
    for raw in raw_flags or ():
        values.extend(shlex.split(str(raw)))
    return tuple(values)


def _prik_args(args) -> tuple[str, ...]:
    """Keep generation-affecting CLI options in the generated CMake call."""
    result: list[str] = []

    def add_option(option: str, value: object | None = None) -> None:
        if value is None:
            result.append(option)
        else:
            result.append(f"{option}={value}")

    for option, values in (
        ("--define", args.defines),
        ("--undef", args.undefs),
        ("--compiler-arg", args.compiler_args),
        ("--public-include", args.public_includes),
        ("--private-include", args.private_includes),
    ):
        for value in values or ():
            add_option(option, value)
    for option, value in (
        ("--preprocessor-adapter", args.preprocessor_adapter),
        ("--preprocess-template", args.preprocess_template),
        ("--std", args.std),
        ("--compile-commands", args.compile_commands),
    ):
        if value:
            add_option(option, value)
    if args.include_exposure != "reachable-project":
        add_option("--include-exposure", args.include_exposure)
    for option, values in (("--collision-adapter", args.collision_adapters),):
        if values:
            result.extend(f"{option}={value}" for value in values)
    for option, enabled in (
        ("--strict-wrapper-names", args.strict_wrapper_names),
        ("--assume-intent-in-scalars", args.assume_intent_in_scalars),
        ("--collision-adapter-all", args.collision_adapter_all),
        ("--positional-only", args.positional_only),
    ):
        if enabled:
            add_option(option)
    return tuple(result)


def _link_values(
    args,
    *,
    base: Path,
    native_link_items: Iterable[dict[str, object]],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    libraries = [str(Path(path).resolve()) for path in (args.native_objects or ())]
    for item in native_link_items:
        kind = item["kind"]
        if kind in {"object", "archive", "shared_library"}:
            libraries.append(str(Path(str(item["path"])).resolve()))
        elif kind == "named_library":
            libraries.append(str(item["name"]))
        elif kind == "linker_argument":
            # CMake permits private linker flags among target_link_libraries
            # items, which retains the explicit PRIK link-item order.
            libraries.append(str(item["argument"]))
        else:  # pragma: no cover - the CLI normalizer rejects this first.
            raise ValueError(f"Unsupported native link item kind: {kind!r}")
    libraries.extend(_flag_values(args.native_libraries))
    options: list[str] = [f"-L{Path(path).resolve()}" for path in (args.native_library_dirs or ())]
    return tuple(
        _relative_path(Path(value), base) if Path(value).is_absolute() else value for value in libraries
    ), tuple(options)


def _module_inputs(*, paths: Iterable[str | Path], args) -> _CMakeModuleInputs:
    input_paths = _absolute_paths(paths)
    if not input_paths:
        raise ValueError("CMake generation requires at least one input")
    if any(path.is_dir() for path in input_paths):
        raise ValueError("generate --cmake expects source files or one semantic .pyi contract, not directories")

    contract = input_paths[0] if input_paths[0].suffix.lower() == ".pyi" else None
    if contract is not None and len(input_paths) != 1:
        raise ValueError("generate --cmake accepts one semantic .pyi contract")
    if contract is not None:
        default_module_name = contract.parent.name if contract.name == "__init__.pyi" else contract.stem
    else:
        default_module_name = input_paths[0].stem
    module_name = args.module_name or default_module_name
    if not module_name.isascii() or not module_name.isidentifier():
        raise ValueError(f"CMake generation requires a valid ASCII Python/C module name: {module_name!r}")

    native_fortran = _absolute_paths(args.native_fortran_sources or ())
    native_c = _absolute_paths(args.native_c_sources or ())
    has_link_implementation = bool(args.native_objects or args.native_libraries or args.native_link_items)
    if args.no_compile_input_sources and not native_fortran and not native_c and not has_link_implementation:
        raise ValueError(
            "generate --cmake --no-compile-input-sources requires native implementation sources or libraries"
        )
    return _CMakeModuleInputs(
        module_name=module_name,
        semantic_sources=input_paths,
        contract=contract,
        native_fortran=native_fortran,
        native_c=native_c,
    )


def _project_preamble(*, module_name: str, languages: str) -> list[str]:
    return [
        "cmake_minimum_required(VERSION 3.20)",
        "",
        f"project({module_name} LANGUAGES {languages})",
        "",
        "find_package(",
        "    Python",
        "    COMPONENTS Interpreter Development.Module",
        "    REQUIRED",
        ")",
        "",
        "execute_process(",
        '    COMMAND "${Python_EXECUTABLE}" -c "from prik.cmake import cmake_module_dir; print(cmake_module_dir().as_posix())"',
        "    RESULT_VARIABLE PRIK_CMAKE_MODULE_RESULT",
        "    OUTPUT_VARIABLE PRIK_CMAKE_MODULE_DIR",
        "    ERROR_VARIABLE PRIK_CMAKE_MODULE_ERROR",
        "    OUTPUT_STRIP_TRAILING_WHITESPACE",
        ")",
        "if(NOT PRIK_CMAKE_MODULE_RESULT EQUAL 0)",
        '    message(FATAL_ERROR "Cannot locate UsePRIK.cmake: ${PRIK_CMAKE_MODULE_ERROR}")',
        "endif()",
        'list(APPEND CMAKE_MODULE_PATH "${PRIK_CMAKE_MODULE_DIR}")',
        "include(UsePRIK)",
        "",
        "prik_add_module(",
        f"    {module_name}",
    ]


def _append_source_declarations(
    lines: list[str],
    inputs: _CMakeModuleInputs,
    *,
    language: str,
    no_compile_input_sources: bool,
    base: Path,
) -> None:
    if no_compile_input_sources:
        lines.append("    NO_COMPILE_INPUT_SOURCES")
    if inputs.contract is not None:
        lines.append(f"    CONTRACT {_cmake_string(_relative_path(inputs.contract, base))}")
    elif not no_compile_input_sources and not inputs.native_fortran and not inputs.native_c:
        keyword = "C_SOURCES" if language == "c" else "FORTRAN_SOURCES"
        _append_block(lines, keyword, inputs.semantic_sources, base=base)
        return
    else:
        _append_block(lines, "SOURCES", inputs.semantic_sources, base=base)
    _append_block(lines, "FORTRAN_SOURCES", inputs.native_fortran, base=base)
    _append_block(lines, "C_SOURCES", inputs.native_c, base=base)


def _append_build_options(
    lines: list[str],
    *,
    args,
    project_dir: Path,
    native_link_items: Iterable[dict[str, object]],
) -> None:
    _append_block(lines, "INCLUDE_DIRS", _absolute_paths(args.include_dirs or ()), base=project_dir)
    fortran_flags = _flag_values(args.native_compile_flags)
    c_flags = _flag_values(args.native_c_compile_flags)
    wrapper_fortran_flags = _flag_values(args.wrapper_fortran_flags)
    wrapper_c_flags = _flag_values(args.wrapper_c_flags)
    libraries, link_options = _link_values(args, base=project_dir, native_link_items=native_link_items)
    _append_values(lines, "FORTRAN_FLAGS", fortran_flags)
    _append_values(lines, "C_FLAGS", c_flags)
    _append_values(lines, "WRAPPER_FORTRAN_FLAGS", wrapper_fortran_flags)
    _append_values(lines, "WRAPPER_C_FLAGS", wrapper_c_flags)
    _append_values(lines, "LINK_LIBRARIES", libraries)
    _append_values(lines, "LINK_OPTIONS", link_options)
    if args.native_linker_language:
        lines.append(f"    LINKER_LANGUAGE {args.native_linker_language.capitalize()}")
    if not args.standard_logicals:
        lines.append("    NO_STANDARD_LOGICALS")
    _append_values(lines, "PRIK_ARGS", _prik_args(args))


def write_cmake_project(
    *,
    paths: Iterable[str | Path],
    output_dir: str | Path,
    language: str,
    args,
    native_link_items: Iterable[dict[str, object]] = (),
) -> CMakeProjectResult:
    """Write a readable standalone project backed by ``UsePRIK.cmake``."""
    project_dir = Path(output_dir).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    inputs = _module_inputs(paths=paths, args=args)
    cmake_module_dir()
    project_languages = (
        "C Fortran"
        if language == "fortran" or inputs.native_fortran or args.native_linker_language == "fortran"
        else "C"
    )
    lines = _project_preamble(module_name=inputs.module_name, languages=project_languages)
    _append_source_declarations(
        lines,
        inputs,
        language=language,
        no_compile_input_sources=args.no_compile_input_sources,
        base=project_dir,
    )
    _append_build_options(lines, args=args, project_dir=project_dir, native_link_items=native_link_items)
    lines.append(")")
    if args.lto:
        lines.extend(("", f"set_property(TARGET {inputs.module_name} PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)"))

    cmake_lists = project_dir / "CMakeLists.txt"
    cmake_lists.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return CMakeProjectResult(module_name=inputs.module_name, output_dir=project_dir, cmake_lists=cmake_lists)
