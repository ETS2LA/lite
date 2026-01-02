#pragma once

#include <opencv2/opencv.hpp>
#include <windows.h>
#include <string>
#include <vector>

#include "telemetry.h"
#include "capture.h"


namespace utils {


/**
 * 3D coordinate structure.
 * @param x X coordinate.
 * @param y Y coordinate.
 * @param z Z coordinate.
 */
struct Coordinate {
    double x;
    double y;
    double z;
};

/**
 * Rotation structure.
 * @param pitch Pitch angle in degrees.
 * @param yaw Yaw angle in degrees.
 * @param roll Roll angle in degrees.
 */
struct Rotation {
    float pitch;
    float yaw;
    float roll;
};

/**
 * Screen coordinate structure.
 * @param x X coordinate on the screen.
 * @param y Y coordinate on the screen.
 * @param distance The distance from the camera to the point.
 */
struct ScreenCoordinate {
    double x;
    double y;
    double distance;
};

/**
 * Camera coordinate structure.
 * @param x X coordinate of the camera.
 * @param y Y coordinate of the camera.
 * @param z Z coordinate of the camera.
 * @param pitch Pitch angle of the camera in degrees.
 * @param yaw Yaw angle of the camera in degrees.
 * @param roll Roll angle of the camera in degrees.
 */
struct CameraCoordinate {
    double x;
    double y;
    double z;
    float pitch;
    float yaw;
    float roll;
};


HWND find_window(
    const std::wstring& window_name,
    const std::vector<std::wstring>& blacklist
);
std::vector<int> get_window_position(HWND hwnd);

void apply_route_advisor_crop(cv::Mat& frame, const bool side_right = true);

double get_time_seconds();

void set_icon(HWND hwnd, const std::wstring& icon_path);
void set_window_title_bar_color(HWND hwnd, COLORREF color);
void set_window_outline_color(HWND hwnd, COLORREF color);

float degrees_to_radians(float degrees);

ScreenCoordinate convert_to_screen_coordinate(
    const Coordinate& world_coords,
    const CameraCoordinate& camera_coords,
    const int window_width,
    const int window_height
);

Coordinate rotate_vector(
    const Coordinate& vector,
    const Rotation& rotation
);

CameraCoordinate get_6th_camera_coordinate(TelemetryData* telemetry_data);

}