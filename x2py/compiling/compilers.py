"""Run explicit native object and extension-link compiler commands."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import cache
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import warnings

from .objects import ObjectFile
from .compiler_profiles import available_compilers, fortran_compiler_family, vendors

__all__ = ("Compiler", "get_condaless_search_path")


def get_condaless_search_path(conda_warnings: str = "basic") -> str:
    """Return ``PATH`` without Conda-managed entries when locating compilers."""

    path_separator = os.pathsep
    entries = tuple(entry for entry in os.environ.get("PATH", "").split(path_separator) if entry)
    conda_markers = ("conda", "anaconda", "miniconda")
    conda_entries = tuple(entry for entry in entries if any(marker in Path(entry).parts for marker in conda_markers))
    if conda_entries and conda_warnings in {"basic", "verbose"}:
        message = "Conda paths are ignored while locating native compilers."
        if conda_warnings == "verbose":
            message += "\nIgnored PATH entries:\n" + "\n".join(conda_entries)
        warnings.warn(message, stacklevel=2)
    return path_separator.join(entry for entry in entries if entry not in conda_entries)


class Compiler:
    """Compile explicit object files and link an explicit extension object list."""

    @classmethod
    def from_fortran_executable(
        cls,
        executable: str = "gfortran",
        *,
        debug: bool = False,
        execute_commands: bool = True,
        search_path: str | None = None,
    ) -> Compiler:
        """Create the coherent vendor toolchain selected by one Fortran driver."""
        resolved_fortran = shutil.which(executable, path=search_path)
        if resolved_fortran is None:
            raise FileNotFoundError(f"Could not find compiler executable: {executable}")

        token, vendor, default_c = fortran_compiler_family(resolved_fortran)
        fortran_name = Path(resolved_fortran).name
        c_names = tuple(dict.fromkeys((fortran_name.replace(token, default_c, 1), default_c)))
        c_candidates = (
            *(str(Path(resolved_fortran).parent / name) for name in c_names),
            *c_names,
        )
        resolved_c = next(
            (candidate for name in c_candidates if (candidate := shutil.which(name, path=search_path)) is not None),
            None,
        )
        if resolved_c is None:
            names = ", ".join(c_names)
            raise FileNotFoundError(
                f"Could not find the {vendor} C compiler matching {resolved_fortran}: expected {names}"
            )
        return cls(
            vendor,
            debug=debug,
            execute_commands=execute_commands,
            search_path=search_path,
            executables={"fortran": resolved_fortran, "c": resolved_c},
        )

    def __init__(
        self,
        vendor: str,
        debug: bool = False,
        *,
        execute_commands: bool = True,
        search_path: str | None = None,
        executables: Mapping[str, str] | None = None,
    ) -> None:
        self._toolchain = self._load_toolchain(vendor)
        self._debug = debug
        self._execute_commands = execute_commands
        self._search_path = search_path
        self._executables = {str(language): str(command) for language, command in (executables or {}).items()}
        unsupported = set(self._executables) - set(self._toolchain)
        if unsupported:
            language = sorted(unsupported)[0]
            raise ValueError(f"Toolchain does not support an executable override for {language!r}")
        self._command_log: list[tuple[str, ...]] = []

    @property
    def command_log(self) -> tuple[tuple[str, ...], ...]:
        """Return exact compiler commands in execution order."""

        return tuple(self._command_log)

    def compile_object(self, object_file: ObjectFile, *, verbose: bool | int = False) -> None:
        """Compile exactly one source file into its declared object path."""

        object_file.object_path.parent.mkdir(parents=True, exist_ok=True)
        language = self._language(object_file.language)
        executable = self._executable(language, object_file.tools)
        command = [
            executable,
            *self._flags(
                language,
                object_file.tools,
                object_file.flags,
                executable=executable if self._execute_commands else None,
            ),
            "-c",
            *self._path_flags("-I", self._include_dirs(language, object_file.tools, object_file.include_dirs)),
            str(object_file.source),
            "-o",
            str(object_file.object_path),
        ]
        if object_file.language == "fortran":
            command.extend((str(language["module_output_flag"]), str(object_file.object_path.parent)))
        self._run_or_record(command, verbose)

    def link_extension(
        self,
        *,
        module_name: str,
        output_dir: str | Path,
        language: str,
        objects: Iterable[ObjectFile | str | Path],
        link_args: Iterable[str] = (),
        library_dirs: Iterable[str | Path] = (),
        libraries: Iterable[str] = (),
        flags: Iterable[str] = (),
        tools: Iterable[str] = ("python",),
        verbose: bool | int = False,
    ) -> Path:
        """Link the supplied objects and ordered native link arguments once."""

        object_items = tuple(objects)
        object_paths = tuple(item.object_path if isinstance(item, ObjectFile) else Path(item) for item in object_items)
        if not object_paths:
            raise ValueError("Extension linking requires at least one object file")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        language_info = self._language(language)
        object_files = tuple(item for item in object_items if isinstance(item, ObjectFile))
        selected_tools = {str(tool) for tool in tools}
        selected_tools.update(tool for item in object_files for tool in item.tools)
        selected_tools.add("python")
        selected_library_dirs = self._ordered_paths(
            (*library_dirs, *(directory for item in object_files for directory in item.library_dirs))
        )
        selected_libraries = self._ordered_strings(
            (*libraries, *(library for item in object_files for library in item.libraries))
        )
        resolved_library_dirs = self._library_dirs(language_info, selected_tools, selected_library_dirs)
        extension_path = output_path / f"{module_name}{language_info['python']['shared_suffix']}"
        executable = self._executable(language_info, selected_tools)
        if verbose:
            print(f">> Create shared library: {extension_path}")
        command = [
            executable,
            "-shared",
            *self._flags(
                language_info,
                selected_tools - {"python"},
                flags,
                executable=executable if self._execute_commands else None,
            ),
            *self._path_flags("-L", resolved_library_dirs),
            *self._path_flags("-Wl,-rpath", resolved_library_dirs),
            *(str(path) for path in object_paths),
            *(str(argument) for argument in link_args),
            *self._tool_values(language_info, "dependencies", selected_tools),
            "-o",
            str(extension_path),
            *self._library_flags(self._libraries(language_info, selected_tools, selected_libraries)),
        ]
        self._run_or_record(command, verbose)
        return extension_path

    @staticmethod
    def run_command(command: Iterable[str], verbose: bool | int = False) -> tuple[str, ...]:
        """Run one argv command and raise a concise error when it fails."""

        expanded = tuple(os.path.expandvars(str(part)) for part in command)
        if verbose:
            print(shlex.join(expanded))
        completed = subprocess.run(expanded, capture_output=True, text=True, check=False)
        if verbose and completed.stdout:
            print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
        if completed.returncode:
            raise RuntimeError(f"Native compiler command failed:\n{completed.stderr}")
        if completed.stderr:
            warnings.warn(completed.stderr, stacklevel=2)
        return expanded

    def _run_or_record(self, command: Iterable[str], verbose: bool | int) -> tuple[str, ...]:
        expanded = tuple(os.path.expandvars(str(part)) for part in command)
        self._command_log.append(expanded)
        if self._execute_commands:
            return self.run_command(expanded, verbose)
        return expanded

    def _load_toolchain(self, vendor: str) -> Mapping[str, Mapping[str, object]]:
        configured_path = Path(vendor)
        if configured_path.suffix == ".json" and configured_path.is_file():
            return self._read_toolchain(configured_path)
        if vendor in vendors:
            return available_compilers[vendor]
        installed_path = Path(os.environ.get("X2PY_CONFIG_HOME", Path.home() / ".x2py")) / vendor / "config.json"
        if installed_path.is_file():
            return self._read_toolchain(installed_path)
        raise ValueError(f"Unknown compiler toolchain: {vendor!r}")

    @staticmethod
    def _read_toolchain(path: Path) -> Mapping[str, Mapping[str, object]]:
        with path.open(encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict):
            raise ValueError(f"Compiler configuration must be a JSON object: {path}")
        return payload

    def _language(self, language: str) -> Mapping[str, object]:
        try:
            configuration = self._toolchain[language]
        except KeyError:
            raise ValueError(f"Toolchain does not support {language!r}") from None
        if not isinstance(configuration, Mapping):
            raise ValueError(f"Invalid {language!r} toolchain configuration")
        return configuration

    def _executable(self, language: Mapping[str, object], tools: Iterable[str]) -> str:
        key = "mpi_exec" if "mpi" in tools else "exec"
        language_name = next((name for name, candidate in self._toolchain.items() if candidate is language), None)
        command = self._executables.get(language_name, str(language[key]))
        executable = shutil.which(command, path=self._search_path)
        if executable is None:
            raise FileNotFoundError(f"Could not find compiler executable: {command}")
        return executable

    def _flags(
        self,
        language: Mapping[str, object],
        tools: Iterable[str],
        requested: Iterable[str],
        *,
        executable: str | None = None,
    ) -> tuple[str, ...]:
        profile = "debug_flags" if self._debug else "release_flags"
        values = [*self._strings(language.get(profile, ())), *self._strings(language.get("general_flags", ()))]
        values.extend(self._supported_optional_flags(executable, language.get("optional_general_flags", ())))
        for tool in sorted(set(tools)):
            if tool != "python":
                values.extend(self._strings(self._tool_mapping(language, tool).get("flags", ())))
        values.extend(str(flag) for flag in requested)
        return tuple(values)

    def _supported_optional_flags(self, executable: str | None, flags: object) -> tuple[str, ...]:
        """Return profile flags accepted by the selected compiler executable."""
        if executable is None:
            return ()
        return tuple(flag for flag in self._strings(flags) if self._supports_optional_flag(executable, flag))

    @staticmethod
    @cache
    def _supports_optional_flag(executable: str, flag: str) -> bool:
        """Probe help text instead of making newer profile flags mandatory."""
        help_key = flag.split("=", maxsplit=1)[0] + "=" if "=" in flag else flag
        try:
            completed = subprocess.run(
                (executable, "-Q", "--help=common"),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return False
        return completed.returncode == 0 and help_key in f"{completed.stdout}\n{completed.stderr}"

    def _include_dirs(
        self,
        language: Mapping[str, object],
        tools: Iterable[str],
        requested: Iterable[str | Path],
    ) -> tuple[Path, ...]:
        return self._ordered_paths(
            (*requested, *self._strings(language.get("include", ())), *self._tool_values(language, "include", tools))
        )

    def _library_dirs(
        self,
        language: Mapping[str, object],
        tools: Iterable[str],
        requested: Iterable[str | Path],
    ) -> tuple[Path, ...]:
        return self._ordered_paths(
            (*requested, *self._strings(language.get("libdir", ())), *self._tool_values(language, "libdir", tools))
        )

    def _libraries(
        self,
        language: Mapping[str, object],
        tools: Iterable[str],
        requested: Iterable[str],
    ) -> tuple[str, ...]:
        return self._ordered_strings(
            (*requested, *self._strings(language.get("libs", ())), *self._tool_values(language, "libs", tools))
        )

    def _tool_values(self, language: Mapping[str, object], key: str, tools: Iterable[str]) -> tuple[str, ...]:
        return tuple(
            value
            for tool in sorted(set(tools))
            for value in self._strings(self._tool_mapping(language, tool).get(key, ()))
        )

    @staticmethod
    def _tool_mapping(language: Mapping[str, object], tool: str) -> Mapping[str, object]:
        value = language.get(tool, {})
        return value if isinstance(value, Mapping) else {}

    @staticmethod
    def _strings(values: object) -> tuple[str, ...]:
        if isinstance(values, str):
            return (values,)
        return tuple(str(value) for value in values)

    @staticmethod
    def _ordered_paths(paths: Iterable[str | Path]) -> tuple[Path, ...]:
        return tuple(dict.fromkeys(Path(path) for path in paths))

    @staticmethod
    def _ordered_strings(values: Iterable[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(str(value) for value in values))

    @staticmethod
    def _path_flags(flag: str, paths: Iterable[Path]) -> tuple[str, ...]:
        return tuple(part for path in paths for part in (flag, str(path)))

    @staticmethod
    def _library_flags(libraries: Iterable[str]) -> tuple[str, ...]:
        return tuple(library if library.startswith("-l") else f"-l{library}" for library in libraries)
