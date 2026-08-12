"""Install bundled native binding support for generated CPython wrappers."""

from pathlib import Path
import shutil

from filelock import FileLock
import numpy as np

import prik.runtime.native_support as native_support_folder

_NATIVE_SUPPORT_IMPORT = "binding_support"
_NATIVE_SUPPORT_SOURCE = Path(native_support_folder.__file__).parent


def _numpy_version_header() -> str:
    """Return NumPy API version guards for the bundled native support."""
    maximum_supported = [1, 19]
    current = [int(value) for value in np.version.version.split(".")[:2]]
    major, minor = min(maximum_supported, current)
    header = f"#ifndef NPY_NO_DEPRECATED_API\n# define NPY_NO_DEPRECATED_API NPY_{major}_{minor}_API_VERSION\n#endif\n"
    if current[0] >= 2:
        header += "#ifndef NPY_TARGET_VERSION\n# define NPY_TARGET_VERSION NPY_2_0_API_VERSION\n#endif\n"
    return header


def install_native_support(imports, *, prik_dirpath, verbose: bool | int = False) -> None:
    """Write header-only native binding support when a generated binding imports it."""
    if not any(name == _NATIVE_SUPPORT_IMPORT or name.startswith(f"{_NATIVE_SUPPORT_IMPORT}/") for name in imports):
        return

    destination = Path(prik_dirpath) / _NATIVE_SUPPORT_IMPORT
    if verbose:
        print(f">> Write native support: {destination}")
    with FileLock(str(destination.with_suffix(".lock"))):
        shutil.rmtree(destination, ignore_errors=True)
        shutil.copytree(_NATIVE_SUPPORT_SOURCE, destination)

    (destination / "numpy_version.h").write_text(
        _numpy_version_header(),
        encoding="utf-8",
    )


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        install_native_support(
            ("binding_support/prik_binding.h",),
            prik_dirpath=directory,
        )
        installed = Path(directory) / "binding_support"

        print(f"Installed directory: {installed.name}")
        print(f"Binding header present: {(installed / 'prik_binding.h').is_file()}")
        print(f"NumPy version header present: {(installed / 'numpy_version.h').is_file()}")
