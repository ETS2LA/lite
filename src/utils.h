#pragma once

#include <windows.h>
#include <string>
#include <vector>


namespace utils {

HWND find_window(const std::wstring& window_name, const std::vector<std::wstring>& blacklist);

}