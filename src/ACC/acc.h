#pragma once

#include "WheelTrajectory/wheel_trajectory.h"
#include "shared_data.h"
#include "controller.h"
#include "input.h"

#include <ets2la_telemetry/telemetry_reader.h>
#include <unordered_map>
#include <memory>


class ACC {
public:
    ACC(const SharedData& shared_data):
    shared_data_(shared_data)
    {
        input_.register_key_binding({"y", [this]() { enabled_ = !enabled_; }});
    }
    bool update();

private:
    const SharedData& shared_data_;
    ets2la_telemetry::TelemetryReader telemetry_reader_;
    WheelTrajectory wheel_trajectory_;
    InputHandler input_;
    Controller controller_;
    bool enabled_ = true;
};