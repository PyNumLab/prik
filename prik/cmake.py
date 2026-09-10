"""Generate small CMake projects that use PRIK's packaged CMake helper."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import sys
import sysconfig

from prik.naming.generated_files import (
    adapter_source_name,
    binding_source_name,
    bridge_source_name,
    wrapper_header_name,
)


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
class StructuralLayout:
    """The generated-file graph one CMake module target declares.

    Every field follows from the module name and the declared build structure,
    so a build system can create its targets before any source is parsed. The
    semantic pipeline never runs to produce this; it only fills the declared
    files in later.
    """

    module_name: str
    output_dir: Path
    fortran: bool
    linker_language: str
    abi_flags: Mapping[str, tuple[str, ...]]

    @property
    def generated_sources(self) -> tuple[Path, ...]:
        """Return every generated compilation unit, in compiler order.

        The optional adapter and bridge units are listed whether or not the
        wrapper turns out to need them; generation writes a harmless stub for
        one it does not, which keeps this list stable across semantic edits.
        """
        bridge = (self.output_dir / bridge_source_name(self.module_name),) if self.fortran else ()
        return (
            *bridge,
            self.output_dir / binding_source_name(self.module_name),
            self.output_dir / adapter_source_name(self.module_name),
        )

    @property
    def generated_files(self) -> tuple[Path, ...]:
        """Return the compilation units plus every other deterministic output."""
        # Imported here so a structural query does not pay for the support
        # module's own NumPy dependency.
        from prik.compiler.native_support import BINDING_SUPPORT_IMPORT, native_support_output_paths

        return (
            *self.generated_sources,
            self.output_dir / wrapper_header_name(self.module_name),
            *native_support_output_paths((BINDING_SUPPORT_IMPORT,), prik_dirpath=self.output_dir),
        )

    @property
    def depfile(self) -> Path:
        """Return the depfile generation writes for its semantic inputs."""
        return self.output_dir / f"prik-{self.module_name}.d"

    def to_dict(self) -> dict[str, object]:
        """Return the payload a build integration reads at configure time."""
        return {
            "structural_plan": True,
            "module_name": self.module_name,
            "generated_sources": [str(path) for path in self.generated_sources],
            "generated_files": [str(path) for path in self.generated_files],
            "depfile": str(self.depfile),
            "linker_language": self.linker_language,
            "required_abi_flags": {language: list(flags) for language, flags in self.abi_flags.items()},
        }


def structural_layout(
    *,
    module_name: str,
    output_dir: str | Path,
    language: str,
    native_fortran_sources: Iterable[str | Path] = (),
    linker_language: str | None = None,
    fortran_compiler: str | None = None,
    standard_logicals: bool = True,
) -> StructuralLayout:
    """Derive one module's generated-file graph from build structure alone.

    A module is Fortran-capable when its own language is Fortran, when it
    contributes native Fortran sources, or when the caller has already required
    the Fortran link driver. That is the whole rule: nothing here reads a
    source file, completes policy, or plans a wrapper.
    """
    if not module_name.isascii() or not module_name.isidentifier():
        raise ValueError(f"CMake structural planning requires a valid ASCII Python/C module name: {module_name!r}")
    requested_linker_language = (linker_language or "").lower() or None
    if requested_linker_language not in (None, "c", "fortran"):
        raise ValueError(f"Unsupported linker language: {linker_language!r}")
    fortran = language == "fortran" or bool(tuple(native_fortran_sources)) or requested_linker_language == "fortran"
    return StructuralLayout(
        module_name=module_name,
        output_dir=Path(output_dir).resolve(),
        fortran=fortran,
        linker_language=requested_linker_language or ("fortran" if fortran else "c"),
        abi_flags=_structural_abi_flags(
            fortran_compiler if fortran else None,
            standard_logicals=standard_logicals,
        ),
    )


def _structural_abi_flags(fortran_compiler: str | None, *, standard_logicals: bool) -> Mapping[str, tuple[str, ...]]:
    """Return mandatory ABI flags from the compiler profile, not from semantics.

    The profile follows from the driver's name, so this stays a table lookup.
    An unrecognized driver contributes no mandatory flag rather than failing
    configuration; the real generation step still validates the toolchain.
    """
    if fortran_compiler is None:
        return {}
    from prik.compiler.compiler_profiles import available_compilers, fortran_compiler_family

    try:
        _token, vendor, _default_c = fortran_compiler_family(fortran_compiler)
    except ValueError:
        return {}
    if not standard_logicals:
        return {}
    flags = available_compilers[vendor].get("fortran", {}).get("logical_interop_flags", ())
    return {"fortran": tuple(str(flag) for flag in flags)} if flags else {}


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


def _link_item_path(path: Path, base: Path) -> str:
    """Keep a prebuilt link input recognizable to CMake as a filesystem path.

    ``target_link_libraries()`` distinguishes file paths from library names and
    linker flags by the item's own text, so a bare relative path would leave
    that category ambiguous. Rooting the path in ``CMAKE_CURRENT_LIST_DIR``
    keeps the generated project relocatable alongside its inputs.
    """
    try:
        relative = _relative_path(path, base)
    except ValueError:  # pragma: no cover - only reachable across Windows drives
        return path.as_posix()
    return "${CMAKE_CURRENT_LIST_DIR}/" + relative


def _link_values(
    args,
    *,
    base: Path,
    native_link_items: Iterable[dict[str, object]],
) -> tuple[str, ...]:
    libraries = [_link_item_path(Path(path).resolve(), base) for path in (args.native_objects or ())]
    for item in native_link_items:
        kind = item["kind"]
        if kind in {"object", "archive", "shared_library"}:
            libraries.append(_link_item_path(Path(str(item["path"])).resolve(), base))
        elif kind == "named_library":
            libraries.append(str(item["name"]))
        elif kind == "linker_argument":
            # CMake permits private linker flags among target_link_libraries
            # items, which retains the explicit PRIK link-item order.
            libraries.append(str(item["argument"]))
        else:  # pragma: no cover - the CLI normalizer rejects this first.
            raise ValueError(f"Unsupported native link item kind: {kind!r}")
    libraries.extend(_flag_values(args.native_libraries))
    return tuple(libraries)


def _validate_c_suffixes(paths: Iterable[Path]) -> None:
    """Reject a ``.C`` suffix, which CMake compiles as C++ rather than C.

    PRIK plans these sources as C, so letting CMake choose its own language for
    them would compile the plan with the wrong compiler.
    """
    for path in paths:
        if path.suffix != ".c" and path.suffix.lower() == ".c":
            raise ValueError(
                f"PRIK C sources used through CMake must use the .c suffix; .C is interpreted as C++ by CMake: {path}"
            )


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


def _project_preamble(*, module_name: str, languages: str, lto: bool = False) -> list[str]:
    lines = [
        "cmake_minimum_required(VERSION 3.21)",
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
    ]
    if lto:
        lines.extend(("set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)", ""))
    lines.extend(
        [
            "prik_add_module(",
            f"    {module_name}",
        ]
    )
    return lines


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
        lines.append(f"    NATIVE_LANGUAGE {language.capitalize()}")
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
    libraries = _link_values(args, base=project_dir, native_link_items=native_link_items)
    _append_values(lines, "FORTRAN_FLAGS", fortran_flags)
    _append_values(lines, "C_FLAGS", c_flags)
    _append_values(lines, "WRAPPER_FORTRAN_FLAGS", wrapper_fortran_flags)
    _append_values(lines, "WRAPPER_C_FLAGS", wrapper_c_flags)
    _append_values(lines, "LINK_LIBRARIES", libraries)
    # A native library directory is both a link-time search path and a runtime
    # search path, so it reaches CMake as a link directory rather than a raw
    # -L flag that carries no runtime meaning.
    _append_block(lines, "LIBRARY_DIRS", _absolute_paths(args.native_library_dirs or ()), base=project_dir)
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
    if language == "c" and inputs.contract is None:
        _validate_c_suffixes(inputs.semantic_sources)
    _validate_c_suffixes(inputs.native_c)
    cmake_module_dir()
    project_languages = (
        "C Fortran"
        if language == "fortran" or inputs.native_fortran or args.native_linker_language == "fortran"
        else "C"
    )
    lines = _project_preamble(module_name=inputs.module_name, languages=project_languages, lto=args.lto)
    _append_source_declarations(
        lines,
        inputs,
        language=language,
        no_compile_input_sources=args.no_compile_input_sources,
        base=project_dir,
    )
    _append_build_options(lines, args=args, project_dir=project_dir, native_link_items=native_link_items)
    lines.append(")")

    cmake_lists = project_dir / "CMakeLists.txt"
    cmake_lists.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return CMakeProjectResult(module_name=inputs.module_name, output_dir=project_dir, cmake_lists=cmake_lists)
