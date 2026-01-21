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
 * Angle structure.
 * @param azimuth Azimuth angle in degrees.
 * @param elevation Elevation angle in degrees.
 */
struct Angle {
    float azimuth;
    float elevation;
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

/**
 * Float RGBA color structure.
 * @param r Red (0.0 - 1.0)
 * @param g Green (0.0 - 1.0)
 * @param b Blue (0.0 - 1.0)
 * @param a Alpha (0.0 - 1.0)
 */
struct ColorFloat {
    float r;
    float g;
    float b;
    float a;
};

/**
 * Integer RGBA color structure.
 * @param r Red (0 - 255)
 * @param g Green (0 - 255)
 * @param b Blue (0 - 255)
 * @param a Alpha (0 - 255)
 */
struct ColorInt {
    int r;
    int g;
    int b;
    int a;
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
float radians_to_degrees(float radians);
double degrees_to_radians(double degrees);
double radians_to_degrees(double radians);

ScreenCoordinate convert_to_screen_coordinate(
    const Coordinate& world_coords,
    const CameraCoordinate& camera_coords,
    const int window_width,
    const int window_height
);

Angle convert_to_angle(
    const ScreenCoordinate screen_coord,
    const int window_width,
    const int window_height
);

Coordinate rotate_vector(
    const Coordinate& vector,
    const Rotation& rotation
);

CameraCoordinate get_6th_camera_coordinate(TelemetryData* telemetry_data);

}