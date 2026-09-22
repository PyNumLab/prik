cmake_minimum_required(VERSION 3.18)
project(prik_prima_native LANGUAGES Fortran)

file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/sources.txt" PRIMA_SOURCE_NAMES)
set(PRIMA_SOURCES)
foreach(source IN LISTS PRIMA_SOURCE_NAMES)
  list(APPEND PRIMA_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/native/${source}")
endforeach()

add_library(primaf STATIC ${PRIMA_SOURCES})
set_target_properties(primaf PROPERTIES
  POSITION_INDEPENDENT_CODE ON
  Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/mod"
)
target_compile_definitions(primaf PUBLIC
  PRIMA_REAL_PRECISION=64
  PRIMA_INTEGER_KIND=0
)
target_include_directories(primaf PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/common")
