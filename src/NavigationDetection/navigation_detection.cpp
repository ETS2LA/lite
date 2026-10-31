#include "navigation_detection.h"
#include "shared_data.h"

using namespace std;


float get_pixel_average(const cv::Mat& frame, int x, int y) {
    int x_left = max(0, x - 1);
    int x_right = min(frame.cols - 1, x + 1);
    int y_above = max(0, y - 1);
    int y_below = min(frame.rows - 1, y + 1);

    float value = 0.0f;
    value += static_cast<float>(frame.at<uint8_t>(y, x));
    value += static_cast<float>(frame.at<uint8_t>(y_above, x_left));
    value += static_cast<float>(frame.at<uint8_t>(y_above, x));
    value += static_cast<float>(frame.at<uint8_t>(y_above, x_right));
    value += static_cast<float>(frame.at<uint8_t>(y_below, x_left));
    value += static_cast<float>(frame.at<uint8_t>(y_below, x));
    value += static_cast<float>(frame.at<uint8_t>(y_below, x_right));

    return value / (7.0f * 255.0f);
}

vector<int> get_lane_edges(const cv::Mat& frame, int y_coordinate, float tilt, int y_offset) {
    bool detecting_lane = false;
    vector<int> lane_edges;

    for (int x = 0; x < frame.cols; ++x) {
        int y = static_cast<int>(round(y_coordinate + y_offset + (frame.cols / 2 - x) * tilt));
        if (y < 0) {
            y = 0;
        }
        if (y > frame.rows - 1) {
            y = frame.rows - 1;
        }

        uint8_t pixel = frame.at<uint8_t>(y, x);
        if (pixel > 0) {
            if (!detecting_lane) {
                detecting_lane = true;
                lane_edges.push_back(x);
            }
        } else {
            if (detecting_lane) {
                detecting_lane = false;
                lane_edges.push_back(x);
            }
        }
    }

    if (lane_edges.size() < 2) {
        lane_edges.push_back(frame.cols);
    }

    return lane_edges;
}

pair<float, float> NavigationDetection::get_lane_position(const vector<int>& lane_edges, int y_coordinate) {
    float left_x_lane = 0.0f;
    float right_x_lane = static_cast<float>(mask_red_green_.cols - 1);
    if (lane_edges.size() >= 2) {
        float best_distance = numeric_limits<float>::max();
        for (size_t i = 0; i + 1 < lane_edges.size(); i += 2) {
            float left_x  = static_cast<float>(lane_edges[i]) - get_pixel_average(mask_red_green_, lane_edges[i], y_coordinate);
            float right_x = static_cast<float>(lane_edges[i + 1]) + get_pixel_average(mask_red_green_, lane_edges[i + 1], y_coordinate);
            float center = (left_x + right_x) / 2.0f;
            float distance = abs(center - static_cast<float>(frame_.cols - 1) / 2.0f);

            if (distance < best_distance) {
                best_distance = distance;
                left_x_lane = left_x;
                right_x_lane = right_x;
            }
        }
    }

    return {left_x_lane, right_x_lane};
}


NavigationDetection::NavigationDetection(SharedData& shared_data, AR *ar):
shared_data_(shared_data)
{
    draw_list_ = ar->get_draw_list("navigation_detection");
    controller_.gamepad_mode = true;

    input_.register_key_binding(
        KeyBinding{
            "x",
            [this]() {
                control_enabled_ = !control_enabled_;
                utils::set_window_outline_color(
                    utils::find_window(L"Navigation Detection", {}),
                    control_enabled_ ? RGB(0, 255, 0) : RGB(255, 0, 0)
                );
                controller_.enabled(control_enabled_);
            }
        }
    );
}


void NavigationDetection::update() {
    double current_time = utils::get_time_seconds();

    if (!reader_.get_frame(capture_frame_, 1000)) {
        return;
    }

    cv::Mat native(int(capture_frame_.height), int(capture_frame_.width), CV_8UC4, capture_frame_.data.data(), capture_frame_.stride);
    if (capture_frame_.layout() == ets2la_capture::PixelLayout::RGBA8) {
        cv::cvtColor(native, frame_, cv::COLOR_RGBA2BGR);
    } else {
        cv::cvtColor(native, frame_, cv::COLOR_BGRA2BGR);
    }

    if (!telemetry_reader_.get_latest_telemetry(telemetry_)) {
        return;
    }

    indicator_left_ = telemetry_.truck.left_blinker;
    indicator_right_ = telemetry_.truck.right_blinker;

    utils::apply_route_advisor_crop(frame_, true);

    // remove speed limit icon
    const int inverse_roi_width = static_cast<int>(round(frame_.cols / 7.8f));
    const int inverse_roi_height = static_cast<int>(round(frame_.rows / 3.95f));
    frame_(cv::Rect(0, 0, inverse_roi_width, inverse_roi_height)).setTo(cv::Scalar(0));
    frame_(cv::Rect(frame_.cols - inverse_roi_width, 0, inverse_roi_width, inverse_roi_height)).setTo(cv::Scalar(0));

    cv::inRange(frame_, lower_red_, upper_red_, mask_red_);
    cv::inRange(frame_, lower_green_, upper_green_, mask_green_);
    cv::bitwise_or(mask_red_, mask_green_, mask_red_green_);

    // set the inverse of the mask to black and the mask to gray on the original frame
    frame_.setTo(cv::Scalar(0,0,0), ~mask_red_green_);
    frame_.setTo(cv::Scalar(128, 128, 128), mask_red_green_);

    int y_coordinate_of_lane = static_cast<int>(round(mask_red_green_.rows/2.5f));
    int y_coordinate_of_turn = static_cast<int>(round(mask_red_green_.rows/6.0f));

    float tilt = 0.0f;
    if (turn_ahead_direction_ == TURN_LEFT) {
        tilt = 0.25f;
    } else if (turn_ahead_direction_ == TURN_RIGHT) {
        tilt = -0.25f;
    }

    vector<int> lane_edges = get_lane_edges(mask_red_green_, y_coordinate_of_lane, tilt, detection_offset_lane_y_);

    pair<float, float> lane_position = get_lane_position(lane_edges, y_coordinate_of_lane);
    float left_x_lane = lane_position.first;
    float right_x_lane = lane_position.second;
    float left_y_lane = round(y_coordinate_of_lane + detection_offset_lane_y_ + (frame_.cols / 2.0f - left_x_lane) * tilt);
    float right_y_lane = round(y_coordinate_of_lane + detection_offset_lane_y_ + (frame_.cols / 2.0f - right_x_lane) * tilt);
    if (right_x_lane == frame_.cols - 1) {
        left_x_lane = 0.0f;
        right_x_lane = 0.0f;
        left_y_lane = y_coordinate_of_lane;
        right_y_lane = y_coordinate_of_lane;
    }

    vector<int> turn_edges = get_lane_edges(mask_red_green_, y_coordinate_of_turn, 0.0f, detection_offset_lane_y_);

    pair<float, float> turn_position = get_lane_position(turn_edges, y_coordinate_of_turn);
    float left_x_turn = turn_position.first;
    float right_x_turn = turn_position.second;
    if (right_x_turn == frame_.cols - 1) {
        left_x_turn = 0;
        right_x_turn = 0;
    }

    float width_lane = right_x_lane - left_x_lane;
    float width_turn = right_x_turn - left_x_turn;
    float center_x_lane = (left_x_lane + right_x_lane) / 2.0f;
    float center_x_turn = (left_x_turn + right_x_turn) / 2.0f;

    int approve_x_left = static_cast<int>(round(mask_red_green_.cols * 0.155f));
    int approve_x_right = static_cast<int>(round(mask_red_green_.cols * 0.845f));

    int approve_upper_y_left = 0;
    int approve_lower_y_left = 0;
    for (int y = mask_red_green_.rows - 1; y >= 0; --y) {
        if (mask_red_green_.at<uint8_t>(y, approve_x_left) >= 128) {
            if (approve_upper_y_left == 0) {
                approve_upper_y_left = y;
                approve_lower_y_left = y;
            } else {
                approve_lower_y_left = y;
            }
        } else {
            if (approve_upper_y_left != 0) {
                break;
            }
        }
    }

    int approve_upper_y_right = 0;
    int approve_lower_y_right = 0;
    for (int y = mask_red_green_.rows - 1; y >= 0; --y) {
        if (mask_red_green_.at<uint8_t>(y, approve_x_right) >= 128) {
            if (approve_upper_y_right == 0) {
                approve_upper_y_right = y;
                approve_lower_y_right = y;
            } else {
                approve_lower_y_right = y;
            }
        } else {
            if (approve_upper_y_right != 0) {
                break;
            }
        }
    }

    if (approve_upper_y_left != 0 && approve_upper_y_right != 0) {
        if (
            (y_coordinate_of_lane >= approve_lower_y_left + (approve_lower_y_left - approve_upper_y_left) &&
             y_coordinate_of_lane <= approve_upper_y_left - (approve_lower_y_left - approve_upper_y_left))
            ||
            (y_coordinate_of_lane >= approve_lower_y_right + (approve_lower_y_right - approve_upper_y_right) &&
             y_coordinate_of_lane <= approve_upper_y_right - (approve_lower_y_right - approve_upper_y_right))
        ) {
            int distance = min(approve_lower_y_left, approve_lower_y_right) - y_coordinate_of_lane;
            if (distance < 0) {
                detection_offset_lane_y_ = distance;
            } else {
                detection_offset_lane_y_ = 0;
            }
        } else {
            detection_offset_lane_y_ = 0;
        }
    } else {
        detection_offset_lane_y_ = 0;
    }

    if (width_turn == 0) {
        if (approve_upper_y_left != 0) {
            turn_ahead_detected_ = true;
            turn_ahead_direction_ = TURN_LEFT;
        }
        if (approve_upper_y_right != 0) {
            turn_ahead_detected_ = true;
            turn_ahead_direction_ = TURN_RIGHT;
        }
    } else {
        turn_ahead_detected_ = false;
        turn_ahead_direction_ = TURN_NONE;
    }

    if (approve_upper_y_left != 0 && approve_upper_y_right != 0) {
        turn_ahead_detected_ = false;
        turn_ahead_direction_ = TURN_NONE;
    }

    if (approve_upper_y_left == 0 && approve_upper_y_right == 0) {
        turn_ahead_detected_ = false;
        turn_ahead_direction_ = TURN_NONE;
    }

    if (turn_ahead_detected_) {
        last_turn_ahead_detected_ = current_time;
        lane_change_current_lane_ = 0;
        lane_change_start_time_ = current_time;
        lane_change_start_offset_ = lane_change_offset_;
    }

    bool indicator_changed_by_code = turn_ahead_detected_;

    if (indicator_left_ != last_indicator_left_) {
        indicator_left_wait_for_response_ = false;
    }
    if (indicator_right_ != last_indicator_right_) {
        indicator_right_wait_for_response_ = false;
    }

    if (current_time - 1 > indicator_left_response_timer_) {
        indicator_left_wait_for_response_ = false;
    }
    if (current_time - 1 > indicator_right_response_timer_) {
        indicator_right_wait_for_response_ = false;
    }

    if (indicator_left_ && indicator_left_ != last_indicator_left_ && !indicator_changed_by_code && current_time - 1 > last_turn_ahead_detected_) {
        lane_change_current_lane_ += 1;
        lane_change_start_time_ = current_time;
        lane_change_start_offset_ = lane_change_offset_;
    }
    if (indicator_right_ && indicator_right_ != last_indicator_right_ && !indicator_changed_by_code && current_time - 1 > last_turn_ahead_detected_) {
        lane_change_current_lane_ -= 1;
        lane_change_start_time_ = current_time;
        lane_change_start_offset_ = lane_change_offset_;
    }

    lane_change_progress_ = static_cast<float>(clamp((current_time - lane_change_start_time_) / 3.0, 0.0, 1.0));
    lane_change_target_offset_ = static_cast<float>(frame_.cols / 24.5f) * static_cast<float>(lane_change_current_lane_);
    lane_change_offset_ = lane_change_start_offset_ + (lane_change_target_offset_ - lane_change_start_offset_) * lane_change_progress_;


    float correction = 0.0f;
    if (width_lane != 0) {
        correction = (frame_.cols / 2.0f - center_x_lane) / frame_.cols * 7.0f;
        if (turn_ahead_direction_ == TURN_LEFT) {
            correction -= width_lane / 1200.0f;
        } else if (turn_ahead_direction_ == TURN_RIGHT) {
            correction += width_lane / 1200.0f;
        }
        correction += lane_change_offset_ / frame_.cols * 7.0f;
    }


    // check for input updates
    input_.update();

    if (control_enabled_) {
        correction = last_correction_ + (correction - last_correction_) / 1.5f;
        last_correction_ = correction;

        if (telemetry_.truck.speed > -0.1f) {
            controller_.steering = -correction;
        } else {
            controller_.steering = correction;
        }

        // handle indicators for turns
        if (turn_ahead_direction_ == TURN_LEFT && !indicator_left_ && !indicator_left_wait_for_response_) {
            controller_.set(ets2la_controller::Button::blinker_left, true);
            indicator_left_wait_for_response_ = true;
            indicator_left_response_timer_ = current_time;
        }
        if (turn_ahead_direction_ == TURN_RIGHT && !indicator_right_ && !indicator_right_wait_for_response_) {
            controller_.set(ets2la_controller::Button::blinker_right, true);
            indicator_right_wait_for_response_ = true;
            indicator_right_response_timer_ = current_time;
        }

        // handle indicators for lane changes
        if (lane_change_progress_ == 1.0f && indicator_left_ && !indicator_left_wait_for_response_ && !indicator_changed_by_code) {
            controller_.set(ets2la_controller::Button::blinker_left, true);
            indicator_left_wait_for_response_ = true;
            indicator_left_response_timer_ = current_time;
        }
        if (lane_change_progress_ == 1.0f && indicator_right_ && !indicator_right_wait_for_response_ && !indicator_changed_by_code) {
            controller_.set(ets2la_controller::Button::blinker_right, true);
            indicator_right_wait_for_response_ = true;
            indicator_right_response_timer_ = current_time;
        }
    } else {
        last_correction_ = 0.0f;
        controller_.steering = 0.0f;
    }


    last_indicator_left_ = indicator_left_;
    last_indicator_right_ = indicator_right_;

    // send controller updates to game
    controller_.update();

    NavigationDetectionData navigation_detection_data{
        .turn = turn_ahead_direction_
    };
    shared_data_.set("navigation_detection", navigation_detection_data);


    if (width_lane != 0) {
        cv::line(
            frame_,
            cv::Point(left_x_lane, left_y_lane),
            cv::Point(right_x_lane, right_y_lane),
            cv::Scalar(0, 255, 0),
            2
        );
    }

    if (width_turn != 0) {
        cv::line(
            frame_,
            cv::Point(left_x_turn, y_coordinate_of_turn),
            cv::Point(right_x_turn, y_coordinate_of_turn),
            cv::Scalar(255, 255, 255),
            2
        );
    }

    if (approve_lower_y_left != 0) {
        cv::rectangle(
            frame_,
            cv::Point(approve_x_left, approve_upper_y_left),
            cv::Point(approve_x_left, approve_lower_y_left),
            turn_ahead_direction_ == TURN_LEFT ? cv::Scalar(0, 255, 0) : cv::Scalar(255, 255, 255),
            2
        );
    }

    if (approve_lower_y_right != 0) {
        cv::rectangle(
            frame_,
            cv::Point(approve_x_right, approve_upper_y_right),
            cv::Point(approve_x_right, approve_lower_y_right),
            turn_ahead_direction_ == TURN_RIGHT ? cv::Scalar(0, 255, 0) : cv::Scalar(255, 255, 255),
            2
        );
    }


    try {
        cv::getWindowImageRect("Navigation Detection");
    } catch (...) {
        cv::namedWindow("Navigation Detection", cv::WINDOW_NORMAL);
        cv::resizeWindow("Navigation Detection", frame_.cols, frame_.rows);
        cv::setWindowProperty("Navigation Detection", cv::WND_PROP_TOPMOST, 1);
        auto target_window = utils::find_window(L"Navigation Detection", {});
        utils::set_icon(target_window, L"assets/lite_icon.ico");
        utils::set_window_title_bar_color(target_window, RGB(0, 0, 0));
        utils::set_window_outline_color(target_window, control_enabled_ ? RGB(0, 255, 0) : RGB(255, 0, 0));
    }

    cv::imshow("Navigation Detection", frame_);
    cv::waitKey(1);
}