#include "utils.h"

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


}