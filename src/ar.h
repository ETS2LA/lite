#pragma once

#include "telemetry.h"
#include "camera.h"

#include <GLFW/glfw3.h>
#include <functional>
#include <windows.h>
#include <thread>


class AR {
public:
    AR(const std::function<HWND()> target_window_handle_function);
    ~AR();
    void run();

private:
    void window_state_update_thread();
    void draw_wheel_trajectory();

    GLFWwindow* window_;
    std::function<HWND()> target_window_handle_function_;
    std::thread position_thread_;

    SCSTelemetry telemetry_;
    TelemetryData* telemetry_data_;

    int window_width_;
    int window_height_;
};