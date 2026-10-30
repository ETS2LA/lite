#pragma once

#include "tracker.h"
#include "utils.h"


utils::PositionEstimationCoordinates triangulate_position(
    const utils::CameraCoordinates& camera_coords,
    Tracker::Object& object,
    const int window_width,
    const int window_height
);