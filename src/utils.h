#pragma once

#include <opencv2/opencv.hpp>
#include <windows.h>
#include <string>
#include <vector>

#include "capture.h"


namespace utils {

HWND find_window(const std::wstring& window_name, const std::vector<std::wstring>& blacklist);
void apply_route_advisor_crop(cv::Mat& frame, const bool side_right = true);
double get_time_seconds();

}