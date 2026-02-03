#include "PositionEstimation/position_estimation.h"
#include <cmath>

using namespace std;


PositionEstimation::PositionEstimation(std::function<HWND()> target_window_handle_function) {
    capture_ = new ScreenCapture(target_window_handle_function);
    capture_->initialize();

    telemetry_data_ = telemetry_.data();
    window_width_ = capture_->get_capture_region().x2 - capture_->get_capture_region().x1;
    window_height_ = capture_->get_capture_region().y2 - capture_->get_capture_region().y1;
}

PositionEstimation::PositionEstimation(ScreenCapture* capture)
    : capture_(capture) {

    telemetry_data_ = telemetry_.data();
    window_width_ = capture_->get_capture_region().x2 - capture_->get_capture_region().x1;
    window_height_ = capture_->get_capture_region().y2 - capture_->get_capture_region().y1;
}


utils::Coordinates triangulate_position(
    const utils::CameraCoordinates& camera_coords,
    Tracker::Object& object,
    const int window_width,
    const int window_height
) {
    const utils::CameraCoordinates& cam0 = object.camera_coords;
    const utils::Angles& ang0 = object.angles;
    const utils::Angles ang1 = utils::convert_to_angles(
        {object.x, object.y, 0.0f},
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


void PositionEstimation::run(AR& ar) {
    window_width_ = capture_->get_capture_region().x2 - capture_->get_capture_region().x1;
    window_height_ = capture_->get_capture_region().y2 - capture_->get_capture_region().y1;

    auto camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    auto keypoints = get_keypoints();
    auto objects = tracker_.update(keypoints, camera_coords, window_width_, window_height_);

    cv::Mat display_frame(500, 500, CV_8UC3, cv::Scalar(0, 0, 0));

    for (const auto& kp : keypoints) {
        ar.rectangle(
            kp.first - 2.0f,
            kp.second - 2.0f,
            kp.first + 2.0f,
            kp.second + 2.0f,
            0.0f,
            1.0f,
            utils::ColorFloat{1.0f, 0.0f, 0.0f, 1.0f}
        );
    }

    for (auto& obj : objects) {
        auto position = triangulate_position(
            camera_coords,
            obj,
            window_width_,
            window_height_
        );

        if (obj.accuracy < 0.1f) {
            continue;
        }

        double distance = std::sqrt(
            (position.x - camera_coords.x) * (position.x - camera_coords.x) +
            (position.y - camera_coords.y) * (position.y - camera_coords.y) +
            (position.z - camera_coords.z) * (position.z - camera_coords.z)
        );
        cv::circle(
            display_frame,
            cv::Point(static_cast<int>((camera_coords.z - position.z) * 3.0f + display_frame.cols / 2.0), static_cast<int>(display_frame.rows / 2.0 - (camera_coords.x - position.x) * 3.0f)),
            2,
            cv::Scalar(
                abs(position.y - camera_coords.y) <= 1.0f ? 127 + (position.y - camera_coords.y) * 15.0f : 0,
                abs(position.y - camera_coords.y) > 1.0f ? 127 + (position.y - camera_coords.y) * 15.0f : 0,
                abs(position.y - camera_coords.y) <= 1.0f ? 127 + (position.y - camera_coords.y) * 15.0f : 0
            ),
            -1
        );
    }
    cv::circle(
        display_frame,
        cv::Point(static_cast<int>(display_frame.cols / 2.0), static_cast<int>(display_frame.rows / 2.0)),
        3,
        cv::Scalar(0, 0, 255),
        -1
    );
    cv::imshow("Position Estimation Debug", display_frame);
    cv::waitKey(1);
}