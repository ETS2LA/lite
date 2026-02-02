#pragma once

#include "telemetry.h"
#include "capture.h"
#include "tracker.h"
#include "camera.h"
#include "AR/ar.h"
#include "input.h"
#include "utils.h"

#include <opencv2/opencv.hpp>
#include <functional>
#include <windows.h>
#include <thread>


class PositionEstimation {
public:
    PositionEstimation(ScreenCapture* capture);
    PositionEstimation(std::function<HWND()> target_window_handle_function);
    void run(AR& ar);

    std::vector<std::pair<float, float>> get_keypoints(cv::Mat& frame);
    std::vector<std::pair<float, float>> get_keypoints();

private:
    ScreenCapture* capture_;
    SCSTelemetry telemetry_;
    InputHandler input_handler_;
    TelemetryData* telemetry_data_;
    cv::Ptr<cv::FastFeatureDetector> feature_detector_ = cv::FastFeatureDetector::create(10, true, cv::FastFeatureDetector::TYPE_9_16);

    cv::Mat frame_;
    cv::Mat frame_gray_;
    int window_width_;
    int window_height_;
    Tracker tracker_;

    // TEMP:
    Tracker::Object test_object_;
    utils::Coordinates target_{
        10350,
        45,
        -9166
    };
};