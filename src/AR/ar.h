#pragma once

#include "telemetry.h"
#include "camera.h"

#include <GLFW/glfw3.h>
#include <functional>
#include <windows.h>
#include <thread>


class AR {
public:
    // MARK: public
    AR(const std::function<HWND()> target_window_handle_function, const int msaa_samples = 8);
    ~AR();
    void draw_wheel_trajectory(const utils::ColorFloat& color);
    void run();

    // MARK: line
    void line(
        const float x1,
        const float y1,
        const float x2,
        const float y2,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::ScreenCoordinate& start,
        const utils::ScreenCoordinate& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::Coordinate& start,
        const utils::Coordinate& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::Coordinate& start,
        const utils::Coordinate& end,
        const utils::CameraCoordinate& camera_coords,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: circle
    void circle(
        const float x,
        const float y,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::ScreenCoordinate& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::Coordinate& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::Coordinate& center,
        const utils::CameraCoordinate& camera_coords,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: rectangle
    void rectangle(
        const float x1,
        const float y1,
        const float x2,
        const float y2,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::ScreenCoordinate& top_left,
        const utils::ScreenCoordinate& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::Coordinate& top_left,
        const utils::Coordinate& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::Coordinate& top_left,
        const utils::Coordinate& bottom_right,
        const utils::CameraCoordinate& camera_coords,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: polyline
    void polyline(
        const std::vector<std::pair<float, float>>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::ScreenCoordinate>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::Coordinate>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::Coordinate>& points,
        const utils::CameraCoordinate& camera_coords,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );

private:
    // MARK: private
    void window_state_update_thread();

    GLFWwindow* window_;
    std::function<HWND()> target_window_handle_function_;
    std::thread position_thread_;

    SCSTelemetry telemetry_;
    TelemetryData* telemetry_data_;

    int window_width_;
    int window_height_;
};