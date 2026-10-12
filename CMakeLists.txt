cmake_minimum_required(VERSION 3.22)
project(Q2 LANGUAGES C)
enable_testing()
set(Q2_TARGET "x86" CACHE STRING "Product target: x86, host, kernel")
set(Q2_DEFAULT_CONFIG "q2.json")
if(Q2_TARGET STREQUAL "x86" AND CMAKE_SYSTEM_NAME STREQUAL "Linux")
  set(Q2_DEFAULT_CONFIG "q2.linux.json")
endif()
set(Q2_CONFIG_FILE "${CMAKE_CURRENT_SOURCE_DIR}/${Q2_DEFAULT_CONFIG}" CACHE FILEPATH "Product configuration")
find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${Q2_CONFIG_FILE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/project_config.py")
set(Q2_GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
execute_process(COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/project_config.py"
  --config "${Q2_CONFIG_FILE}" --output "${Q2_GENERATED_DIR}" --target "${Q2_TARGET}"
  RESULT_VARIABLE config_result)
if(NOT config_result EQUAL 0)
  message(FATAL_ERROR "Invalid Q2 product configuration")
endif()
include("${Q2_GENERATED_DIR}/project.cmake")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/bin")
if(Q2_TARGET STREQUAL "kernel")
  add_subdirectory("${Q2_KERNEL_DIR}" kernel)
elseif(Q2_TARGET STREQUAL "x86" OR Q2_TARGET STREQUAL "host")
  add_subdirectory("${Q2_PLATFORM_DIR}/${Q2_TARGET}" platform)
else()
  message(FATAL_ERROR
    "Use q2.py build --target esp32, esp32s3 or esp32s31 for the separate ESP-IDF build system")
endif()
add_test(NAME q2_product_config COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_SOURCE_DIR}/scripts/test_project_config.py")

add_test(NAME q2_esp_build_cache COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_SOURCE_DIR}/scripts/test_esp_build_cache.py")
add_test(NAME q2_linux_entry COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_SOURCE_DIR}/scripts/test_linux_entry.py")

add_test(NAME q2_python_entry COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_SOURCE_DIR}/scripts/test_python_entry.py")
