# ETS2LA-Lite

### Build

- Get [OpenCV](https://opencv.org/releases)
  - Install it
  - Create an environment variable named `OpenCV_DIR` and set its value to the path of the OpenCV folder, which contains folders like `bin`, `x64`, `include`, etc.
  - Add the absolute path of the `/x64/*/bin` folder (where `*` is for example `vc14`, `vc15`, `vc16`, etc.) in the `OpenCV_DIR` to the system PATH
- Get [GLFW](https://github.com/glfw/glfw) (source, not precompiled)
  - Extract it
  - Create an environment variable named `glfw3_DIR` and set its value to the path of the GLFW folder, which contains folders like `CMake`, `docs`, `include`, etc.
- Get [CMake](https://cmake.org/)
  - Install it (select the option to add it to the system PATH)
- Build the app in release mode
  - Open a terminal and cd into the `ETS2LA-Lite` folder
  - Run ```cmake --preset=x64-release -B build/x64-release && cmake --build build/x64-release --config Release``` to build the app in release mode
  - Run ```.\build\x64-release\Release\ETS2LA-Lite.exe``` to run the release build
- Build the app in debug mode
  - Run ```cmake --preset=x64-debug -B build/x64-debug && cmake --build build/x64-debug``` to build the app in debug mode
  - Run ```.\build\x64-debug\Debug\ETS2LA-Lite.exe``` to run the debug build