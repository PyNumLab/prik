cmake_minimum_required(VERSION 3.21)

project(prik_cmake_example LANGUAGES C Fortran)

find_package(
    Python
    COMPONENTS Interpreter Development.Module
    REQUIRED
)

set(PRIK_DISCOVERY "find-package" CACHE STRING "How this project loads PRIK's CMake modules")
set_property(CACHE PRIK_DISCOVERY PROPERTY STRINGS find-package include)

if(PRIK_DISCOVERY STREQUAL "include")
    # The module-path route. A plain configure needs CMAKE_MODULE_PATH set to
    # `prik cmake-dir`; scikit-build-core supplies it from PRIK's cmake.module
    # entry point.
    include(UsePRIK)
else()
    # The default. scikit-build-core sets PRIK_ROOT from PRIK's cmake.root
    # entry point, so this needs no argument there at all; a plain configure
    # passes PRIK_DIR or CMAKE_PREFIX_PATH instead.
    find_package(PRIK CONFIG REQUIRED)
endif()

prik_add_module(
    heat
    FORTRAN_SOURCES
        kernel.f90
)

install(TARGETS heat DESTINATION .)
