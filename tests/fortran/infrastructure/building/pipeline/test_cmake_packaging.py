"""Installed-distribution contracts for PRIK's packaged CMake modules.

A CMake project finds the helper in an installation, either through PRIK's own
``cmake_module_dir()``, through ``find_package(PRIK CONFIG)``, or through the
``cmake.module`` entry point a build backend reads. All three need the packaged
modules to survive packaging, which only an installed wheel can show.
"""

from pathlib import Path

import pytest

from tests.fortran._support.installed_distribution import installed_output, installed_prik_python, installed_run
from tests.fortran._support.paths import REPO_ROOT


@pytest.mark.slow
def test_installed_distribution_exposes_its_cmake_modules_through_every_discovery_route() -> None:
    """The packaged directory, the data share, and both build-backend entry points name the modules.

    scikit-build-core reads ``cmake.module`` and sets ``<entry-point name>_ROOT``
    from ``cmake.root``, so ``find_package(PRIK CONFIG REQUIRED)`` resolves with
    no argument only because that root entry point is named ``PRIK``.
    """
    module_dir, data_dir, module_entry_dir, root_name, root_dir = (
        installed_output(
            "import os, sysconfig\n"
            "from importlib import metadata, resources\n"
            "from prik.cmake import cmake_module_dir\n"
            "entries = metadata.distribution('prik').entry_points\n"
            "modules = [entry for entry in entries if entry.group == 'cmake.module']\n"
            "roots = [entry for entry in entries if entry.group == 'cmake.root']\n"
            "assert len(modules) == 1, modules\n"
            "assert len(roots) == 1, roots\n"
            "print(cmake_module_dir())\n"
            "print(sysconfig.get_path('data'))\n"
            "print(os.path.realpath(str(resources.files(modules[0].load()))))\n"
            "print(roots[0].name)\n"
            "print(os.path.realpath(str(resources.files(roots[0].load()))))\n"
        )
        .strip()
        .splitlines()
    )
    module_dir, data_dir, module_entry_dir = Path(module_dir), Path(data_dir), Path(module_entry_dir)

    assert REPO_ROOT not in module_dir.parents
    for directory in (module_dir, data_dir / "share" / "prik" / "cmake"):
        assert (directory / "UsePRIK.cmake").is_file(), directory
        assert (directory / "PRIKConfig.cmake").is_file(), directory
    assert module_entry_dir == module_dir.resolve()
    assert root_name == "PRIK"
    assert (Path(root_dir) / "PRIKConfig.cmake").is_file()


@pytest.mark.slow
def test_installed_console_script_prints_the_paths_a_build_configures_with() -> None:
    """``prik cmake-dir`` and ``prik install-dir`` answer for the installation they run from."""
    script = installed_prik_python().parent / "prik"
    module_dir = Path(installed_run(str(script), "cmake-dir").strip())
    prefix = Path(installed_run(str(script), "install-dir").strip())

    assert (module_dir / "PRIKConfig.cmake").is_file()
    # macOS puts a temporary environment behind a /var -> /private/var symlink,
    # so the environment root and the reported prefix are compared resolved.
    assert prefix.resolve() == installed_prik_python().parent.parent.resolve()
    assert (prefix / "share" / "prik" / "cmake" / "PRIKConfig.cmake").is_file()
