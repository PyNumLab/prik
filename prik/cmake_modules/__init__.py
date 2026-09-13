"""Packaged CMake modules for PRIK's CMake integration.

The directory holding this package is what ``include(UsePRIK)`` and
``find_package(PRIK CONFIG)`` need on ``CMAKE_MODULE_PATH`` or ``PRIK_DIR``.
Keeping the modules in an importable package lets a build backend discover them
through the ``cmake.module`` entry point without running PRIK.
"""
