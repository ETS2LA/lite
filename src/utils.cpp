#include "utils.h"
#include <numbers>

using namespace std;


namespace utils {


/**
 * PID controller class.
 * @param kp Proportional gain
 * @param ki Integral gain
 * @param kd Derivative gain
 */
PIDController::PIDController(float kp, float ki, float kd):
kp_(kp),
ki_(ki),
kd_(kd),
integral_(0.0f),
integral_limit_(1.0f),
previous_error_(0.0f) {}

/**
 * Set the PID gains.
 * @param kp Proportional gain
 * @param ki Integral gain
 * @param kd Derivative gain
 */
void PIDController::set_gains(float kp, float ki, float kd) {
    kp_ = kp;
    ki_ = ki;
    kd_ = kd;
}

/**
 * Get the PID gains.
 * @param kp Proportional gain
 * @param ki Integral gain
 * @param kd Derivative gain
 */
void PIDController::get_gains(float& kp, float& ki, float& kd) {
    kp = kp_;
    ki = ki_;
    kd = kd_;
}

/**
 * Set the integral limit to prevent windup.
 * @param limit The maximum absolute value for the integral term.
 */
void PIDController::set_integral_limit(float limit) {
    integral_limit_ = abs(limit);
}

/**
 * Get the integral limit.
 * @param limit The maximum absolute value for the integral term.
 */
void PIDController::get_integral_limit(float& limit) {
    limit = integral_limit_;
}

/**
 * Update the PID controller with the target and current values, and get the control output.
 * @param target The desired target value.
 * @param current_value The current value to compare against the target.
 * @return The control output calculated by the PID controller.
 */
float PIDController::update(float target, float current_value) {
    auto current_time = chrono::high_resolution_clock::now();
    float dt = chrono::duration<float>(current_time - last_update_time_).count();
    if (dt <= 0.0f) {
        return previous_output_;
    }
    last_update_time_ = current_time;

    float error = target - current_value;
    if (!initialized_) {
        previous_error_ = error;
        initialized_ = true;
    }

    integral_ += error * dt;
    float derivative = (error - previous_error_) / dt;
    float output = kp_ * error + ki_ * integral_ + kd_ * derivative;

    integral_ = clamp(integral_, -integral_limit_, integral_limit_);
    previous_error_ = error;
    previous_output_ = output;
    return output;
}

/**
 * Reset the PID controller.
 */
void PIDController::reset() {
    initialized_ = false;
    integral_ = 0.0f;
    previous_error_ = 0.0f;
    previous_output_ = 0.0f;
    last_update_time_ = chrono::steady_clock::now();
}


/**
 * Timer class.
 */
Timer::Timer() : last_fps_update_(0.0) {}

/**
 * Start the timer.
 */
void Timer::start() {
    start_time_ = chrono::high_resolution_clock::now();
}

/**
 * Get the elapsed time in seconds since the timer was started.
 * @return Elapsed time in seconds.
 */
double Timer::get_seconds() {
    auto now = chrono::high_resolution_clock::now();
    return chrono::duration<double>(now - start_time_).count();
}

/**
 * Get the elapsed time in milliseconds since the timer was started.
 * @return Elapsed time in milliseconds.
 */
double Timer::get_milliseconds() {
    auto now = chrono::high_resolution_clock::now();
    return chrono::duration<double, milli>(now - start_time_).count();
}

/**
 * Get the elapsed time in microseconds since the timer was started.
 * @return Elapsed time in microseconds.
 */
double Timer::get_microseconds() {
    auto now = chrono::high_resolution_clock::now();
    return chrono::duration<double, micro>(now - start_time_).count();
}

/**
 * Get the frames per second based on the time since the last get_fps() call.
 * @return The calculated FPS.
 */
double Timer::get_fps() {
    double current_time = get_seconds();
    double fps = 1.0 / (current_time - last_fps_update_);
    last_fps_update_ = current_time;
    return fps;
}


/**
 * Finds a window whose title contains window_name but does not include any blacklist terms.
 * @param window_name The name (or part of the name) of the window to find.
 * @param blacklist A list of terms that should not be present in the window title.
 * @return The handle to the found window, or nullptr if no suitable window was found.
 */
HWND find_window(const wstring& window_name, const vector<wstring>& blacklist) {
    HWND found_handle = nullptr;

    struct Params {
        const wstring* target_name;
        const vector<wstring>* blacklist;
        HWND* output;
    } params{ &window_name, &blacklist, &found_handle };

    EnumWindows(
        [](HWND hwnd, LPARAM lParam) -> BOOL {
            auto params = reinterpret_cast<Params*>(lParam);
            const wstring& target_name = *params->target_name;
            const vector<wstring>& blacklist = *params->blacklist;

            const int length = GetWindowTextLengthW(hwnd);
            if (length == 0) return TRUE;

            wstring window_title(length + 1, L'\0');
            GetWindowTextW(hwnd, &window_title[0], length + 1);
            window_title.resize(length);

            if (window_title.find(target_name) != wstring::npos) {
                for (const auto& term : blacklist) {
                    // if any blacklist term is found, skip this window
                    if (window_title.find(term) != wstring::npos) return TRUE;
                }
                // valid window found, stop enumeration
                *params->output = hwnd;
                return FALSE;
            }

            return TRUE;
        },
        reinterpret_cast<LPARAM>(&params)
    );

    return found_handle;
}


/**
 * Get the position of a window.
 * @param hwnd The handle to the window.
 * @return A vector containing the x1, y1, x2, and y2 coordinates of the window.
 */
vector<int> get_window_position(HWND hwnd) {
    vector<int> position(4);

    if (hwnd == nullptr) {
        return position;
    }

    RECT client_rect;
    if (!GetClientRect(hwnd, &client_rect)) {
        return position;
    }

    POINT top_left{client_rect.left, client_rect.top};
    POINT bottom_right{client_rect.right, client_rect.bottom};
    if (!ClientToScreen(hwnd, &top_left) || !ClientToScreen(hwnd, &bottom_right)) {
        return position;
    }

    position[0] = top_left.x;
    position[1] = top_left.y;
    position[2] = bottom_right.x;
    position[3] = bottom_right.y;

    return position;
}


/**
 * Applies a crop to the given frame to focus on the route advisor area.
 * @param frame The frame to apply the crop to.
 */
void apply_route_advisor_crop(cv::Mat& frame, const bool side_right) {
    float frame_width = static_cast<float>(frame.cols);
    float frame_height = static_cast<float>(frame.rows);
    int map_x1, map_y1, map_x2, map_y2;

    int distance_right = 24;
    int distance_bottom = 51;
    int width = 324;
    int height = 228;
    float scale = frame_height / 1080.0f;

    if (side_right == false) {
        map_x1 = static_cast<int>(round(distance_right * scale - 1.0f));
        map_y1 = static_cast<int>(round(frame_height - (distance_bottom * scale + height * scale)));
        map_x2 = static_cast<int>(round(distance_right * scale + width * scale - 1.0f));
        map_y2 = static_cast<int>(round(frame_height - (distance_bottom * scale)));
    } else {
        map_x1 = static_cast<int>(round(frame_width - (distance_right * scale + width * scale)));
        map_y1 = static_cast<int>(round(frame_height - (distance_bottom * scale + height * scale)));
        map_x2 = static_cast<int>(round(frame_width - (distance_right * scale)));
        map_y2 = static_cast<int>(round(frame_height - (distance_bottom * scale)));
    }

    if (map_x1 > map_x2) {
        map_x2 = map_x1 + 1;
    }

    if (map_y1 > map_y2) {
        map_y2 = map_y1 + 1;
    }

    map_x1 = max(0, min(map_x1, frame.cols));
    map_y1 = max(0, min(map_y1, frame.rows));
    map_x2 = max(0, min(map_x2, frame.cols));
    map_y2 = max(0, min(map_y2, frame.rows));

    if (map_x1 == map_x2) {
        return;
    }

    if (map_y1 == map_y2) {
        return;
    }

    frame = frame(cv::Rect(map_x1, map_y1, map_x2 - map_x1, map_y2 - map_y1)).clone();
}


/**
 * Get the current time in seconds with nanosecond precision.
 * @return The current time in seconds.
 */
double get_time_seconds() {
    auto now = chrono::high_resolution_clock::now();
    auto now_ns = chrono::time_point_cast<chrono::nanoseconds>(now);
    return static_cast<double>(now_ns.time_since_epoch().count()) / 1e9;
}


/**
 * Set the icon of a window.
 * @param hwnd The handle to the window.
 * @param icon_path The path to the .ico file.
 */
void set_icon(HWND hwnd, const wstring& icon_path) {
    HICON h_icon = static_cast<HICON>(LoadImageW(
        nullptr,
        icon_path.c_str(),
        IMAGE_ICON,
        32,
        32,
        LR_LOADFROMFILE | LR_DEFAULTSIZE | LR_SHARED
    ));

    if (h_icon) {
        SendMessageW(hwnd, WM_SETICON, ICON_BIG, reinterpret_cast<LPARAM>(h_icon));
        SendMessageW(hwnd, WM_SETICON, ICON_SMALL, reinterpret_cast<LPARAM>(h_icon));
    }
}


/**
 * Set the title bar color of a window.
 * @param hwnd The handle to the window.
 * @param color The color to set the title bar to.
 */
void set_window_title_bar_color(HWND hwnd, COLORREF color) {
    if (!hwnd) return;

    HMODULE h_dwm = LoadLibraryW(L"dwmapi.dll");
    if (!h_dwm) return;

    using DwmSetWindowAttributeFn = HRESULT(WINAPI*)(HWND, DWORD, LPCVOID, DWORD);
    auto pDwmSetWindowAttribute = reinterpret_cast<DwmSetWindowAttributeFn>(GetProcAddress(h_dwm, "DwmSetWindowAttribute"));
    if (!pDwmSetWindowAttribute) {
        return;
    }

    constexpr DWORD DWMWA_CAPTION_COLOR = 35;
    pDwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, &color, sizeof(color));
}


/**
 * Set the outline color of a window.
 * @param hwnd The handle to the window.
 * @param color The color to set the outline to.
 */
void set_window_outline_color(HWND hwnd, COLORREF color) {
    if (!hwnd) return;

    HMODULE h_dwm = LoadLibraryW(L"dwmapi.dll");
    if (!h_dwm) return;

    using DwmSetWindowAttributeFn = HRESULT(WINAPI*)(HWND, DWORD, LPCVOID, DWORD);
    auto pDwmSetWindowAttribute = reinterpret_cast<DwmSetWindowAttributeFn>(GetProcAddress(h_dwm, "DwmSetWindowAttribute"));
    if (!pDwmSetWindowAttribute) {
        return;
    }

    constexpr DWORD DWMWA_BORDER_COLOR = 34;
    pDwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR, &color, sizeof(color));
}


/**
 * Convert degrees to radians.
 * @param degrees The angle in degrees.
 */
float degrees_to_radians(float degrees) {
    return degrees * static_cast<float>(numbers::pi) / 180.0f;
}


/**
 * Convert radians to degrees.
 * @param radians The angle in radians.
 */
float radians_to_degrees(float radians) {
    return radians * 180.0f / static_cast<float>(numbers::pi);
}


/**
 * Convert degrees to radians.
 * @param degrees The angle in degrees.
 */
double degrees_to_radians(double degrees) {
    return degrees * numbers::pi / 180.0;
}


/**
 * Convert radians to degrees.
 * @param radians The angle in radians.
 */
double radians_to_degrees(double radians) {
    return radians * 180.0 / numbers::pi;
}


/**
 * Convert world coordinates to screen coordinates.
 * @param world_coords The world coordinates.
 * @param camera_coords The camera coordinates.
 * @param window_width The width of the window.
 * @param window_height The height of the window.
 */
ScreenCoordinates convert_to_screen_coordinate(const Coordinates& world_coords, const CameraCoordinates& camera_coords, const int window_width, const int window_height) {
    ScreenCoordinates screen_coord;

    double relative_x = world_coords.x - camera_coords.x;
    double relative_y = world_coords.y - camera_coords.y;
    double relative_z = world_coords.z - camera_coords.z;

    float cos_yaw = cos(degrees_to_radians(camera_coords.yaw));
    float sin_yaw = sin(degrees_to_radians(camera_coords.yaw));
    double new_x = relative_x * cos_yaw + relative_z * sin_yaw;
    double new_z = relative_z * cos_yaw - relative_x * sin_yaw;

    float cos_pitch = cos(degrees_to_radians(camera_coords.pitch));
    float sin_pitch = sin(degrees_to_radians(camera_coords.pitch));
    double new_y = relative_y * cos_pitch - new_z * sin_pitch;
    double final_z = new_z * cos_pitch + relative_y * sin_pitch;

    float cos_roll = cos(degrees_to_radians(camera_coords.roll));
    float sin_roll = sin(degrees_to_radians(camera_coords.roll));
    double final_x = new_x * cos_roll - new_y * sin_roll;
    double final_y = new_y * cos_roll + new_x * sin_roll;


    if (final_z >= 0) {
        screen_coord.x = -1;
        screen_coord.y = -1;
        screen_coord.distance = -1;
        return screen_coord;
    }

    // FOV for 6th cam is always 65 degrees
    double fov_rad = degrees_to_radians(65.0);

    double window_distance = (window_height * (4.0 / 3.0) / 2.0) / tan(fov_rad / 2.0);

    screen_coord.x = (final_x / final_z) * window_distance + (window_width / 2.0);
    screen_coord.y = (final_y / final_z) * window_distance + (window_height / 2.0);

    screen_coord.x = window_width - screen_coord.x;

    screen_coord.distance = sqrt(relative_x * relative_x + relative_y * relative_y + relative_z * relative_z);

    return screen_coord;
}


/**
 * Convert screen coordinates to angles.
 * @param screen_coord The screen coordinates.
 * @param window_width The width of the window.
 * @param window_height The height of the window.
 * @return The angles corresponding to the screen coordinates.
 */
Angles convert_to_angles(const ScreenCoordinates screen_coord, const int window_width, const int window_height) {
    Angles angles;

    // FOV for 6th cam is always 65 degrees
    double fov_rad = degrees_to_radians(65.0);
    double window_distance = (window_height * (4.0 / 3.0) / 2.0) / tan(fov_rad / 2.0);

    angles.azimuth = atan2(screen_coord.x - window_width / 2.0, window_distance) * (180.0f / numbers::pi);
    angles.elevation = atan2(screen_coord.y - window_height / 2.0, window_distance) * (180.0f / numbers::pi);

    return angles;
}


/**
 * Rotate a vector by given rotation angles.
 * @param vector The vector to rotate.
 * @param rotation The rotation angles in degrees.
 */
Coordinates rotate_vector(const Coordinates& vector, const Rotations& rotations) {
    float pitch = degrees_to_radians(rotations.pitch);
    float yaw = degrees_to_radians(rotations.yaw);
    float roll = degrees_to_radians(rotations.roll);

    float cos_pitch = cos(pitch);
    float sin_pitch = sin(pitch);
    float cos_yaw = cos(yaw);
    float sin_yaw = sin(yaw);
    float cos_roll = cos(roll);
    float sin_roll = sin(roll);

    Coordinates result;

    result.x = (
        vector.x * (cos_yaw * cos_roll + sin_yaw * sin_pitch * sin_roll) +
        vector.y * (-sin_roll * cos_yaw + cos_roll * sin_pitch * sin_yaw) +
        vector.z * cos_pitch * sin_yaw
    );

    result.y = (
        vector.x * (cos_pitch * sin_roll) +
        vector.y * cos_roll * cos_pitch +
        vector.z * -sin_pitch
    );

    result.z = (
        vector.x * (-sin_yaw * cos_roll + cos_yaw * sin_pitch * sin_roll) +
        vector.y * (sin_roll * sin_yaw + cos_roll * sin_pitch * cos_yaw) +
        vector.z * cos_pitch * cos_yaw
    );

    return result;
}


/**
 * Get the coordinates of the 6th camera from telemetry data.
 * @param telemetry_data The telemetry data.
 */
CameraCoordinates get_6th_camera_coordinate(TelemetryData* telemetry_data) {
    // vector from the truck center to the 6th camera
    Coordinates offset_vector{
        0.0,
        1.5,
        -0.1
    };
    // only truck rotation
    Rotations truck_rotation{
        static_cast<float>(telemetry_data->truck_dp.rotationY * 360.0),
        static_cast<float>(telemetry_data->truck_dp.rotationX * 360.0),
        static_cast<float>(telemetry_data->truck_dp.rotationZ * 360.0)
    };
    Coordinates rotated_offset = rotate_vector(offset_vector, truck_rotation);

    // truck position with rotated offset and with cabin rotation applied
    CameraCoordinates camera_coords{
        telemetry_data->truck_dp.coordinateX + rotated_offset.x,
        telemetry_data->truck_dp.coordinateY + rotated_offset.y,
        telemetry_data->truck_dp.coordinateZ + rotated_offset.z,
        static_cast<float>(360.0 - telemetry_data->truck_dp.rotationY * 360.0 + 360.0 - telemetry_data->truck_fp.cabinOffsetrotationY * 360.0),
        static_cast<float>(360.0 - telemetry_data->truck_dp.rotationX * 360.0 + 360.0 - telemetry_data->truck_fp.cabinOffsetrotationX * 360.0),
        static_cast<float>(360.0 - telemetry_data->truck_dp.rotationZ * 360.0 + 360.0 - telemetry_data->truck_fp.cabinOffsetrotationZ * 360.0)
    };

    return camera_coords;
}


}