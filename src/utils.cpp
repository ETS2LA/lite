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

}