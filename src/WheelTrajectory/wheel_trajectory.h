#pragma once

#include "AR/ar.h"
#include "utils.h"

#include <ets2la_telemetry/telemetry_reader.h>
#include <vector>


struct Trajectories {
    std::vector<utils::Coordinates> left_trajectory;
    std::vector<utils::Coordinates> right_trajectory;
};

class WheelTrajectory {
public:
    WheelTrajectory(AR *ar);
    void draw_clear();
    void draw_publish();
    void draw_front(
        const bool forward = true,
        const float length = 25.0f,
        const float resolution = 2.0f,
        const float thickness = 3.0f,
        const utils::ColorFloat& color = {1.0f, 0.75f, 0.0f, 1.0f}
    );
    void draw_back(
        const bool forward = false,
        const float length = 25.0f,
        const float resolution = 2.0f,
        const float thickness = 3.0f,
        const utils::ColorFloat& color = {0.0f, 0.75f, 1.0f, 1.0f}
    );
    Trajectories get_front(
        const bool forward = true,
        const float length = 25.0f,
        const float resolution = 2.0f
    );
    Trajectories get_back(
        const bool forward = false,
        const float length = 25.0f,
        const float resolution = 2.0f
    );

private:
    Trajectories calculate_front(
        const bool forward,
        const float length,
        const float resolution
    );
    Trajectories calculate_back(
        const bool forward,
        const float length,
        const float resolution
    );

    uint32_t last_front_trajectories_index_;
    Trajectories front_trajectories_;

    uint32_t last_back_trajectories_index_;
    Trajectories back_trajectories_;

    ets2la_telemetry::TelemetryReader telemetry_reader_;
    ets2la_telemetry::Telemetry telemetry_;

    std::shared_ptr<DrawList> draw_list_;
};