#include "PositionEstimation/position_estimation.h"
#include "triangulation.h"
#include <format>
#include <cmath>

using namespace std;


PositionEstimation::PositionEstimation(SharedData& shared_data, AR *ar):
wheel_trajectory_(ar),
shared_data_(shared_data)
{
    draw_list_ = ar->get_draw_list("position_estimation");
    telemetry_reader_.get_latest_telemetry(telemetry_);
}


utils::PositionEstimationCoordinates PositionEstimation::estimate_position(
    const utils::CameraCoordinates& camera_coords,
    Tracker::Object& object,
    int window_width,
    int window_height
) {
    utils::Coordinates position_left{0.0, 0.0, 0.0};
    utils::Coordinates position_right{0.0, 0.0, 0.0};
    bool ok = false;

    if (object_classes::is_ground_projected(object.class_id)) {
        if (object_classes::is_vehicle(object.class_id)) {
            const utils::Angles angles_left = utils::convert_to_angles(
                {object.half_left_x(), object.bottom_y()},
                window_width,
                window_height
            );
            const utils::Angles angles_right = utils::convert_to_angles(
                {object.half_right_x(), object.bottom_y()},
                window_width,
                window_height
            );
            position_left = ground_projection_.project_to_ground(angles_left, camera_coords, ok);
            position_right = ground_projection_.project_to_ground(angles_right, camera_coords, ok);
            object.accuracy = ok ? 1.0f : 0.0f;
        }

        const utils::Angles angles_center = utils::convert_to_angles(
            {object.center_x(), object.bottom_y()},
            window_width,
            window_height
        );
        const utils::Coordinates position_center = ground_projection_.project_to_ground(angles_center, camera_coords, ok);
        object.accuracy = ok ? 1.0f : 0.0f;

        return utils::PositionEstimationCoordinates{
            position_left,
            position_right,
            position_center
        };
    }

    return triangulate_position(camera_coords, object, window_width, window_height);
}


void PositionEstimation::draw(const vector<Tracker::Object>& objects) const {
    for (const auto& obj : objects) {
        const utils::ColorFloat color = obj.is_coasting
            ? utils::ColorFloat(1.0f, 0.0f, 0.0f, 1.0f)
            : utils::ColorFloat(0.0f, 1.0f, 0.0f, 1.0f);

        const float left = obj.x - obj.width * 0.5f;
        const float top = obj.y - obj.height * 0.5f;
        const float right = obj.x + obj.width * 0.5f;
        const float bottom = obj.y + obj.height * 0.5f;

        draw_list_->rectangle(left, top, right, bottom, 3.0f, 1.0f, color);

        const string class_name = object_classes::name(obj.class_id);
        const string label = obj.is_coasting
            ? format("{} (coasting)", class_name)
            : format("{} {:.2f}", class_name, obj.confidence);
        const wstring wide_label(label.begin(), label.end());
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


void PositionEstimation::run() {
    if (!telemetry_reader_.get_latest_telemetry(telemetry_)) {
        return;
    }

    auto object_detection_data = shared_data_.get<ObjectDetectionData>("object_detection");
    if (!object_detection_data ||
        object_detection_data->frame_index == last_object_detection_frame_index
    ) {
        this_thread::sleep_for(chrono::milliseconds(1));
        return;
    }
    last_object_detection_frame_index = object_detection_data->frame_index;

    draw_list_->clear();
    const auto camera_coords = utils::get_6th_camera_coordinate(telemetry_);

    ground_projection_.update(telemetry_);

    const uint64_t capture_qpc = object_detection_data->timestamp_qpc;
    const float capture_dt_seconds = static_cast<float>(
        telemetry_reader_.ticks_to_ms(capture_qpc - last_capture_qpc_) / 1000.0
    );
    last_capture_qpc_ = capture_qpc;

    auto objects = tracker_.update(
        object_detection_data->objects.detections,
        camera_coords,
        object_detection_data->objects.frame_width,
        object_detection_data->objects.frame_height,
        capture_dt_seconds
    );
    draw(objects);

    cv::Mat display_frame(500, 500, CV_8UC3, cv::Scalar(0, 0, 0));

    if (route_advisor_reader_.get_frame(route_advisor_capture_frame_, 1000)) {
        cv::Mat native(
            static_cast<int>(route_advisor_capture_frame_.height),
            static_cast<int>(route_advisor_capture_frame_.width),
            CV_8UC4,
            route_advisor_capture_frame_.data.data(),
            route_advisor_capture_frame_.stride
        );
        if (route_advisor_capture_frame_.layout() == ets2la_capture::PixelLayout::RGBA8) {
            cv::cvtColor(native, frame_, cv::COLOR_RGBA2BGR);
        } else {
            cv::cvtColor(native, frame_, cv::COLOR_BGRA2BGR);
        }

        utils::apply_route_advisor_crop(frame_, true);

        const cv::Mat route_advisor = utils::warp_route_advisor_to_top_down(
            frame_,
            display_frame.cols,
            display_frame.rows,
            0.1,
            {display_frame.cols / 2.0, static_cast<double>(display_frame.rows)}
        );
        if (!route_advisor.empty()) {
            cv::Mat route_advisor_mask;
            cv::inRange(
                route_advisor,
                cv::Scalar(1, 1, 1),
                cv::Scalar(255, 255, 255),
                route_advisor_mask
            );
            route_advisor.copyTo(display_frame, route_advisor_mask);
        }
    }

    PositionEstimationData position_estimation_data;
    position_estimation_data.objects.reserve(objects.size());
    position_estimation_data.frame_index = telemetry_.frame_index;
    position_estimation_data.timestamp_qpc = telemetry_.timestamp_qpc;

    for (auto& obj : objects) {
        auto position = estimate_position(
            camera_coords,
            obj,
            object_detection_data->objects.frame_width,
            object_detection_data->objects.frame_height
        );

        const bool position_valid = obj.accuracy >= 0.1f;

        position_estimation_data.objects.push_back(PositionEstimationObject{
            .tracking = obj,
            .position = position,
            .position_valid = position_valid
        });

        if (!position_valid) {
            continue;
        }

        if (object_classes::is_vehicle(obj.class_id)) {
            const cv::Point pt1 = top_down_view_point(position.left, camera_coords, display_frame.size(), 25);
            const cv::Point pt2 = top_down_view_point(position.right, camera_coords, display_frame.size(), 25);

            cv::line(
                display_frame,
                pt1,
                pt2,
                object_classes::color(obj.class_id),
                2
            );
        } else {
            const cv::Point pt = top_down_view_point(position.center, camera_coords, display_frame.size(), 25);

            cv::circle(
                display_frame,
                pt,
                2,
                object_classes::color(obj.class_id),
                -1
            );
        }
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

    try {
        cv::getWindowImageRect("Position Estimation");
    } catch (...) {
        cv::namedWindow("Position Estimation", cv::WINDOW_NORMAL);
        cv::resizeWindow("Position Estimation", display_frame.cols, display_frame.rows);
        auto target_window = utils::find_window(L"Position Estimation", {});
        utils::set_icon(target_window, L"assets/lite_icon.ico");
        utils::set_window_title_bar_color(target_window, RGB(0, 0, 0));
    }

    cv::imshow("Position Estimation", display_frame);
    cv::waitKey(1);

    auto fps = timer_.get_fps();
    printf("PositionEstimation FPS: %.2f\n", fps);
}