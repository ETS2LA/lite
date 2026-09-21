#include "PositionEstimation/position_estimation.h"
#include <cmath>
#include <format>

using namespace std;


PositionEstimation::PositionEstimation(AR *ar) {
    draw_list_ = ar->get_draw_list("position_estimation");
    telemetry_data_ = telemetry_.data();
}


utils::Coordinates triangulate_position(
    const utils::CameraCoordinates& camera_coords,
    Tracker::Object& object,
    const int window_width,
    const int window_height
) {
    const utils::CameraCoordinates& cam0 = object.first_camera_coords;
    const utils::Angles& ang0 = object.angles;
    const utils::Angles ang1 = utils::convert_to_angles(
        {object.ground_anchor_x(), object.ground_anchor_y(), 0.0f},
        window_width,
        window_height
    );

    auto get_direction = [](const utils::Angles& angles, const utils::CameraCoordinates& cam) -> utils::Coordinates {
        const double az = utils::degrees_to_radians(static_cast<double>(angles.azimuth));
        const double el = utils::degrees_to_radians(static_cast<double>(angles.elevation));

        const double t_az = std::tan(az);
        const double t_el = -std::tan(el);
        const double len_inv = 1.0 / std::sqrt(t_az * t_az + t_el * t_el + 1.0);

        double x = t_az * len_inv;
        double y = t_el * len_inv;
        double z = -1.0 * len_inv;

        const double roll = utils::degrees_to_radians(static_cast<double>(cam.roll));
        const double c_r = std::cos(roll);
        const double s_r = std::sin(roll);

        // rot_z(-roll): x = x*c + y*s, y = y*c - x*s
        double nx = x * c_r + y * s_r;
        double ny = y * c_r - x * s_r;
        x = nx; y = ny;

        const double pitch = utils::degrees_to_radians(static_cast<double>(cam.pitch));
        const double c_p = std::cos(pitch);
        const double s_p = std::sin(pitch);
        
        // rot_x(-pitch): y = y*c + z*s, z = z*c - y*s
        ny = y * c_p + z * s_p;
        double nz = z * c_p - y * s_p;
        y = ny; z = nz;

        const double yaw = utils::degrees_to_radians(static_cast<double>(cam.yaw));
        const double c_y = std::cos(yaw);
        const double s_y = std::sin(yaw);

        // rot_y(-yaw): x = x*c - z*s, z = z*c + x*s
        nx = x * c_y - z * s_y;
        nz = z * c_y + x * s_y;

        return utils::Coordinates{nx, y, nz};
    };

    const utils::Coordinates p0{cam0.x, cam0.y, cam0.z};
    const utils::Coordinates p1{camera_coords.x, camera_coords.y, camera_coords.z};
    const utils::Coordinates d0 = get_direction(ang0, cam0);
    const utils::Coordinates d1 = get_direction(ang1, camera_coords);

    auto dot = [](const utils::Coordinates& a, const utils::Coordinates& b) -> double {
        return a.x * b.x + a.y * b.y + a.z * b.z;
    };

    const utils::Coordinates r{p0.x - p1.x, p0.y - p1.y, p0.z - p1.z};
    const double a = dot(d0, d0);
    const double b = dot(d0, d1);
    const double c = dot(d1, d1);
    const double d = dot(d0, r);
    const double e = dot(d1, r);
    const double denom = a * c - b * b;

    double t = 0.0;
    double s = 0.0;
    if (std::abs(denom) > 1e-6) {
        t = (b * e - c * d) / denom;
        s = (a * e - b * d) / denom;
    } else if (std::abs(b) > 1e-6) {
        t = 0.0;
        s = d / b;
    }

    // prevent triangulated points from being placed behind either cameras ray
    if (s < 1e-6) {
        s = 1e-6;
    }
    if (t < 0.0) {
        t = 0.0;
    }

    const utils::Coordinates c0{p0.x + d0.x * t, p0.y + d0.y * t, p0.z + d0.z * t};
    const utils::Coordinates c1{p1.x + d1.x * s, p1.y + d1.y * s, p1.z + d1.z * s};

    const double baseline = std::sqrt(r.x * r.x + r.y * r.y + r.z * r.z);
    const double sin_angle = std::sqrt(std::max(0.0, 1.0 - b * b));
    object.accuracy = baseline * sin_angle;

    // compute midpoint and ensure it lies in front of the current camera
    const utils::Coordinates mid{
        (c0.x + c1.x) * 0.5,
        (c0.y + c1.y) * 0.5,
        (c0.z + c1.z) * 0.5
    };

    const utils::Coordinates v1{mid.x - p1.x, mid.y - p1.y, mid.z - p1.z};
    if (dot(d1, v1) < 0.0) {
        object.accuracy = 0.0f;
    }

    return mid;
}


void PositionEstimation::draw(const std::vector<Tracker::Object>& objects) const {
    for (const auto& obj : objects) {
        // Green for a box backed by a real detection this frame, red for a
        // coasted/predicted "ghost" box that has no current detection.
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

    utils::CameraCoordinates camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

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


void PositionEstimation::run(std::vector<ObjectDetection> detections, int window_width, int window_height) {
    draw_list_->clear();
    auto camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    auto objects = tracker_.update(detections, camera_coords, window_width, window_height);
    draw(objects);

    cv::Mat display_frame(500, 500, CV_8UC3, cv::Scalar(0, 0, 0));

    for (auto& obj : objects) {
        //draw_list_->line(
        //    obj.x,
        //    obj.y,
        //    obj.first_x,
        //    obj.first_y,
        //    2,
        //    2,
        //    utils::ColorFloat(1.0f, 1.0f, 0.0f, 1.0f)
        //);

        auto position = triangulate_position(
            camera_coords,
            obj,
            window_width,
            window_height
        );

        if (obj.accuracy < 0.1f) {
            continue;
        }

        double distance = std::sqrt(
            (position.x - camera_coords.x) * (position.x - camera_coords.x) +
            (position.y - camera_coords.y) * (position.y - camera_coords.y) +
            (position.z - camera_coords.z) * (position.z - camera_coords.z)
        );

        float dx = camera_coords.z - position.z;
        float dy = camera_coords.x - position.x;
        float rotated_x = dx * cos(utils::degrees_to_radians(camera_coords.yaw)) - dy * sin(utils::degrees_to_radians(camera_coords.yaw));
        float rotated_y = dx * sin(utils::degrees_to_radians(camera_coords.yaw)) + dy * cos(utils::degrees_to_radians(camera_coords.yaw));
        float y = -(rotated_x * (display_frame.cols / 2.0)) / 25.0f + display_frame.cols;
        float x = -(rotated_y * (display_frame.rows / 2.0)) / 25.0f + display_frame.rows / 2.0;

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

        cv::circle(
            display_frame,
            cv::Point(
                static_cast<int>(x),
                static_cast<int>(y)
            ),
            2,
            (obj.class_id >= 0 && obj.class_id < static_cast<int>(class_colors.size()))
                ? class_colors[obj.class_id]
                : cv::Scalar{255, 255, 255},
            -1
        );

        //draw_list_->circle(
        //    utils::Coordinates(
        //        position.x,
        //        position.y,
        //        position.z
        //    ),
        //    2,
        //    -1,
        //    obj.is_coasting ? utils::ColorFloat(1.0f, 0.0f, 0.0f, 1.0f) : utils::ColorFloat(0.0f, 1.0f, 0.0f, 1.0f)
        //);
        //const std::string label = format("{:.2f}m", distance);
        //const std::wstring wide_label(label.begin(), label.end());
        //draw_list_->text(
        //    wide_label,
        //    utils::Coordinates(
        //        position.x,
        //        position.y,
        //        position.z
        //    ),
        //    13.0f,
        //    obj.is_coasting ? utils::ColorFloat(1.0f, 0.0f, 0.0f, 1.0f) : utils::ColorFloat(0.0f, 1.0f, 0.0f, 1.0f)
        //);
    }

    auto wheel_trajectories = get_wheel_trajectory();
    vector<cv::Point> poly_line_left;
    for (const auto& point : wheel_trajectories.first) {
        float dx = camera_coords.z - point.z;
        float dy = camera_coords.x - point.x;
        float rotated_x = dx * cos(utils::degrees_to_radians(camera_coords.yaw)) - dy * sin(utils::degrees_to_radians(camera_coords.yaw));
        float rotated_y = dx * sin(utils::degrees_to_radians(camera_coords.yaw)) + dy * cos(utils::degrees_to_radians(camera_coords.yaw));
        float y = -(rotated_x * (display_frame.cols / 2.0)) / 25.0f + display_frame.cols;
        float x = -(rotated_y * (display_frame.rows / 2.0)) / 25.0f + display_frame.rows / 2.0;

        poly_line_left.push_back(cv::Point(static_cast<int>(x), static_cast<int>(y)));
    }

    vector<cv::Point> poly_line_right;
    for (const auto& point : wheel_trajectories.second) {
        float dx = camera_coords.z - point.z;
        float dy = camera_coords.x - point.x;
        float rotated_x = dx * cos(utils::degrees_to_radians(camera_coords.yaw)) - dy * sin(utils::degrees_to_radians(camera_coords.yaw));
        float rotated_y = dx * sin(utils::degrees_to_radians(camera_coords.yaw)) + dy * cos(utils::degrees_to_radians(camera_coords.yaw));
        float y = -(rotated_x * (display_frame.cols / 2.0)) / 25.0f + display_frame.cols;
        float x = -(rotated_y * (display_frame.rows / 2.0)) / 25.0f + display_frame.rows / 2.0;

        poly_line_right.push_back(cv::Point(static_cast<int>(x), static_cast<int>(y)));
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