#pragma once

#include "object_detection.h"
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
    PositionEstimation();
    void run(std::vector<ObjectDetection> detections, int window_width, int window_height);

private:
    ScreenCapture* capture_;
    SCSTelemetry telemetry_;
    TelemetryData* telemetry_data_;

    cv::Mat frame_;
    cv::Mat frame_gray_;
    Tracker tracker_{0, 10.0f};
};