# ETS2LA-Lite C++

### Build

- Get [LibTorch](https://pytorch.org/)
  - Unzip it
  - Create an environment variable named `LIBTORCH` and set its value to the path of the LibTorch folder, which contains folders like `lib`, `bin`, `include`, etc.
- Get [CMake](https://cmake.org/)
  - Install it (select the option to add it to the system PATH)
  - Open a terminal and cd into the `cpp-app` folder
  - Run ```cmake --preset=x64-release -B build/x64-release && cmake --build build/x64-release``` to build the app
  - Run ```.\build\x64-release\Debug\cpp-app.exe``` to run the app