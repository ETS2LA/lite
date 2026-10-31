#pragma once

#include <ets2la_telemetry/telemetry_reader.h>
#include <ets2la_capture/frame_reader.h>
#include <opencv2/opencv.hpp>

#include "controller.h"
#include "AR/ar.h"
#include "input.h"
#include "utils.h"

#define TURN_NONE 0
#define TURN_LEFT 1
#define TURN_RIGHT 2


class SharedData;

class NavigationDetection {
public:
    NavigationDetection(SharedData& shared_data, AR *ar);
    void update();

private:
    std::pair<float, float> get_lane_position(
        const std::vector<int>& lane_edges,
        int y_coordinate
    );

    ets2la_capture::Frame capture_frame_;
    ets2la_capture::FrameReader reader_;

    SharedData& shared_data_;
    std::shared_ptr<DrawList> draw_list_;
    ets2la_telemetry::TelemetryReader telemetry_reader_;
    ets2la_telemetry::Telemetry telemetry_;
    InputHandler input_;
    Controller controller_;

    cv::Mat frame_;
    cv::Mat mask_red_green_;
    cv::Mat mask_red_;
    cv::Mat mask_green_;

    const cv::Scalar lower_red_{2, 2, 197, 0};
    const cv::Scalar upper_red_{119, 133, 238, 255};
    const cv::Scalar lower_green_{0, 241, 07, 0};
    const cv::Scalar upper_green_{119, 255, 120, 255};

    bool control_enabled_ = true;
    float last_correction_ = 0.0f;
    int detection_offset_lane_y_ = 0;

    int lane_change_current_lane_ = 0;
    float lane_change_target_offset_ = 0.0f;
    float lane_change_offset_ = 0.0f;
    float lane_change_progress_ = 0.0f;
    double lane_change_start_time_ = 0.0;
    float lane_change_start_offset_ = 0.0f;

    bool turn_ahead_detected_ = false;
    float last_turn_ahead_detected_ = 0.0f;
    int turn_ahead_direction_ = TURN_NONE;

    bool indicator_left_ = false;
    bool indicator_right_ = false;
    bool last_indicator_left_ = false;
    bool last_indicator_right_ = false;
    bool indicator_left_wait_for_response_ = false;
    bool indicator_right_wait_for_response_ = false;
    double indicator_left_response_timer_ = 0.0;
    double indicator_right_response_timer_ = 0.0;
};