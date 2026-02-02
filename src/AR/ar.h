#pragma once

#include "telemetry.h"
#include "camera.h"

#include <GLFW/glfw3.h>
#include <functional>
#include <string>
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
        const utils::ScreenCoordinates& start,
        const utils::ScreenCoordinates& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::Coordinates& start,
        const utils::Coordinates& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::Coordinates& start,
        const utils::Coordinates& end,
        const utils::CameraCoordinates& camera_coords,
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
        const utils::ScreenCoordinates& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::Coordinates& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::Coordinates& center,
        const utils::CameraCoordinates& camera_coords,
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
        const utils::ScreenCoordinates& top_left,
        const utils::ScreenCoordinates& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::Coordinates& top_left,
        const utils::Coordinates& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::Coordinates& top_left,
        const utils::Coordinates& bottom_right,
        const utils::CameraCoordinates& camera_coords,
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
        const std::vector<utils::ScreenCoordinates>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::Coordinates>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::Coordinates>& points,
        const utils::CameraCoordinates& camera_coords,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: text
    void text(
        const std::string& text,
        const float x,
        const float y,
        const float size,
        const utils::ColorFloat& color
    );
    void text(
        const std::string& text,
        const utils::ScreenCoordinates& origin,
        const float size,
        const utils::ColorFloat& color
    );
    void text(
        const std::string& text,
        const utils::Coordinates& origin,
        const float size,
        const utils::ColorFloat& color
    );
    void text(
        const std::string& text,
        const utils::Coordinates& origin,
        const utils::CameraCoordinates& camera_coords,
        const float size,
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