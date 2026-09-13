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
def test_installed_distribution_ships_prik_config_beside_use_prik() -> None:
    module_dir, data_dir = (
        Path(line)
        for line in installed_output(
            "import sysconfig\n"
            "from prik.cmake import cmake_module_dir\n"
            "print(cmake_module_dir())\n"
            "print(sysconfig.get_path('data'))\n"
        ).splitlines()
    )

    assert REPO_ROOT not in module_dir.parents
    for directory in (module_dir, data_dir / "share" / "prik" / "cmake"):
        assert (directory / "UsePRIK.cmake").is_file(), directory
        assert (directory / "PRIKConfig.cmake").is_file(), directory


@pytest.mark.slow
def test_installed_distribution_exposes_the_cmake_module_entry_point() -> None:
    """The entry point resolves the way a scikit-build-core build reads it."""
    entry_point_dir = Path(
        installed_output(
            "import os\n"
            "from importlib import metadata, resources\n"
            "from prik.cmake import cmake_module_dir\n"
            "modules = [\n"
            "    entry\n"
            "    for entry in metadata.distribution('prik').entry_points\n"
            "    if entry.group == 'cmake.module'\n"
            "]\n"
            "assert len(modules) == 1, modules\n"
            "directory = os.path.realpath(str(resources.files(modules[0].load())))\n"
            "assert directory == os.path.realpath(str(cmake_module_dir())), directory\n"
            "print(directory)\n"
        ).strip()
    )

    assert REPO_ROOT not in entry_point_dir.parents
    assert (entry_point_dir / "UsePRIK.cmake").is_file()


@pytest.mark.slow
def test_installed_distribution_exposes_the_cmake_root_entry_point_as_prik() -> None:
    """scikit-build-core sets ``<entry-point name>_ROOT``, so the name is the contract.

    ``find_package(PRIK CONFIG REQUIRED)`` resolves with no argument only
    because that variable comes out as ``PRIK_ROOT``, which makes the entry
    point's name load-bearing rather than decorative.
    """
    name, directory = installed_output(
        "import os\n"
        "from importlib import metadata, resources\n"
        "roots = [\n"
        "    entry\n"
        "    for entry in metadata.distribution('prik').entry_points\n"
        "    if entry.group == 'cmake.root'\n"
        "]\n"
        "assert len(roots) == 1, roots\n"
        "print(roots[0].name)\n"
        "print(os.path.realpath(str(resources.files(roots[0].load()))))\n"
    ).splitlines()

    assert name == "PRIK"
    assert (Path(directory) / "PRIKConfig.cmake").is_file()


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
