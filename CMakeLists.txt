cmake_minimum_required(VERSION 3.20)

if(CMAKE_BUILD_TYPE MATCHES Debug)
    add_compile_definitions(BUILD_TYPE_DEBUG)
elseif(CMAKE_BUILD_TYPE MATCHES Release)
    add_compile_definitions(BUILD_TYPE_RELEASE)
endif()

project("ETS2LA-Lite")

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED True)

set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /MT")

find_package(OpenCV REQUIRED)
find_package(OpenGL REQUIRED)
add_subdirectory($ENV{glfw3_DIR} glfw)

file(GLOB_RECURSE SRC_FILES "src/*.cpp" "src/*.h")

add_executable(${PROJECT_NAME} main.cpp ${SRC_FILES})
target_link_libraries(${PROJECT_NAME} PRIVATE
    ${OpenCV_LIBS}
    OpenGL::GL
    glfw
    windowsapp
)
target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND robocopy "${CMAKE_SOURCE_DIR}/assets" "$<TARGET_FILE_DIR:${PROJECT_NAME}>/assets" /MIR /FFT /Z /R:0 /W:0 >nul || (exit 0)
)

if (MSVC)
    file(GLOB OPENCV_DLLS "${OpenCV_DIR}/x64/*/bin/*.dll")
    add_custom_command(
        TARGET ${PROJECT_NAME}
        POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${OPENCV_DLLS}
        $<TARGET_FILE_DIR:${PROJECT_NAME}>
    )
endif (MSVC)