cmake_minimum_required(VERSION 3.21)

project(prik_cmake_example LANGUAGES C Fortran)

find_package(
    Python
    COMPONENTS Interpreter Development.Module
    REQUIRED
)

set(PRIK_DISCOVERY "include" CACHE STRING "How this project loads PRIK's CMake modules")
set_property(CACHE PRIK_DISCOVERY PROPERTY STRINGS include find-package)

if(PRIK_DISCOVERY STREQUAL "find-package")
    # Needs PRIK's CMake package on a search path: PRIK_DIR set to
    # `prik cmake-dir`, or CMAKE_PREFIX_PATH set to `prik install-dir`.
    find_package(PRIK CONFIG REQUIRED)
else()
    # scikit-build-core adds PRIK's packaged module directory to
    # CMAKE_MODULE_PATH through its cmake.module entry point, so this include
    # needs no lookup. A plain configure gets there by setting
    # CMAKE_MODULE_PATH to `prik cmake-dir`.
    include(UsePRIK)
endif()

prik_add_module(
    heat
    FORTRAN_SOURCES
        kernel.f90
)

install(TARGETS heat DESTINATION .)
