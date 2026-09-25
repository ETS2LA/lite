#pragma once

#include "PositionEstimation/ground_projection.h"
#include "PositionEstimation/triangulation.h"
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
    PositionEstimation(AR *ar);
    void run(std::vector<ObjectDetection> detections, int window_width, int window_height);
    std::pair<std::vector<utils::Coordinates>, std::vector<utils::Coordinates>> get_wheel_trajectory();

private:
    void draw(const std::vector<Tracker::Object>& objects) const;

    utils::Coordinates estimate_position(
        const utils::CameraCoordinates& camera_coords,
        Tracker::Object& object,
        int window_width,
        int window_height
    );

    static bool is_ground_projected_class(int class_id);

    std::shared_ptr<DrawList> draw_list_;
    ScreenCapture* capture_;
    SCSTelemetry telemetry_;
    TelemetryData* telemetry_data_;

    cv::Mat frame_;
    cv::Mat frame_gray_;

    Tracker tracker_{Tracker::Config{}};
    GroundProjection ground_projection_;
};