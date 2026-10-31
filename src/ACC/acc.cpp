#include "ACC/acc.h"

#include <unordered_set>
#include <algorithm>
#include <limits>
#include <array>
#include <cmath>

using namespace std;


constexpr float min_distance = 5.0f;
constexpr float restart_distance = 7.5f;
constexpr float max_distance = 60.0f;
constexpr float following_time = 1.5f;

struct LeadVehicle {
    float distance = numeric_limits<float>::max();
    float speed = 0.0f;
    utils::Coordinates heading{0.0, 0.0, 0.0};
    int id = -1;
};

ObjectMotion calculate_object_motion(
    const utils::Coordinates& current_position,
    int object_id,
    uint64_t timestamp_qpc,
    ets2la_telemetry::TelemetryReader& telemetry_reader,
    unordered_map<int, deque<ObjectPositionSample>>& position_history
) {
    auto& history = position_history[object_id];
    if (!history.empty() && timestamp_qpc <= history.back().timestamp_qpc) {
        return {};
    }

    history.push_back(ObjectPositionSample{
        current_position,
        timestamp_qpc
    });

    constexpr double motion_window_seconds = 0.5;
    while (history.size() > 2) {
        const double age_seconds = telemetry_reader.ticks_to_ms(
            timestamp_qpc - history.front().timestamp_qpc
        ) / 1000.0;
        if (age_seconds <= motion_window_seconds) {
            break;
        }
        history.pop_front();
    }

    if (history.size() < 2) {
        return {};
    }

    const double delta_time = telemetry_reader.ticks_to_ms(
        timestamp_qpc - history.front().timestamp_qpc
    ) / 1000.0;
    if (delta_time <= 0.0) {
        return {};
    }

    const double delta_x = current_position.x - history.front().position.x;
    const double delta_z = current_position.z - history.front().position.z;
    const double distance = hypot(delta_x, delta_z);

    ObjectMotion motion;
    motion.speed = static_cast<float>(distance / delta_time);
    if (distance > 0.0) {
        motion.heading = {
            delta_x / distance,
            0.0,
            delta_z / distance
        };
    }
    return motion;
}

float relative_speed(
    const ObjectMotion& object_motion,
    const ets2la_telemetry::Telemetry& telemetry
) {
    const utils::Rotations truck_rotation{
        telemetry.truck.world.orientation.pitch * 360.0f,
        telemetry.truck.world.orientation.heading * 360.0f,
        telemetry.truck.world.orientation.roll * 360.0f
    };
    const utils::Coordinates forward = utils::rotate_vector(
        {0.0, 0.0, -1.0},
        truck_rotation
    );

    float speed = static_cast<float>(
        object_motion.speed * (
            object_motion.heading.x * forward.x +
            object_motion.heading.y * forward.y +
            object_motion.heading.z * forward.z
        ) - telemetry.truck.speed
    );

    if (abs(speed) < 1) {
        speed = 0;
    }
    return speed;
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
    const vector<utils::Coordinates>& left,
    const vector<utils::Coordinates>& right,
    const utils::Coordinates& object_position,
    int object_id,
    LeadVehicle& lead
) {
    const size_t sample_count = min(left.size(), right.size());
    if (sample_count < 2) {
        return;
    }

    float distance_from_start = 0.0f;
    for (size_t i = 1; i < sample_count; ++i) {
        const auto& previous_left = left[i - 1];
        const auto& current_left = left[i];
        const auto& previous_right = right[i - 1];
        const auto& current_right = right[i];
        const utils::Coordinates previous_center{
            (previous_left.x + previous_right.x) * 0.5,
            (previous_left.y + previous_right.y) * 0.5,
            (previous_left.z + previous_right.z) * 0.5
        };
        const utils::Coordinates current_center{
            (current_left.x + current_right.x) * 0.5,
            (current_left.y + current_right.y) * 0.5,
            (current_left.z + current_right.z) * 0.5
        };
        const float segment_length = static_cast<float>(hypot(
            current_center.x - previous_center.x,
            current_center.z - previous_center.z
        ));
        if (segment_length <= 0.0f) {
            continue;
        }

        const array<utils::Coordinates, 4> corridor{
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
            const double segment_x = current_center.x - previous_center.x;
            const double segment_z = current_center.z - previous_center.z;
            const double point_x = object_position.x - previous_center.x;
            const double point_z = object_position.z - previous_center.z;
            const double segment_squared_length = segment_x * segment_x + segment_z * segment_z;
            const double projection = segment_squared_length > 0.0 ?
                (point_x * segment_x + point_z * segment_z) / segment_squared_length : 0.0;
            const float path_distance = distance_from_start + segment_length * static_cast<float>(
                clamp(projection, 0.0, 1.0)
            );
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


ACC::ACC(SharedData& shared_data, AR *ar):
shared_data_(shared_data)
{
    draw_list_ = ar->get_draw_list("acc");

    input_.register_key_binding(
        KeyBinding{
            "y",
            [this]() {
                enabled_ = !enabled_;
            }
        }
    );
}


bool ACC::update() {
    input_.update();

    controller_.enabled(enabled_);
    if (!enabled_) {
        return false;
    }

    if (!telemetry_reader_.get_telemetry(telemetry_, 0)) {
        controller_.target_speed.reset();
        controller_.update();
        return false;
    }

    const auto navigation_detection = shared_data_.get<NavigationDetectionData>("navigation_detection");
    const auto position_estimation = shared_data_.get<PositionEstimationData>("position_estimation");

    LeadVehicle lead;
    const auto trajectories = wheel_trajectory_.get_front(true, max_distance, 1.0f);

    const bool turning = navigation_detection->turn != 0;

    if (telemetry_.truck.navigation_speed_limit > 0.0f) {
        speed_limit_ = telemetry_.truck.navigation_speed_limit;
    }

    float target_speed = turning ? 25.0f / 3.6f : speed_limit_;

    if (target_speed > 0.0f) {
        if (abs(previous_target_speed_ - target_speed) > 0.01f) {
            controller_.distance_speed(30, target_speed);

            if (controller_.distance_speed_enabled()) {
                previous_target_speed_ = target_speed;
            }
        }
    } else {
        controller_.disable_distance_speed();
        previous_target_speed_ = 0.0f;
    }

    if (position_estimation && !telemetry_.game.paused) {
        const bool is_new_position_snapshot = !has_position_snapshot_ ||
            position_estimation->frame_index != last_position_frame_index_;
        if (is_new_position_snapshot) {
            last_position_frame_index_ = position_estimation->frame_index;
            has_position_snapshot_ = true;
        }

        unordered_set<int> current_vehicle_ids;
        for (const auto& object : position_estimation->objects) {
            if (!object.position_valid || object.tracking.is_coasting || !is_vehicle(object.tracking.class_id)) {
                continue;
            }
            current_vehicle_ids.insert(object.tracking.id);
        }
        if (is_new_position_snapshot) {
            for (auto it = object_position_history_.begin(); it != object_position_history_.end();) {
                if (!current_vehicle_ids.contains(it->first)) {
                    object_motions_.erase(it->first);
                    it = object_position_history_.erase(it);
                } else {
                    ++it;
                }
            }
        }

        for (const auto& object : position_estimation->objects) {
            if (!object.position_valid || object.tracking.is_coasting || !is_vehicle(object.tracking.class_id)) {
                continue;
            }
            if (is_new_position_snapshot) {
                object_motions_[object.tracking.id] = calculate_object_motion(
                    object.position.center,
                    object.tracking.id,
                    position_estimation->timestamp_qpc,
                    telemetry_reader_,
                    object_position_history_
                );
            }
            const auto motion = object_motions_.find(object.tracking.id);
            const ObjectMotion object_motion = motion != object_motions_.end() ? motion->second  : ObjectMotion{};
            LeadVehicle candidate;
            candidate.heading = object_motion.heading;
            candidate.speed = relative_speed(object_motion, telemetry_);
            update_lead(
                trajectories.left_trajectory,
                trajectories.right_trajectory,
                object.position.left,
                object.tracking.id,
                candidate
            );
            update_lead(
                trajectories.left_trajectory,
                trajectories.right_trajectory,
                object.position.right,
                object.tracking.id,
                candidate
            );
            update_lead(
                trajectories.left_trajectory,
                trajectories.right_trajectory,
                object.position.center,
                object.tracking.id,
                candidate
            );
            if (!isfinite(candidate.distance)) {
                continue;
            }

            if (candidate.distance < lead.distance) {
                lead = candidate;
            }
        }
    }

    if (telemetry_.game.paused) {
        controller_.target_speed.reset();
    } else {
        if (isfinite(lead.distance) && !telemetry_.game.paused) {
            const float desired_distance = clamp(
                min_distance + (telemetry_.truck.speed - lead.speed) * following_time,
                min_distance,
                max_distance
            );
            if (lead.distance < desired_distance) {
                const float available_distance = desired_distance - min_distance;
                const float distance_ratio = available_distance > 0.0f
                    ? (lead.distance - min_distance) / available_distance
                    : 0.0f;
                target_speed = min(
                    target_speed,
                    max(0.0f, telemetry_.truck.speed * distance_ratio)
                );
            }
            if (telemetry_.truck.speed <= 0.5f &&
                lead.distance < restart_distance) {
                target_speed = 0.0f;
            }
            controller_.disable_distance_speed();
        }
        controller_.target_speed = target_speed;
    }

    draw_list_->rectangle(
        utils::ScreenCoordinates{0, 0, 0},
        utils::ScreenCoordinates(300, 110, 0),
        0,
        -1,
        utils::ColorFloat{0, 0, 0, 0.5}
    );
    draw_list_->text(
        format(L"ACC: {}\nTarget Speed: {:.2f} km/h\nLead Vehicle: {}\nDistance: {:.2f} m\nRelative Speed: {:.2f} km/h",
            enabled_ ? L"Enabled" : L"Disabled",
            target_speed * 3.6f,
            lead.id >= 0 ? to_wstring(lead.id) : L"None",
            lead.distance < 10e3 ? lead.distance : 0.0f,
            lead.speed * 3.6f
        ),
        10.0f,
        26.0f,
        16.0f,
        utils::ColorFloat(1.0f, 1.0f, 1.0f, 1.0f)
    );
    draw_list_->publish();

    controller_.update();
    return true;
}