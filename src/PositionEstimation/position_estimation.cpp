#include "PositionEstimation/position_estimation.h"
#include <cmath>
#include <format>

using namespace std;


PositionEstimation::PositionEstimation(AR *ar) {
    draw_list_ = ar->get_draw_list("position_estimation");
    telemetry_data_ = telemetry_.data();
}


bool PositionEstimation::is_ground_projected_class(int class_id) {
    return class_id == 0 || class_id == 1 || class_id == 2 || class_id == 6 || class_id == 9;
}


utils::Coordinates PositionEstimation::estimate_position(
    const utils::CameraCoordinates& camera_coords,
    Tracker::Object& object,
    int window_width,
    int window_height
) {
    if (is_ground_projected_class(object.class_id)) {
        const utils::Angles angles = utils::convert_to_angles(
            {object.ground_anchor_x(), object.ground_anchor_y(), 0.0f},
            window_width,
            window_height
        );

        bool ok = false;
        const utils::Coordinates position = ground_projection_.project_to_ground(angles, camera_coords, ok);
        object.accuracy = ok ? 1.0f : 0.0f;
        return position;
    }

    return triangulate_position(camera_coords, object, window_width, window_height);
}


void PositionEstimation::draw(const std::vector<Tracker::Object>& objects) const {
    for (const auto& obj : objects) {
        const utils::ColorFloat color = obj.is_coasting
            ? utils::ColorFloat(1.0f, 0.0f, 0.0f, 1.0f)
            : utils::ColorFloat(0.0f, 1.0f, 0.0f, 1.0f);

        const float left = obj.x - obj.width * 0.5f;
        const float top = obj.y - obj.height * 0.5f;
        const float right = obj.x + obj.width * 0.5f;
        const float bottom = obj.y + obj.height * 0.5f;

        draw_list_->rectangle(left, top, right, bottom, 3.0f, 1.0f, color);

        const std::string class_name = (obj.class_id >= 0 && obj.class_id < static_cast<int>(kObjectClassNames.size()))
            ? kObjectClassNames[obj.class_id]
            : "unknown";
        const std::string label = obj.is_coasting
            ? std::format("{} (coasting)", class_name)
            : std::format("{} {:.2f}", class_name, obj.confidence);
        const std::wstring wide_label(label.begin(), label.end());
        draw_list_->text(wide_label, left, top - 14, 13.0f, color);
    }
}


double calculate_front_wheel_radius_(double steering_angle, double wheelbase) {
    if (abs(steering_angle) < 0.001) {
        return INFINITY;
    }
    steering_angle = utils::degrees_to_radians(steering_angle);
    return wheelbase / sin(steering_angle);
}


double calculate_back_wheel_radius_(double steering_angle, double wheelbase) {
    if (abs(steering_angle) < 0.001) {
        return INFINITY;
    }
    steering_angle = utils::degrees_to_radians(steering_angle);
    return wheelbase / tan(steering_angle);
}


pair<vector<utils::Coordinates>, vector<utils::Coordinates>> PositionEstimation::get_wheel_trajectory() {
    utils::Rotations truck_rotation{
        static_cast<float>(telemetry_data_->truck_dp.rotationY * 360.0),
        static_cast<float>(telemetry_data_->truck_dp.rotationX * 360.0),
        static_cast<float>(telemetry_data_->truck_dp.rotationZ * 360.0)
    };

    vector<utils::Coordinates> wheel_coords;
    vector<double> wheel_angles;
    for (int i = 0; i < telemetry_data_->config_ui.truckWheelCount; ++i) {
        if (telemetry_data_->config_b.truckWheelSimulated[i]) {
            utils::Coordinates wheel_vector{
                telemetry_data_->config_fv.truckWheelPositionX[i],
                telemetry_data_->config_fv.truckWheelPositionY[i],
                telemetry_data_->config_fv.truckWheelPositionZ[i]
            };
            wheel_vector = utils::rotate_vector(wheel_vector, truck_rotation);
            utils::Coordinates coord{
                telemetry_data_->truck_dp.coordinateX + wheel_vector.x,
                telemetry_data_->truck_dp.coordinateY + wheel_vector.y,
                telemetry_data_->truck_dp.coordinateZ + wheel_vector.z
            };
            wheel_coords.push_back(coord);

            if (telemetry_data_->config_b.truckWheelSteerable[i]) {
                wheel_angles.push_back(
                    telemetry_data_->truck_f.truck_wheelSteering[i] * 360.0f
                );
            }
        }
    }

    if (wheel_coords.size() < 4 || wheel_angles.size() < 2) {
        return make_pair(vector<utils::Coordinates>(), vector<utils::Coordinates>());
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

    double wheel_base_left = sqrt(
        pow(front_left_wheel.x - back_left_wheel.x, 2) +
        pow(front_left_wheel.y - back_left_wheel.y, 2) +
        pow(front_left_wheel.z - back_left_wheel.z, 2)
    );
    double wheel_base_right = sqrt(
        pow(front_right_wheel.x - back_right_wheel.x, 2) +
        pow(front_right_wheel.y - back_right_wheel.y, 2) +
        pow(front_right_wheel.z - back_right_wheel.z, 2)
    );

    double front_left_wheel_radius = calculate_front_wheel_radius_(
        wheel_angles[0],
        wheel_base_left
    );
    double front_right_wheel_radius = calculate_front_wheel_radius_(
        wheel_angles[1],
        wheel_base_right
    );
    double back_left_wheel_radius = calculate_back_wheel_radius_(
        wheel_angles[0],
        wheel_base_left
    );
    double back_right_wheel_radius = calculate_back_wheel_radius_(
        wheel_angles[1],
        wheel_base_right
    );

    if (front_left_wheel_radius == INFINITY) front_left_wheel_radius = 1000000.0;
    if (front_right_wheel_radius == INFINITY) front_right_wheel_radius = 1000000.0;
    if (back_left_wheel_radius == INFINITY) back_left_wheel_radius = 1000000.0;
    if (back_right_wheel_radius == INFINITY) back_right_wheel_radius = 1000000.0;

    utils::Coordinates left_offset_local{
        -back_left_wheel_radius - 0.3,
        0.0,
        0.0
    };
    utils::Coordinates left_offset_world = utils::rotate_vector(left_offset_local, truck_rotation);
    utils::Coordinates left_circle_center{
        back_left_wheel.x + left_offset_world.x,
        telemetry_data_->truck_dp.coordinateY + left_offset_world.y,
        back_left_wheel.z + left_offset_world.z
    };

    utils::Coordinates right_offset_local{
        -back_right_wheel_radius + 0.3,
        0.0,
        0.0
    };
    utils::Coordinates right_offset_world = utils::rotate_vector(right_offset_local, truck_rotation);
    utils::Coordinates right_circle_center{
        back_right_wheel.x + right_offset_world.x,
        telemetry_data_->truck_dp.coordinateY + right_offset_world.y,
        back_right_wheel.z + right_offset_world.z
    };

    vector<utils::Coordinates> wheel_trajectory_left;
    for (int i = 0; i <= 45; ++i) {
        double angle = utils::degrees_to_radians(
            i * (1.0 / -front_left_wheel_radius) * 30.0 - utils::radians_to_degrees(atan(wheel_base_left / front_left_wheel_radius))
        );

        utils::Coordinates local_point{
            front_left_wheel_radius * cos(angle),
            0.0,
            front_left_wheel_radius * sin(angle)
        };
        utils::Coordinates world_point = utils::rotate_vector(local_point, truck_rotation);

        double x = left_circle_center.x + world_point.x;
        double y = left_circle_center.y + world_point.y;
        double z = left_circle_center.z + world_point.z;

        wheel_trajectory_left.push_back({x, y, z});
    }

    vector<utils::Coordinates> wheel_trajectory_right;
    for (int i = 0; i <= 45; ++i) {
        double angle = utils::degrees_to_radians(
            i * (1.0 / -front_right_wheel_radius) * 30.0 - utils::radians_to_degrees(atan(wheel_base_right / front_right_wheel_radius))
        );

        utils::Coordinates local_point{
            front_right_wheel_radius * cos(angle),
            0.0,
            front_right_wheel_radius * sin(angle)
        };
        utils::Coordinates world_point = utils::rotate_vector(local_point, truck_rotation);

        double x = right_circle_center.x + world_point.x;
        double y = right_circle_center.y + world_point.y;
        double z = right_circle_center.z + world_point.z;

        wheel_trajectory_right.push_back({x, y, z});
    }

    return {wheel_trajectory_left, wheel_trajectory_right};
}


cv::Point top_down_view_point(
    const utils::Coordinates& world_point,
    const utils::CameraCoordinates& camera_coords,
    const cv::Size& view_size,
    double meters_range
) {
    const double dx = camera_coords.z - world_point.z;
    const double dy = camera_coords.x - world_point.x;
    const double yaw = utils::degrees_to_radians(static_cast<double>(camera_coords.yaw));
    const double rotated_x = dx * cos(yaw) - dy * sin(yaw);
    const double rotated_y = dx * sin(yaw) + dy * cos(yaw);

    const double y = -(rotated_x * (view_size.width / 2.0)) / meters_range + view_size.width;
    const double x = -(rotated_y * (view_size.height / 2.0)) / meters_range + view_size.height / 2.0;

    return cv::Point(static_cast<int>(x), static_cast<int>(y));
}


void PositionEstimation::run(std::vector<ObjectDetection> detections, int window_width, int window_height) {
    draw_list_->clear();
    auto camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    ground_projection_.update(telemetry_data_);

    auto objects = tracker_.update(detections, camera_coords, window_width, window_height);
    draw(objects);

    cv::Mat display_frame(500, 500, CV_8UC3, cv::Scalar(0, 0, 0));

    vector<cv::Scalar> class_colors = {
        cv::Scalar{0, 255, 0}, // car
        cv::Scalar{255, 255, 0},  // bus
        cv::Scalar{0, 0, 255},  // truck
        cv::Scalar{0, 255, 255},  // stoplight
        cv::Scalar{128, 128, 128},  // streetlamp
        cv::Scalar{255, 75, 75},  // sign
        cv::Scalar{128, 128, 128},  // short post
        cv::Scalar{128, 128, 128},  // long pole
        cv::Scalar{128, 128, 128},  // curved pole
        cv::Scalar{255, 255, 255},  // lane line
        cv::Scalar{0, 25, 50},  // tree trunk
        cv::Scalar{128, 128, 128},  // bridge pier
        cv::Scalar{0, 75, 255},  // traffic cone
        cv::Scalar{0, 75, 255},  // traffic delineator
    };

    for (auto& obj : objects) {
        auto position = estimate_position(camera_coords, obj, window_width, window_height);

        if (obj.accuracy < 0.1f) {
            continue;
        }

        const cv::Point pt = top_down_view_point(position, camera_coords, display_frame.size(), 25);

        cv::circle(
            display_frame,
            pt,
            2,
            (obj.class_id >= 0 && obj.class_id < static_cast<int>(class_colors.size()))
                ? class_colors[obj.class_id]
                : cv::Scalar{255, 255, 255},
            -1
        );
    }

    auto wheel_trajectories = get_wheel_trajectory();
    vector<cv::Point> poly_line_left;
    for (const auto& point : wheel_trajectories.first) {
        poly_line_left.push_back(top_down_view_point(point, camera_coords, display_frame.size(), 25));
    }

    vector<cv::Point> poly_line_right;
    for (const auto& point : wheel_trajectories.second) {
        poly_line_right.push_back(top_down_view_point(point, camera_coords, display_frame.size(), 25));
    }

    cv::polylines(display_frame, poly_line_left, false, cv::Scalar(0, 191, 255), 1);
    cv::polylines(display_frame, poly_line_right, false, cv::Scalar(0, 191, 255), 1);

    cv::circle(
        display_frame,
        cv::Point(static_cast<int>(display_frame.cols / 2.0), static_cast<int>(display_frame.rows)),
        3,
        cv::Scalar(0, 0, 255),
        -1
    );

    draw_list_->publish();

    cv::imshow("Position Estimation Debug", display_frame);
    cv::waitKey(1);
}