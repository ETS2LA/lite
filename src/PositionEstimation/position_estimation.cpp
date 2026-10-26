#include "PositionEstimation/position_estimation.h"
#include <format>
#include <cmath>

using namespace std;


PositionEstimation::PositionEstimation(AR *ar, SharedData& shared_data):
wheel_trajectory_(ar),
shared_data_(shared_data)
{
    draw_list_ = ar->get_draw_list("position_estimation");
    telemetry_reader_.get_latest_telemetry(telemetry_);
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
    if (!telemetry_reader_.get_latest_telemetry(telemetry_)) {
        return;
    }

    draw_list_->clear();
    auto camera_coords = utils::get_6th_camera_coordinate(telemetry_);

    ground_projection_.update(telemetry_);

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

    PositionEstimationData position_estimation_data;
    position_estimation_data.objects.reserve(objects.size());

    for (auto& obj : objects) {
        auto position = estimate_position(camera_coords, obj, window_width, window_height);

        const bool position_valid = obj.accuracy >= 0.1f;

        position_estimation_data.objects.push_back(PositionEstimationObject{
            .tracking = obj,
            .position = position,
            .position_valid = position_valid
        });

        if (!position_valid) {
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

    shared_data_.set("position_estimation", move(position_estimation_data));

    wheel_trajectory_.draw_clear();
    wheel_trajectory_.draw_front();
    wheel_trajectory_.draw_publish();
    auto wheel_trajectories = wheel_trajectory_.get_front();

    vector<cv::Point> poly_line_left;
    for (const auto& point : wheel_trajectories.left_trajectory) {
        poly_line_left.push_back(top_down_view_point(point, camera_coords, display_frame.size(), 25));
    }

    vector<cv::Point> poly_line_right;
    for (const auto& point : wheel_trajectories.right_trajectory) {
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