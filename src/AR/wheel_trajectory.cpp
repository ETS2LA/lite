#include "AR/ar.h"
#include <vector>

using namespace std;


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


void AR::draw_wheel_trajectory(const utils::ColorFloat& color) {
    utils::Rotation truck_rotation{
        static_cast<float>(telemetry_data_->truck_dp.rotationY * 360.0),
        static_cast<float>(telemetry_data_->truck_dp.rotationX * 360.0),
        static_cast<float>(telemetry_data_->truck_dp.rotationZ * 360.0)
    };

    vector<utils::Coordinate> wheel_coords;
    vector<double> wheel_angles;
    for (int i = 0; i < telemetry_data_->config_ui.truckWheelCount; ++i) {
        if (telemetry_data_->config_b.truckWheelSimulated[i]) {
            utils::Coordinate wheel_vector{
                telemetry_data_->config_fv.truckWheelPositionX[i],
                telemetry_data_->config_fv.truckWheelPositionY[i],
                telemetry_data_->config_fv.truckWheelPositionZ[i]
            };
            wheel_vector = utils::rotate_vector(wheel_vector, truck_rotation);
            utils::Coordinate coord{
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
        return;
    }

    utils::Coordinate front_left_wheel = wheel_coords[0];
    utils::Coordinate front_right_wheel = wheel_coords[1];

    utils::Coordinate back_left_wheel{0, 0, 0};
    utils::Coordinate back_right_wheel{0, 0, 0};

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

    double front_left_wheel_radius = calculate_front_wheel_radius(
        wheel_angles[0],
        wheel_base_left
    );
    double front_right_wheel_radius = calculate_front_wheel_radius(
        wheel_angles[1],
        wheel_base_right
    );
    double back_left_wheel_radius = calculate_back_wheel_radius(
        wheel_angles[0],
        wheel_base_left
    );
    double back_right_wheel_radius = calculate_back_wheel_radius(
        wheel_angles[1],
        wheel_base_right
    );

    if (front_left_wheel_radius == INFINITY) front_left_wheel_radius = 1000000.0;
    if (front_right_wheel_radius == INFINITY) front_right_wheel_radius = 1000000.0;
    if (back_left_wheel_radius == INFINITY) back_left_wheel_radius = 1000000.0;
    if (back_right_wheel_radius == INFINITY) back_right_wheel_radius = 1000000.0;

    utils::Coordinate left_offset_local{
        -back_left_wheel_radius - 0.3,
        0.0,
        0.0
    };
    utils::Coordinate left_offset_world = utils::rotate_vector(left_offset_local, truck_rotation);
    utils::Coordinate left_circle_center{
        back_left_wheel.x + left_offset_world.x,
        telemetry_data_->truck_dp.coordinateY + left_offset_world.y,
        back_left_wheel.z + left_offset_world.z
    };

    utils::Coordinate right_offset_local{
        -back_right_wheel_radius + 0.3,
        0.0,
        0.0
    };
    utils::Coordinate right_offset_world = utils::rotate_vector(right_offset_local, truck_rotation);
    utils::Coordinate right_circle_center{
        back_right_wheel.x + right_offset_world.x,
        telemetry_data_->truck_dp.coordinateY + right_offset_world.y,
        back_right_wheel.z + right_offset_world.z
    };

    utils::CameraCoordinate camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    glLineWidth(3.0f);
    glColor4f(color.r, color.g, color.b, color.a);
    glBegin(GL_LINE_STRIP);
    for (int i = 0; i <= 45; ++i) {
        double angle = utils::degrees_to_radians(
            i * (1.0 / -front_left_wheel_radius) * 30.0 - utils::radians_to_degrees(atan(wheel_base_left / front_left_wheel_radius))
        );

        utils::Coordinate local_point{
            front_left_wheel_radius * cos(angle),
            0.0,
            front_left_wheel_radius * sin(angle)
        };
        utils::Coordinate world_point = utils::rotate_vector(local_point, truck_rotation);

        double x = left_circle_center.x + world_point.x;
        double y = left_circle_center.y + world_point.y;
        double z = left_circle_center.z + world_point.z;

        utils::ScreenCoordinate screen_coords = utils::convert_to_screen_coordinate(
            {x, y, z},
            camera_coords,
            window_width_,
            window_height_
        );
        if (screen_coords.distance < 0) {
            continue;
        }

        glVertex2f(
            (screen_coords.x / window_width_) * 2 - 1,
            1 - (screen_coords.y / window_height_) * 2
        );
    }
    glEnd();

    glBegin(GL_LINE_STRIP);
    for (int i = 0; i <= 45; ++i) {
        double angle = utils::degrees_to_radians(
            i * (1.0 / -front_right_wheel_radius) * 30.0 - utils::radians_to_degrees(atan(wheel_base_right / front_right_wheel_radius))
        );

        utils::Coordinate local_point{
            front_right_wheel_radius * cos(angle),
            0.0,
            front_right_wheel_radius * sin(angle)
        };
        utils::Coordinate world_point = utils::rotate_vector(local_point, truck_rotation);

        double x = right_circle_center.x + world_point.x;
        double y = right_circle_center.y + world_point.y;
        double z = right_circle_center.z + world_point.z;

        utils::ScreenCoordinate screen_coords = utils::convert_to_screen_coordinate(
            {x, y, z},
            camera_coords,
            window_width_,
            window_height_
        );
        if (screen_coords.distance < 0) {
            continue;
        }

        glVertex2f(
            (screen_coords.x / window_width_) * 2 - 1,
            1 - (screen_coords.y / window_height_) * 2
        );
    }
    glEnd();
}