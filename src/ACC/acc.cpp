#include "ACC/acc.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

const float min_distance = 7.5f;
const float max_distance = 50.0f;
const float following_time = 1.0f;

struct LeadVehicle {
    float distance = std::numeric_limits<float>::max();
    int id = -1;
};

bool is_vehicle(const PositionedObject& object) {
    return object.tracking.class_id >= 0 && object.tracking.class_id <= 2;
}

float cross_product(
    const utils::Coordinates& a,
    const utils::Coordinates& b,
    const utils::Coordinates& point
) {
    return static_cast<float>(
        (b.x - a.x) * (point.z - a.z) -
        (b.z - a.z) * (point.x - a.x)
    );
}

void update_lead(
    const std::vector<utils::Coordinates>& left,
    const std::vector<utils::Coordinates>& right,
    const utils::Coordinates& object_position,
    int object_id,
    float object_speed,
    LeadVehicle& lead
) {
    const size_t sample_count = std::min(left.size(), right.size());
    if (sample_count < 2) {
        return;
    }

    float distance_from_start = 0.0f;
    for (size_t i = 1; i < sample_count; ++i) {
        const auto& previous_left = left[i - 1];
        const auto& current_left = left[i];
        const auto& previous_right = right[i - 1];
        const auto& current_right = right[i];
        const auto& previous_center = previous_left;
        const auto& current_center = current_left;
        const float segment_length = static_cast<float>(std::hypot(
            current_center.x - previous_center.x,
            current_center.z - previous_center.z
        ));
        if (segment_length <= 0.0f) {
            continue;
        }

        const std::array<utils::Coordinates, 4> corridor{
            previous_left,
            current_left,
            current_right,
            previous_right
        };
        bool has_positive_cross = false;
        bool has_negative_cross = false;
        for (size_t edge = 0; edge < corridor.size(); ++edge) {
            const float cross = cross_product(
                corridor[edge],
                corridor[(edge + 1) % corridor.size()],
                object_position
            );
            has_positive_cross = has_positive_cross || cross > 0.0f;
            has_negative_cross = has_negative_cross || cross < 0.0f;
        }

        if (!has_positive_cross || !has_negative_cross) {
            const float path_distance = distance_from_start + segment_length * 0.5f;
            if (path_distance < lead.distance) {
                lead.distance = path_distance;
                lead.id = object_id;
            }
        }

        distance_from_start += segment_length;
        if (distance_from_start > max_distance) {
            break;
        }
    }
}


bool ACC::update() {
    input_.update();

    controller_.enabled(enabled_);
    if (!enabled_) {
        return false;
    }

    ets2la_telemetry::Telemetry telemetry;
    if (!telemetry_reader_.get_telemetry(telemetry, 0)) {
        controller_.target_speed.reset();
        controller_.update();
        return false;
    }

    const auto positions = shared_data_.get<PositionSnapshot>("positions");
    const float speed_limit = telemetry.truck.navigation_speed_limit;
    const bool has_speed_limit = std::isfinite(speed_limit) && speed_limit > 0.0f;
    LeadVehicle lead;
    const auto trajectories = wheel_trajectory_.get_front(true, 35.0f, 1.0f);
    const uint64_t timestamp_us = telemetry.game.simulation_time_us;

    if (positions && !telemetry.game.paused) {
        for (const auto& object : positions->objects) {
            if (!object.position_valid || object.tracking.is_coasting || !is_vehicle(object)) {
                continue;
            }
            LeadVehicle candidate;
            update_lead(
                trajectories.left_trajectory,
                trajectories.right_trajectory,
                object.position,
                object.tracking.id,
                0.0f,
                candidate
            );
            if (!std::isfinite(candidate.distance)) {
                continue;
            }

            if (candidate.distance < lead.distance) {
                lead = candidate;
            }
        }
    }

    const bool close_vehicle = std::isfinite(lead.distance) && lead.distance < max_distance;
    if (telemetry.game.paused || (!has_speed_limit && !std::isfinite(lead.distance))) {
        controller_.target_speed.reset();
    } else {
        controller_.target_speed = has_speed_limit ? speed_limit : telemetry.truck.speed;
    }

    if (std::isfinite(lead.distance) && lead.distance < max_distance - 1.0f && !telemetry.game.paused) {
        controller_.target_speed.reset();
        controller_.set(
            ets2la_controller::Axis::throttle,
            0.0f
        );
        controller_.set(
            ets2la_controller::Axis::brake,
            0.25f
        );
    }

    controller_.update();
    return true;
}