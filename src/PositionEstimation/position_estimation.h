#pragma once

#include "PositionEstimation/ground_projection.h"
#include "ObjectDetection/object_detection.h"
#include "PositionEstimation/triangulation.h"
#include "WheelTrajectory/wheel_trajectory.h"
#include "shared_data.h"
#include "tracker.h"
#include "camera.h"
#include "AR/ar.h"
#include "input.h"
#include "utils.h"

#include <ets2la_telemetry/telemetry_reader.h>
#include <opencv2/opencv.hpp>
#include <functional>
#include <windows.h>
#include <thread>


class PositionEstimation {
public:
    PositionEstimation(SharedData& shared_data, AR *ar);
    void run(std::vector<ObjectDetection> detections, int window_width, int window_height);

private:
    void draw(const std::vector<Tracker::Object>& objects) const;

    utils::PositionEstimationCoordinates estimate_position(
        const utils::CameraCoordinates& camera_coords,
        Tracker::Object& object,
        int window_width,
        int window_height
    );

    static bool is_ground_projected_class(int class_id);

    AR* ar_;
    SharedData& shared_data_;
    std::shared_ptr<DrawList> draw_list_;
    ets2la_telemetry::TelemetryReader telemetry_reader_;
    ets2la_telemetry::Telemetry telemetry_;

    WheelTrajectory wheel_trajectory_;

    cv::Mat frame_;
    cv::Mat frame_gray_;

    Tracker tracker_{Tracker::Config{}};
    GroundProjection ground_projection_;
};