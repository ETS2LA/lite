#pragma once

#include "WheelTrajectory/wheel_trajectory.h"
#include "shared_data.h"
#include "controller.h"
#include "input.h"
#include "utils.h"

#include <ets2la_telemetry/telemetry_reader.h>
#include <unordered_map>
#include <cstdint>
#include <deque>
#include <memory>


struct ObjectPositionSample {
    utils::Coordinates position;
    uint64_t timestamp_qpc = 0;
};

struct ObjectMotion {
    float speed = 0.0f;
    utils::Coordinates heading{0.0, 0.0, 0.0};
};


class ACC {
public:
    ACC(SharedData& shared_data, AR *ar);
    bool update();

private:
    SharedData& shared_data_;
    std::shared_ptr<DrawList> draw_list_;
    ets2la_telemetry::TelemetryReader telemetry_reader_;
    ets2la_telemetry::Telemetry telemetry_;
    WheelTrajectory wheel_trajectory_;
    InputHandler input_;
    Controller controller_;
    bool enabled_ = true;

    float speed_limit_;
    float previous_target_speed_;
    std::unordered_map<int, std::deque<ObjectPositionSample>> object_position_history_;
    std::unordered_map<int, ObjectMotion> object_motions_;
    uint64_t last_position_frame_index_ = 0;
    bool has_position_snapshot_ = false;
};