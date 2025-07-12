cmake_minimum_required(VERSION 3.10)
project(ETS2LALite)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

set(SCS_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/scs_sdk" CACHE PATH "Path to SCS SDK")

if(NOT EXISTS ${SCS_SDK_PATH})
    message(FATAL_ERROR "SCS SDK not found at ${SCS_SDK_PATH}. Please download the official SDK from SCS Software and extract it.")
endif()

include_directories(
    ${SCS_SDK_PATH}/include
    ${CMAKE_CURRENT_SOURCE_DIR}
)

add_library(ets2la_lite SHARED
    src/ets2la_lite.def
    src/main.cpp
    src/log.cpp
)

set_target_properties(ets2la_lite PROPERTIES
    PREFIX ""
    SUFFIX ".dll"
    OUTPUT_NAME "ets2la_lite"
)

if(WIN32)
    target_link_libraries(ets2la_lite
        PRIVATE
        kernel32
        user32
    )
endif()

if(MSVC)
    target_compile_options(ets2la_lite PRIVATE
        /W4
        /WX-
    )
elseif(CMAKE_COMPILER_IS_GNUCXX)
    target_compile_options(ets2la_lite PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
endif()

message(STATUS "Building ETS2LA Lite")
message(STATUS "SCS SDK Path: ${SCS_SDK_PATH}")
message(STATUS "Output Directory: ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")