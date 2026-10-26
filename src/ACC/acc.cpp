#include "ACC/acc.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

constexpr float min_distance = 7.5f;
constexpr float max_distance = 50.0f;
constexpr float following_time = 1.0f;

struct LeadVehicle {
    float distance = std::numeric_limits<float>::max();
    int id = -1;
};

bool is_vehicle(const PositionEstimationObject& object) {
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

    const auto navigation_detection = shared_data_.get<NavigationDetectionData>("navigation_detection");
    const auto position_estimation = shared_data_.get<PositionEstimationData>("position_estimation");

    LeadVehicle lead;
    const auto trajectories = wheel_trajectory_.get_front(true, max_distance, 1.0f);
    float speed_limit = navigation_detection->turn == 0 ? telemetry.truck.navigation_speed_limit : 25.0f/3.6f;
    if (speed_limit <= 0.0f) speed_limit = 30.0f/3.6f;

    if (position_estimation && !telemetry.game.paused) {
        for (const auto& object : position_estimation->objects) {
            if (!object.position_valid || object.tracking.is_coasting || !is_vehicle(object)) {
                continue;
            }
            LeadVehicle candidate;
            update_lead(
                trajectories.left_trajectory,
                trajectories.right_trajectory,
                object.position,
                object.tracking.id,
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

    if (telemetry.game.paused) {
        controller_.target_speed.reset();
    } else {
        float target_speed = speed_limit;
        if (std::isfinite(lead.distance) && !telemetry.game.paused) {
            const float desired_distance = std::clamp(
                min_distance + telemetry.truck.speed * following_time,
                min_distance,
                max_distance
            );
            if (lead.distance < desired_distance) {
                const float available_distance = desired_distance - min_distance;
                const float distance_ratio = available_distance > 0.0f
                    ? (lead.distance - min_distance) / available_distance
                    : 0.0f;
                target_speed = std::min(
                    target_speed,
                    std::max(0.0f, telemetry.truck.speed * distance_ratio)
                );
            }
        }
        controller_.target_speed = target_speed;
    }

    controller_.update();
    return true;
}