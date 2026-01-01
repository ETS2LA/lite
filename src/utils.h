#pragma once

#include <opencv2/opencv.hpp>
#include <windows.h>
#include <string>
#include <vector>

#include "capture.h"


namespace utils {

HWND find_window(const std::wstring& window_name, const std::vector<std::wstring>& blacklist);
std::vector<int> get_window_position(HWND hwnd);
void apply_route_advisor_crop(cv::Mat& frame, const bool side_right = true);
double get_time_seconds();
void set_icon(HWND hwnd, const std::wstring& icon_path);
void set_window_title_bar_color(HWND hwnd, COLORREF color);
void set_window_outline_color(HWND hwnd, COLORREF color);

}