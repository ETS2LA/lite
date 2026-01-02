#include "utils.h"
#include <numbers>

using namespace std;


namespace utils {


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
    float width = static_cast<float>(frame.cols);
    float height = static_cast<float>(frame.rows);
    int map_x1, map_y1, map_x2, map_y2;
    int arrow_x1, arrow_y1, arrow_x2, arrow_y2;

    int ra_distance_right = 21;
    int ra_distance_bottom = 100;
    int ra_width = 420;
    int ra_height = 219;
    float scale = height / 1080.0f;

    if (side_right == false) {
        map_x1 = static_cast<int>(std::round(ra_distance_right * scale - 1.0f));
        map_y1 = static_cast<int>(std::round(height - (ra_distance_bottom * scale + ra_height * scale)));
        map_x2 = static_cast<int>(std::round(ra_distance_right * scale + ra_width * scale - 1.0f));
        map_y2 = static_cast<int>(std::round(height - (ra_distance_bottom * scale)));
    } else {
        map_x1 = static_cast<int>(std::round(width - (ra_distance_right * scale + ra_width * scale)));
        map_y1 = static_cast<int>(std::round(height - (ra_distance_bottom * scale + ra_height * scale)));
        map_x2 = static_cast<int>(std::round(width - (ra_distance_right * scale)));
        map_y2 = static_cast<int>(std::round(height - (ra_distance_bottom * scale)));
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
void set_icon(HWND hwnd, const std::wstring& icon_path) {
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
 * Convert world coordinates to screen coordinates.
 * @param world_coords The world coordinates.
 * @param camera_coords The camera coordinates.
 * @param window_width The width of the window.
 * @param window_height The height of the window.
 */
ScreenCoordinate convert_to_screen_coordinate(const Coordinate& world_coords, const CameraCoordinate& camera_coords, const int window_width, const int window_height) {
    ScreenCoordinate screen_coord;

    double relative_x = world_coords.x - camera_coords.x;
    double relative_y = world_coords.y - camera_coords.y;
    double relative_z = world_coords.z - camera_coords.z;

    float cos_yaw = cosf(degrees_to_radians(camera_coords.yaw));
    float sin_yaw = sinf(degrees_to_radians(camera_coords.yaw));
    double new_x = relative_x * cos_yaw + relative_z * sin_yaw;
    double new_z = relative_z * cos_yaw - relative_x * sin_yaw;

    float cos_pitch = cosf(degrees_to_radians(camera_coords.pitch));
    float sin_pitch = sinf(degrees_to_radians(camera_coords.pitch));
    double new_y = relative_y * cos_pitch - new_z * sin_pitch;
    double final_z = new_z * cos_pitch + relative_y * sin_pitch;

    float cos_roll = cosf(degrees_to_radians(camera_coords.roll));
    float sin_roll = sinf(degrees_to_radians(camera_coords.roll));
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
 * Rotate a vector by given rotation angles.
 * @param vector The vector to rotate.
 * @param rotation The rotation angles in degrees.
 */
Coordinate rotate_vector(const Coordinate& vector, const Rotation& rotation) {
    float pitch = degrees_to_radians(rotation.pitch);
    float yaw = degrees_to_radians(rotation.yaw);
    float roll = degrees_to_radians(rotation.roll);

    float cos_pitch = cosf(pitch);
    float sin_pitch = sinf(pitch);
    float cos_yaw = cosf(yaw);
    float sin_yaw = sinf(yaw);
    float cos_roll = cosf(roll);
    float sin_roll = sinf(roll);

    Coordinate result;

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
CameraCoordinate get_6th_camera_coordinate(TelemetryData* telemetry_data) {
    // vector from the truck center to the 6th camera
    Coordinate offset_vector{
        0.0,
        1.5,
        -0.1
    };
    // only truck rotation
    Rotation truck_rotation{
        telemetry_data->truck_dp.rotationY * 360.0,
        telemetry_data->truck_dp.rotationX * 360.0,
        telemetry_data->truck_dp.rotationZ * 360.0
    };
    Coordinate rotated_offset = rotate_vector(offset_vector, truck_rotation);

    // truck position with rotated offset and with cabin rotation applied
    CameraCoordinate camera_coords{
        telemetry_data->truck_dp.coordinateX + rotated_offset.x,
        telemetry_data->truck_dp.coordinateY + rotated_offset.y,
        telemetry_data->truck_dp.coordinateZ + rotated_offset.z,
        360.0 - telemetry_data->truck_dp.rotationY * 360.0 + 360.0 - telemetry_data->truck_fp.cabinOffsetrotationY * 360.0,
        360.0 - telemetry_data->truck_dp.rotationX * 360.0 + 360.0 - telemetry_data->truck_fp.cabinOffsetrotationX * 360.0,
        360.0 - telemetry_data->truck_dp.rotationZ * 360.0 + 360.0 - telemetry_data->truck_fp.cabinOffsetrotationZ * 360.0
    };

    return camera_coords;
}


}