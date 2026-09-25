#pragma once

#include "telemetry.h"
#include "utils.h"

#include <opencv2/opencv.hpp>


class GroundProjection {
public:
    struct GroundPlane {
        utils::Coordinates point;
        utils::Coordinates normal;
        float pitch_degrees = 0.0f;
        float roll_degrees = 0.0f;
        bool valid = false;
    };

    void update(TelemetryData* telemetry_data);

    utils::Coordinates project_to_ground(
        const utils::Angles& angles,
        const utils::CameraCoordinates& camera_coords,
        bool& ok
    ) const;

    const GroundPlane& plane() const { return plane_; }

private:
    GroundPlane plane_;
};
