#include "WheelTrajectory/wheel_trajectory.h"
#include <numbers>
#include <vector>
#include <array>

using namespace std;


WheelTrajectory::WheelTrajectory(AR *ar) {
    draw_list_ = ar->get_draw_list("wheel_trajectory");
}


double calculate_front_wheel_radius(double steering_angle, double wheelbase) {
    if (abs(steering_angle) < 0.001) {
        return INFINITY;
    }
    steering_angle = utils::degrees_to_radians(steering_angle);
    return wheelbase / sin(steering_angle);
}


double calculate_back_wheel_radius(double steering_angle, double wheelbase) {
    if (abs(steering_angle) < 0.001) {
        return INFINITY;
    }
    steering_angle = utils::degrees_to_radians(steering_angle);
    return wheelbase / tan(steering_angle);
}


Trajectories WheelTrajectory::calculate_front(
    const bool forward,
    const float length,
    const float resolution
) {
    telemetry_reader_.get_latest_telemetry(telemetry_);
    if (!telemetry_.valid || telemetry_.frame_index == last_front_trajectories_index_) {
        return front_trajectories_;
    }
    last_front_trajectories_index_ = telemetry_.frame_index;

    utils::Rotations truck_rotation{
        telemetry_.truck.world.orientation.pitch * 360.0f,
        telemetry_.truck.world.orientation.heading * 360.0f,
        telemetry_.truck.world.orientation.roll * 360.0f
    };

    vector<utils::Coordinates> wheel_coords;
    vector<double> wheel_angles;
    for (uint32_t i = 0; i < telemetry_.truck.wheel_count; ++i) {
        if (telemetry_.truck.wheels[i].simulated) {
            utils::Coordinates wheel_vector{
                telemetry_.truck.wheels[i].position.x,
                telemetry_.truck.wheels[i].position.y +
                telemetry_.truck.wheels[i].suspension_deflection -
                telemetry_.truck.wheels[i].radius,
                telemetry_.truck.wheels[i].position.z
            };
            wheel_vector = utils::rotate_vector(wheel_vector, truck_rotation);
            utils::Coordinates coord{
                telemetry_.truck.world.position.x + wheel_vector.x,
                telemetry_.truck.world.position.y + wheel_vector.y,
                telemetry_.truck.world.position.z + wheel_vector.z
            };
            wheel_coords.push_back(coord);

            if (telemetry_.truck.wheels[i].steerable) {
                wheel_angles.push_back(
                    telemetry_.truck.wheels[i].steering * 360.0f
                );
            }
        }
    }

    if (wheel_coords.size() < 4 || wheel_angles.size() < 2) {
        return front_trajectories_;
    }

    utils::Coordinates front_left_wheel = wheel_coords[0];
    utils::Coordinates front_right_wheel = wheel_coords[1];

    utils::Coordinates back_left_wheel{0, 0, 0};
    utils::Coordinates back_right_wheel{0, 0, 0};

    for (int i = wheel_angles.size(); i < wheel_coords.size(); ++i) {
        if (i % 2 == 0) {
            back_left_wheel.x += wheel_coords[i].x;;
            back_left_wheel.y += wheel_coords[i].y;
            back_left_wheel.z += wheel_coords[i].z;
        } else {
            back_right_wheel.x += wheel_coords[i].x;;
            back_right_wheel.y += wheel_coords[i].y;
            back_right_wheel.z += wheel_coords[i].z;
        }
    }

    back_left_wheel.x /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_left_wheel.y /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_left_wheel.z /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.x /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.y /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.z /= (wheel_coords.size() - wheel_angles.size()) / 2;

    const array<utils::Coordinates, 2> front_wheels{front_left_wheel, front_right_wheel};
    const array<utils::Coordinates, 2> back_wheels{back_left_wheel, back_right_wheel};

    array<utils::Coordinates, 2> circle_centers;
    array<utils::Coordinates, 2> trajectory_normals;
    array<utils::Coordinates, 2> forwards;
    array<double, 2> forward_lengths;
    array<double, 2> back_radii;
    array<double, 2> front_radii;
    array<double, 2> rear_radii;

    for (int side = 0; side < 2; ++side) {
        const utils::Coordinates& front_wheel = front_wheels[side];
        const utils::Coordinates& back_wheel = back_wheels[side];
        const double wheelbase = sqrt(
            pow(front_wheel.x - back_wheel.x, 2) +
            pow(front_wheel.y - back_wheel.y, 2) +
            pow(front_wheel.z - back_wheel.z, 2)
        );
        const double steering_angle = wheel_angles[side];
        const double back_radius = calculate_back_wheel_radius(steering_angle, wheelbase);
        const double center_offset = isinf(back_radius) ? 0.0 : -back_radius;

        forwards[side] = {
            front_wheel.x - back_wheel.x,
            front_wheel.y - back_wheel.y,
            front_wheel.z - back_wheel.z
        };
        utils::Coordinates lateral = utils::rotate_vector({1.0, 0.0, 0.0}, truck_rotation);
        forward_lengths[side] = sqrt(
            pow(forwards[side].x, 2) +
            pow(forwards[side].y, 2) +
            pow(forwards[side].z, 2)
        );
        const double lateral_projection = (
            lateral.x * forwards[side].x +
            lateral.y * forwards[side].y +
            lateral.z * forwards[side].z
        ) / forward_lengths[side];
        lateral.x -= lateral_projection * forwards[side].x / forward_lengths[side];
        lateral.y -= lateral_projection * forwards[side].y / forward_lengths[side];
        lateral.z -= lateral_projection * forwards[side].z / forward_lengths[side];
        const double lateral_length = sqrt(
            pow(lateral.x, 2) +
            pow(lateral.y, 2) +
            pow(lateral.z, 2)
        );
        lateral.x /= lateral_length;
        lateral.y /= lateral_length;
        lateral.z /= lateral_length;

        circle_centers[side] = {
            back_wheel.x + center_offset * lateral.x,
            back_wheel.y + center_offset * lateral.y,
            back_wheel.z + center_offset * lateral.z
        };
        trajectory_normals[side] = {
            forwards[side].y * lateral.z - forwards[side].z * lateral.y,
            forwards[side].z * lateral.x - forwards[side].x * lateral.z,
            forwards[side].x * lateral.y - forwards[side].y * lateral.x
        };
        const double normal_length = sqrt(
            pow(trajectory_normals[side].x, 2) +
            pow(trajectory_normals[side].y, 2) +
            pow(trajectory_normals[side].z, 2)
        );
        trajectory_normals[side].x /= normal_length;
        trajectory_normals[side].y /= normal_length;
        trajectory_normals[side].z /= normal_length;
        back_radii[side] = back_radius;
    }

    circle_centers[0].x = (circle_centers[0].x + circle_centers[1].x) * 0.5;
    circle_centers[0].y = (circle_centers[0].y + circle_centers[1].y) * 0.5;
    circle_centers[0].z = (circle_centers[0].z + circle_centers[1].z) * 0.5;
    circle_centers[1] = circle_centers[0];
    for (int side = 0; side < 2; ++side) {
        const utils::Coordinates& front_wheel = front_wheels[side];
        const utils::Coordinates& back_wheel = back_wheels[side];
        front_radii[side] = sqrt(
            pow(front_wheel.x - circle_centers[side].x, 2) +
            pow(front_wheel.y - circle_centers[side].y, 2) +
            pow(front_wheel.z - circle_centers[side].z, 2)
        );
        rear_radii[side] = sqrt(
            pow(back_wheel.x - circle_centers[side].x, 2) +
            pow(back_wheel.y - circle_centers[side].y, 2) +
            pow(back_wheel.z - circle_centers[side].z, 2)
        );
    }

    array<double, 2> front_lengths{length, length};
    array<double, 2> rear_lengths{length, length};
    const int outer_side = front_radii[0] >= front_radii[1] ? 0 : 1;
    const int inner_side = 1 - outer_side;

    for (int wheel = 0; wheel < 2; ++wheel) {
        if (isinf(back_radii[0]) || isinf(back_radii[1])) {
            continue;
        }
        const double outer_radius = wheel == 0 ? front_radii[outer_side] : rear_radii[outer_side];
        const double inner_radius = wheel == 0 ? front_radii[inner_side] : rear_radii[inner_side];
        const utils::Coordinates& outer_start = wheel == 0 ? front_wheels[outer_side] : back_wheels[outer_side];
        const utils::Coordinates& inner_start = wheel == 0 ? front_wheels[inner_side] : back_wheels[inner_side];
        const double direction = wheel == 0 ? -copysign(1.0, back_radii[outer_side]) : copysign(1.0, back_radii[outer_side]);
        utils::Coordinates outer_radial{
            outer_start.x - circle_centers[outer_side].x,
            outer_start.y - circle_centers[outer_side].y,
            outer_start.z - circle_centers[outer_side].z
        };
        outer_radial.x /= outer_radius;
        outer_radial.y /= outer_radius;
        outer_radial.z /= outer_radius;
        utils::Coordinates outer_tangent{
            trajectory_normals[outer_side].y * outer_radial.z - trajectory_normals[outer_side].z * outer_radial.y,
            trajectory_normals[outer_side].z * outer_radial.x - trajectory_normals[outer_side].x * outer_radial.z,
            trajectory_normals[outer_side].x * outer_radial.y - trajectory_normals[outer_side].y * outer_radial.x
        };
        const double outer_angle = direction * length / outer_radius;
        const utils::Coordinates outer_end{
            circle_centers[outer_side].x +
            outer_radius * (outer_radial.x * cos(outer_angle) +
            outer_tangent.x * sin(outer_angle)),
            circle_centers[outer_side].y +
            outer_radius * (outer_radial.y * cos(outer_angle) +
            outer_tangent.y * sin(outer_angle)),
            circle_centers[outer_side].z +
            outer_radius * (outer_radial.z * cos(outer_angle) +
            outer_tangent.z * sin(outer_angle))
        };
        const utils::Coordinates ray{
            outer_end.x - circle_centers[outer_side].x,
            outer_end.y - circle_centers[outer_side].y,
            outer_end.z - circle_centers[outer_side].z
        };
        const utils::Coordinates center_delta{
            circle_centers[outer_side].x - circle_centers[inner_side].x,
            circle_centers[outer_side].y - circle_centers[inner_side].y,
            circle_centers[outer_side].z - circle_centers[inner_side].z
        };
        const double ray_length_squared = ray.x * ray.x + ray.y * ray.y + ray.z * ray.z;
        const double quadratic_b = 2.0 * (center_delta.x * ray.x + center_delta.y * ray.y + center_delta.z * ray.z);
        const double quadratic_c =
            center_delta.x * center_delta.x +
            center_delta.y * center_delta.y +
            center_delta.z * center_delta.z -
            inner_radius * inner_radius;
        const double discriminant = quadratic_b * quadratic_b - 4.0 * ray_length_squared * quadratic_c;
        if (discriminant < 0.0) {
            continue;
        }
        const double root_a = (-quadratic_b - sqrt(discriminant)) / (2.0 * ray_length_squared);
        const double root_b = (-quadratic_b + sqrt(discriminant)) / (2.0 * ray_length_squared);
        utils::Coordinates inner_radial{
            inner_start.x - circle_centers[inner_side].x,
            inner_start.y - circle_centers[inner_side].y,
            inner_start.z - circle_centers[inner_side].z
        };
        inner_radial.x /= inner_radius;
        inner_radial.y /= inner_radius;
        inner_radial.z /= inner_radius;
        const utils::Coordinates inner_tangent{
            trajectory_normals[inner_side].y * inner_radial.z -
            trajectory_normals[inner_side].z * inner_radial.y,
            trajectory_normals[inner_side].z * inner_radial.x -
            trajectory_normals[inner_side].x * inner_radial.z,
            trajectory_normals[inner_side].x * inner_radial.y -
            trajectory_normals[inner_side].y * inner_radial.x
        };
        double inner_length = INFINITY;
        const array<double, 2> roots{root_a, root_b};
        for (double root : roots) {
            if (root <= 0.0) {
                continue;
            }
            const utils::Coordinates candidate{
                circle_centers[outer_side].x + root * ray.x,
                circle_centers[outer_side].y + root * ray.y,
                circle_centers[outer_side].z + root * ray.z
            };
            utils::Coordinates candidate_radial{
                candidate.x - circle_centers[inner_side].x,
                candidate.y - circle_centers[inner_side].y,
                candidate.z - circle_centers[inner_side].z
            };
            candidate_radial.x /= inner_radius;
            candidate_radial.y /= inner_radius;
            candidate_radial.z /= inner_radius;
            const double candidate_angle = atan2(
                candidate_radial.x * inner_tangent.x +
                candidate_radial.y * inner_tangent.y +
                candidate_radial.z * inner_tangent.z,
                candidate_radial.x * inner_radial.x +
                candidate_radial.y * inner_radial.y +
                candidate_radial.z * inner_radial.z
            );
            double candidate_length = direction * candidate_angle;
            while (candidate_length < 0.0) {
                candidate_length += 2.0 * numbers::pi;
            }
            candidate_length *= inner_radius;
            if (candidate_length < inner_length) {
                inner_length = candidate_length;
            }
        }
        if (!isfinite(inner_length)) {
            continue;
        }
        if (wheel == 0) {
            front_lengths[inner_side] = inner_length;
        } else {
            rear_lengths[inner_side] = inner_length;
        }
    }

    front_trajectories_ = {};
     for (int side = 0; side < 2; ++side) {
        const utils::Coordinates& start = front_wheels[side];
        const double radius = front_radii[side];
        const double direction = forward ? -copysign(1.0, back_radii[side]) : copysign(1.0, back_radii[side]);
        const double length = front_lengths[side];

        for (int i = 0; i <= int(length * resolution); ++i) {
            utils::Coordinates point;
            if (isinf(back_radii[side])) {
                const double distance = i / resolution;
                point = {
                    start.x + distance * forwards[side].x / forward_lengths[side],
                    start.y + distance * forwards[side].y / forward_lengths[side],
                    start.z + distance * forwards[side].z / forward_lengths[side]
                };
            } else {
                utils::Coordinates radial{
                    start.x - circle_centers[side].x,
                    start.y - circle_centers[side].y,
                    start.z - circle_centers[side].z
                };
                const double radial_length = sqrt(
                    pow(radial.x, 2) +
                    pow(radial.y, 2) +
                    pow(radial.z, 2)
                );
                radial.x /= radial_length;
                radial.y /= radial_length;
                radial.z /= radial_length;
                utils::Coordinates tangent{
                    trajectory_normals[side].y * radial.z -
                    trajectory_normals[side].z * radial.y,
                    trajectory_normals[side].z * radial.x -
                    trajectory_normals[side].x * radial.z,
                    trajectory_normals[side].x * radial.y -
                    trajectory_normals[side].y * radial.x
                };
                const double angle = direction * i / resolution / radius;
                point = {
                    circle_centers[side].x + radius * (radial.x * cos(angle) + tangent.x * sin(angle)),
                    circle_centers[side].y + radius * (radial.y * cos(angle) + tangent.y * sin(angle)),
                    circle_centers[side].z + radius * (radial.z * cos(angle) + tangent.z * sin(angle))
                };
                if (i == 0) {
                    point = start;
                }
            }
            if (side == 0) {
                front_trajectories_.left_trajectory.push_back(point);
            } else {
                front_trajectories_.right_trajectory.push_back(point);
            }
        }
    }

    return front_trajectories_;
}


Trajectories WheelTrajectory::calculate_back(
    const bool forward,
    const float length,
    const float resolution
) {
    telemetry_reader_.get_latest_telemetry(telemetry_);
    if (!telemetry_.valid || telemetry_.frame_index == last_back_trajectories_index_) {
        return back_trajectories_;
    }
    last_back_trajectories_index_ = telemetry_.frame_index;

    utils::Rotations truck_rotation{
        telemetry_.truck.world.orientation.pitch * 360.0f,
        telemetry_.truck.world.orientation.heading * 360.0f,
        telemetry_.truck.world.orientation.roll * 360.0f
    };

    vector<utils::Coordinates> wheel_coords;
    vector<double> wheel_angles;
    for (uint32_t i = 0; i < telemetry_.truck.wheel_count; ++i) {
        if (telemetry_.truck.wheels[i].simulated) {
            utils::Coordinates wheel_vector{
                telemetry_.truck.wheels[i].position.x,
                telemetry_.truck.wheels[i].position.y +
                telemetry_.truck.wheels[i].suspension_deflection -
                telemetry_.truck.wheels[i].radius,
                telemetry_.truck.wheels[i].position.z
            };
            wheel_vector = utils::rotate_vector(wheel_vector, truck_rotation);
            utils::Coordinates coord{
                telemetry_.truck.world.position.x + wheel_vector.x,
                telemetry_.truck.world.position.y + wheel_vector.y,
                telemetry_.truck.world.position.z + wheel_vector.z
            };
            wheel_coords.push_back(coord);

            if (telemetry_.truck.wheels[i].steerable) {
                wheel_angles.push_back(
                    telemetry_.truck.wheels[i].steering * 360.0f
                );
            }
        }
    }

    if (wheel_coords.size() < 4 || wheel_angles.size() < 2) {
        return back_trajectories_;
    }

    utils::Coordinates front_left_wheel = wheel_coords[0];
    utils::Coordinates front_right_wheel = wheel_coords[1];

    utils::Coordinates back_left_wheel{0, 0, 0};
    utils::Coordinates back_right_wheel{0, 0, 0};

    for (int i = wheel_angles.size(); i < wheel_coords.size(); ++i) {
        if (i % 2 == 0) {
            back_left_wheel.x += wheel_coords[i].x;;
            back_left_wheel.y += wheel_coords[i].y;
            back_left_wheel.z += wheel_coords[i].z;
        } else {
            back_right_wheel.x += wheel_coords[i].x;;
            back_right_wheel.y += wheel_coords[i].y;
            back_right_wheel.z += wheel_coords[i].z;
        }
    }

    back_left_wheel.x /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_left_wheel.y /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_left_wheel.z /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.x /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.y /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.z /= (wheel_coords.size() - wheel_angles.size()) / 2;

    const array<utils::Coordinates, 2> front_wheels{front_left_wheel, front_right_wheel};
    const array<utils::Coordinates, 2> back_wheels{back_left_wheel, back_right_wheel};

    array<utils::Coordinates, 2> circle_centers;
    array<utils::Coordinates, 2> trajectory_normals;
    array<utils::Coordinates, 2> forwards;
    array<double, 2> forward_lengths;
    array<double, 2> back_radii;
    array<double, 2> front_radii;
    array<double, 2> rear_radii;

    for (int side = 0; side < 2; ++side) {
        const utils::Coordinates& front_wheel = front_wheels[side];
        const utils::Coordinates& back_wheel = back_wheels[side];
        const double wheelbase = sqrt(
            pow(front_wheel.x - back_wheel.x, 2) +
            pow(front_wheel.y - back_wheel.y, 2) +
            pow(front_wheel.z - back_wheel.z, 2)
        );
        const double steering_angle = wheel_angles[side];
        const double back_radius = calculate_back_wheel_radius(steering_angle, wheelbase);
        const double center_offset = isinf(back_radius) ? 0.0 : -back_radius;

        forwards[side] = {
            front_wheel.x - back_wheel.x,
            front_wheel.y - back_wheel.y,
            front_wheel.z - back_wheel.z
        };
        utils::Coordinates lateral = utils::rotate_vector({1.0, 0.0, 0.0}, truck_rotation);
        forward_lengths[side] = sqrt(
            pow(forwards[side].x, 2) +
            pow(forwards[side].y, 2) +
            pow(forwards[side].z, 2)
        );
        const double lateral_projection = (
            lateral.x * forwards[side].x +
            lateral.y * forwards[side].y +
            lateral.z * forwards[side].z
        ) / forward_lengths[side];
        lateral.x -= lateral_projection * forwards[side].x / forward_lengths[side];
        lateral.y -= lateral_projection * forwards[side].y / forward_lengths[side];
        lateral.z -= lateral_projection * forwards[side].z / forward_lengths[side];
        const double lateral_length = sqrt(
            pow(lateral.x, 2) +
            pow(lateral.y, 2) +
            pow(lateral.z, 2)
        );
        lateral.x /= lateral_length;
        lateral.y /= lateral_length;
        lateral.z /= lateral_length;

        circle_centers[side] = {
            back_wheel.x + center_offset * lateral.x,
            back_wheel.y + center_offset * lateral.y,
            back_wheel.z + center_offset * lateral.z
        };
        trajectory_normals[side] = {
            forwards[side].y * lateral.z - forwards[side].z * lateral.y,
            forwards[side].z * lateral.x - forwards[side].x * lateral.z,
            forwards[side].x * lateral.y - forwards[side].y * lateral.x
        };
        const double normal_length = sqrt(
            pow(trajectory_normals[side].x, 2) +
            pow(trajectory_normals[side].y, 2) +
            pow(trajectory_normals[side].z, 2)
        );
        trajectory_normals[side].x /= normal_length;
        trajectory_normals[side].y /= normal_length;
        trajectory_normals[side].z /= normal_length;
        back_radii[side] = back_radius;
    }

    circle_centers[0].x = (circle_centers[0].x + circle_centers[1].x) * 0.5;
    circle_centers[0].y = (circle_centers[0].y + circle_centers[1].y) * 0.5;
    circle_centers[0].z = (circle_centers[0].z + circle_centers[1].z) * 0.5;
    circle_centers[1] = circle_centers[0];
    for (int side = 0; side < 2; ++side) {
        const utils::Coordinates& front_wheel = front_wheels[side];
        const utils::Coordinates& back_wheel = back_wheels[side];
        front_radii[side] = sqrt(
            pow(front_wheel.x - circle_centers[side].x, 2) +
            pow(front_wheel.y - circle_centers[side].y, 2) +
            pow(front_wheel.z - circle_centers[side].z, 2)
        );
        rear_radii[side] = sqrt(
            pow(back_wheel.x - circle_centers[side].x, 2) +
            pow(back_wheel.y - circle_centers[side].y, 2) +
            pow(back_wheel.z - circle_centers[side].z, 2)
        );
    }

    array<double, 2> front_lengths{length, length};
    array<double, 2> rear_lengths{length, length};
    const int outer_side = front_radii[0] >= front_radii[1] ? 0 : 1;
    const int inner_side = 1 - outer_side;

    for (int wheel = 0; wheel < 2; ++wheel) {
        if (isinf(back_radii[0]) || isinf(back_radii[1])) {
            continue;
        }
        const double outer_radius = wheel == 0 ? front_radii[outer_side] : rear_radii[outer_side];
        const double inner_radius = wheel == 0 ? front_radii[inner_side] : rear_radii[inner_side];
        const utils::Coordinates& outer_start = wheel == 0 ? front_wheels[outer_side] : back_wheels[outer_side];
        const utils::Coordinates& inner_start = wheel == 0 ? front_wheels[inner_side] : back_wheels[inner_side];
        const double direction = wheel == 0 ? -copysign(1.0, back_radii[outer_side]) : copysign(1.0, back_radii[outer_side]);
        utils::Coordinates outer_radial{
            outer_start.x - circle_centers[outer_side].x,
            outer_start.y - circle_centers[outer_side].y,
            outer_start.z - circle_centers[outer_side].z
        };
        outer_radial.x /= outer_radius;
        outer_radial.y /= outer_radius;
        outer_radial.z /= outer_radius;
        utils::Coordinates outer_tangent{
            trajectory_normals[outer_side].y * outer_radial.z - trajectory_normals[outer_side].z * outer_radial.y,
            trajectory_normals[outer_side].z * outer_radial.x - trajectory_normals[outer_side].x * outer_radial.z,
            trajectory_normals[outer_side].x * outer_radial.y - trajectory_normals[outer_side].y * outer_radial.x
        };
        const double outer_angle = direction * length / outer_radius;
        const utils::Coordinates outer_end{
            circle_centers[outer_side].x +
            outer_radius * (outer_radial.x * cos(outer_angle) +
            outer_tangent.x * sin(outer_angle)),
            circle_centers[outer_side].y +
            outer_radius * (outer_radial.y * cos(outer_angle) +
            outer_tangent.y * sin(outer_angle)),
            circle_centers[outer_side].z +
            outer_radius * (outer_radial.z * cos(outer_angle) +
            outer_tangent.z * sin(outer_angle))
        };
        const utils::Coordinates ray{
            outer_end.x - circle_centers[outer_side].x,
            outer_end.y - circle_centers[outer_side].y,
            outer_end.z - circle_centers[outer_side].z
        };
        const utils::Coordinates center_delta{
            circle_centers[outer_side].x - circle_centers[inner_side].x,
            circle_centers[outer_side].y - circle_centers[inner_side].y,
            circle_centers[outer_side].z - circle_centers[inner_side].z
        };
        const double ray_length_squared = ray.x * ray.x + ray.y * ray.y + ray.z * ray.z;
        const double quadratic_b = 2.0 * (center_delta.x * ray.x + center_delta.y * ray.y + center_delta.z * ray.z);
        const double quadratic_c =
            center_delta.x * center_delta.x +
            center_delta.y * center_delta.y +
            center_delta.z * center_delta.z -
            inner_radius * inner_radius;
        const double discriminant = quadratic_b * quadratic_b - 4.0 * ray_length_squared * quadratic_c;
        if (discriminant < 0.0) {
            continue;
        }
        const double root_a = (-quadratic_b - sqrt(discriminant)) / (2.0 * ray_length_squared);
        const double root_b = (-quadratic_b + sqrt(discriminant)) / (2.0 * ray_length_squared);
        utils::Coordinates inner_radial{
            inner_start.x - circle_centers[inner_side].x,
            inner_start.y - circle_centers[inner_side].y,
            inner_start.z - circle_centers[inner_side].z
        };
        inner_radial.x /= inner_radius;
        inner_radial.y /= inner_radius;
        inner_radial.z /= inner_radius;
        const utils::Coordinates inner_tangent{
            trajectory_normals[inner_side].y * inner_radial.z -
            trajectory_normals[inner_side].z * inner_radial.y,
            trajectory_normals[inner_side].z * inner_radial.x -
            trajectory_normals[inner_side].x * inner_radial.z,
            trajectory_normals[inner_side].x * inner_radial.y -
            trajectory_normals[inner_side].y * inner_radial.x
        };
        double inner_length = INFINITY;
        const array<double, 2> roots{root_a, root_b};
        for (double root : roots) {
            if (root <= 0.0) {
                continue;
            }
            const utils::Coordinates candidate{
                circle_centers[outer_side].x + root * ray.x,
                circle_centers[outer_side].y + root * ray.y,
                circle_centers[outer_side].z + root * ray.z
            };
            utils::Coordinates candidate_radial{
                candidate.x - circle_centers[inner_side].x,
                candidate.y - circle_centers[inner_side].y,
                candidate.z - circle_centers[inner_side].z
            };
            candidate_radial.x /= inner_radius;
            candidate_radial.y /= inner_radius;
            candidate_radial.z /= inner_radius;
            const double candidate_angle = atan2(
                candidate_radial.x * inner_tangent.x +
                candidate_radial.y * inner_tangent.y +
                candidate_radial.z * inner_tangent.z,
                candidate_radial.x * inner_radial.x +
                candidate_radial.y * inner_radial.y +
                candidate_radial.z * inner_radial.z
            );
            double candidate_length = direction * candidate_angle;
            while (candidate_length < 0.0) {
                candidate_length += 2.0 * numbers::pi;
            }
            candidate_length *= inner_radius;
            if (candidate_length < inner_length) {
                inner_length = candidate_length;
            }
        }
        if (!isfinite(inner_length)) {
            continue;
        }
        if (wheel == 0) {
            front_lengths[inner_side] = inner_length;
        } else {
            rear_lengths[inner_side] = inner_length;
        }
    }

    back_trajectories_ = {};
     for (int side = 0; side < 2; ++side) {
        const utils::Coordinates& start = back_wheels[side];
        const double radius = rear_radii[side];
        const double direction = forward ? -copysign(1.0, back_radii[side]) : copysign(1.0, back_radii[side]);
        const double length = rear_lengths[side];

        for (int i = 0; i <= int(length * resolution); ++i) {
            utils::Coordinates point;
            if (isinf(back_radii[side])) {
                const double distance = -i / resolution;
                point = {
                    start.x + distance * forwards[side].x / forward_lengths[side],
                    start.y + distance * forwards[side].y / forward_lengths[side],
                    start.z + distance * forwards[side].z / forward_lengths[side]
                };
            } else {
                utils::Coordinates radial{
                    start.x - circle_centers[side].x,
                    start.y - circle_centers[side].y,
                    start.z - circle_centers[side].z
                };
                const double radial_length = sqrt(
                    pow(radial.x, 2) +
                    pow(radial.y, 2) +
                    pow(radial.z, 2)
                );
                radial.x /= radial_length;
                radial.y /= radial_length;
                radial.z /= radial_length;
                utils::Coordinates tangent{
                    trajectory_normals[side].y * radial.z -
                    trajectory_normals[side].z * radial.y,
                    trajectory_normals[side].z * radial.x -
                    trajectory_normals[side].x * radial.z,
                    trajectory_normals[side].x * radial.y -
                    trajectory_normals[side].y * radial.x
                };
                const double angle = direction * i / resolution / radius;
                point = {
                    circle_centers[side].x + radius * (radial.x * cos(angle) + tangent.x * sin(angle)),
                    circle_centers[side].y + radius * (radial.y * cos(angle) + tangent.y * sin(angle)),
                    circle_centers[side].z + radius * (radial.z * cos(angle) + tangent.z * sin(angle))
                };
                if (i == 0) {
                    point = start;
                }
            }
            if (side == 0) {
                back_trajectories_.left_trajectory.push_back(point);
            } else {
                back_trajectories_.right_trajectory.push_back(point);
            }
        }
    }

    return back_trajectories_;
}


// Clear the draw list of the wheel trajectories
void WheelTrajectory::draw_clear() {
    draw_list_->clear();
}

// Send the draw list to AR for rendering
void WheelTrajectory::draw_publish() {
    draw_list_->publish();
}


// Draw the front wheel trajectories
void WheelTrajectory::draw_front(
    const bool forward,
    const float length,
    const float resolution,
    const float thickness,
    const utils::ColorFloat& color
) {
    get_front(forward, length, resolution);
    draw_list_->polyline(
        front_trajectories_.left_trajectory,
        false,
        false,
        thickness,
        color
    );
    draw_list_->polyline(
        front_trajectories_.right_trajectory,
        false,
        false,
        thickness,
        color
    );
}


// Draw the back wheel trajectories
void WheelTrajectory::draw_back(
    const bool forward,
    const float length,
    const float resolution,
    const float thickness,
    const utils::ColorFloat& color
) {
    get_back(forward, length, resolution);
    draw_list_->polyline(
        back_trajectories_.left_trajectory,
        false,
        false,
        thickness,
        color
    );
    draw_list_->polyline(
        back_trajectories_.right_trajectory,
        false,
        false,
        thickness,
        color
    );
}


// Get the front wheel trajectories
Trajectories WheelTrajectory::get_front(
    const bool forward,
    const float length,
    const float resolution
) {
    return calculate_front(forward, length, resolution);
}


// Get the back wheel trajectories
Trajectories WheelTrajectory::get_back(
    const bool forward,
    const float length,
    const float resolution
) {
    return calculate_back(forward, length, resolution);
}