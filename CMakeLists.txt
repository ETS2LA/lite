cmake_minimum_required(VERSION 3.25)

if(CMAKE_BUILD_TYPE MATCHES Debug)
    add_compile_definitions(BUILD_TYPE_DEBUG)
elseif(CMAKE_BUILD_TYPE MATCHES Release)
    add_compile_definitions(BUILD_TYPE_RELEASE)
endif()

project("ETS2LA-Lite")

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED True)

set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /MT")

include(FetchContent)
FetchContent_Declare(
    ets2la_capture
    GIT_REPOSITORY https://github.com/ETS2LA/capture.git
    GIT_TAG main
)
cmake_policy(SET CMP0169 OLD)
FetchContent_Populate(ets2la_capture)

find_package(OpenCV REQUIRED)
find_package(OpenGL REQUIRED)
add_subdirectory($ENV{glfw3_DIR} glfw)
add_subdirectory($ENV{freetype_DIR} freetype)

set(ORT_DIR "$ENV{OnnxRuntime_DIR}")
set(ORT_INCLUDE "${ORT_DIR}/build/native/include")
set(ORT_LIB "${ORT_DIR}/runtimes/win-x64/native")
set(ORT_BIN "${ORT_DIR}/runtimes/win-x64/native")

add_library(onnxruntime SHARED IMPORTED)
set_target_properties(onnxruntime PROPERTIES
    IMPORTED_IMPLIB "${ORT_LIB}/onnxruntime.lib"
    IMPORTED_LOCATION "${ORT_BIN}/onnxruntime.dll"
    INTERFACE_INCLUDE_DIRECTORIES "${ORT_INCLUDE}"
)

file(GLOB_RECURSE SRC_FILES "src/*.cpp" "src/*.h")

add_executable(${PROJECT_NAME} main.cpp ${SRC_FILES})
target_link_libraries(${PROJECT_NAME} PRIVATE
    ${OpenCV_LIBS}
    OpenGL::GL
    glfw
    freetype
    windowsapp
    onnxruntime
)
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${ets2la_capture_SOURCE_DIR}/include
)

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_RUNTIME_DLLS:${PROJECT_NAME}>
        $<TARGET_FILE_DIR:${PROJECT_NAME}>
    COMMAND_EXPAND_LISTS

    COMMAND robocopy "${CMAKE_SOURCE_DIR}/assets" "$<TARGET_FILE_DIR:${PROJECT_NAME}>/assets" /MIR /FFT /Z /R:0 /W:0 >nul || (exit 0)
)