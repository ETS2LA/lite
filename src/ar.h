#pragma once

#include <GLFW/glfw3.h>
#include <functional>
#include <windows.h>
#include <thread>


class AR {
public:
    AR(std::function<HWND()> target_window_handle_function);
    ~AR();
    void run();

private:
    GLFWwindow* window_;
    std::function<HWND()> target_window_handle_function_;
    std::thread position_thread_;
};