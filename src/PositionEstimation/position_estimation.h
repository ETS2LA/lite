#pragma once

#include "PositionEstimation/ground_projection.h"
#include "WheelTrajectory/wheel_trajectory.h"
#include "shared_data.h"
#include "tracker.h"
#include "AR/ar.h"
#include "utils.h"

#include <ets2la_telemetry/telemetry_reader.h>
#include <ets2la_capture/frame_reader.h>


class PositionEstimation {
public:
    PositionEstimation(SharedData& shared_data, AR *ar);
    void run();

private:
    void draw(const std::vector<Tracker::Object>& objects) const;

    utils::PositionEstimationCoordinates estimate_position(
        const utils::CameraCoordinates& camera_coords,
        Tracker::Object& object,
        int window_width,
        int window_height
    );

    AR* ar_;
    SharedData& shared_data_;
    std::shared_ptr<DrawList> draw_list_;
    ets2la_telemetry::TelemetryReader telemetry_reader_;
    ets2la_telemetry::Telemetry telemetry_;
    ets2la_capture::FrameReader route_advisor_reader_;
    ets2la_capture::Frame route_advisor_capture_frame_;
    utils::Timer timer_;

    WheelTrajectory wheel_trajectory_;

    cv::Mat frame_;
    cv::Mat frame_gray_;

    Tracker tracker_{Tracker::Config{}};
    GroundProjection ground_projection_;

    uint64_t last_object_detection_frame_index;
    uint64_t last_capture_qpc_;
};