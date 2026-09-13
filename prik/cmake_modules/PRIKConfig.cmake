#[=======================================================================[.rst:

PRIKConfig
----------

Provide PRIK's packaged CMake helper through ``find_package(PRIK CONFIG)``.

This loads ``UsePRIK.cmake`` from the same directory, so a project that finds
the package gets exactly what ``include(UsePRIK)`` provides, including
``prik_add_module()``.

]=======================================================================]

include("${CMAKE_CURRENT_LIST_DIR}/UsePRIK.cmake")
