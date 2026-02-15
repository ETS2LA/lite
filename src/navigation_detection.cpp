#include "navigation_detection.h"

#define TURN_NONE 0
#define TURN_LEFT 1
#define TURN_RIGHT 2


using namespace std;

ScreenCapture* capture;
SCSController controller;
SCSTelemetry telemetry;
InputHandler input_handler;

static cv::Mat frame;
static cv::Mat mask_red_green;
static cv::Mat mask_red;
static cv::Mat mask_green;

static cv::Scalar lower_red(0, 0, 160, 0);
static cv::Scalar upper_red(110, 110, 255, 255);
static cv::Scalar lower_green(0, 200, 0, 0);
static cv::Scalar upper_green(230, 255, 150, 255);

bool control_enabled = true;
float last_correction = 0.0f;
int detection_offset_lane_y = 0;

int lane_change_current_lane = 0;
float lane_change_target_offset = 0.0f;
float lane_change_offset = 0.0f;
float lane_change_progress = 0.0f;
double lane_change_start_time = 0.0;
float lane_change_start_offset = 0.0f;

bool turn_ahead_detected = false;
float last_turn_ahead_detected = 0.0f;
int turn_ahead_direction = TURN_NONE;

bool indicator_left = false;
bool indicator_right = false;
bool last_indicator_left = false;
bool last_indicator_right = false;
bool indicator_left_wait_for_response = false;
bool indicator_right_wait_for_response = false;
double indicator_left_response_timer = 0.0;
double indicator_right_response_timer = 0.0;


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

pair<float, float> get_lane_position(const vector<int>& lane_edges, int y_coordinate) {
    float left_x_lane = 0.0f;
    float right_x_lane = static_cast<float>(mask_red_green.cols - 1);
    if (lane_edges.size() >= 2) {
        float best_distance = numeric_limits<float>::max();
        for (size_t i = 0; i + 1 < lane_edges.size(); i += 2) {
            float left_x  = static_cast<float>(lane_edges[i]) - get_pixel_average(mask_red_green, lane_edges[i], y_coordinate);
            float right_x = static_cast<float>(lane_edges[i + 1]) + get_pixel_average(mask_red_green, lane_edges[i + 1], y_coordinate);
            float center = (left_x + right_x) / 2.0f;
            float distance = abs(center - static_cast<float>(frame.cols - 1) / 2.0f);

            if (distance < best_distance) {
                best_distance = distance;
                left_x_lane = left_x;
                right_x_lane = right_x;
            }
        }
    }

    return {left_x_lane, right_x_lane};
}


namespace navigation_detection {

void initialize(ScreenCapture* screen_capture) {
    capture = screen_capture;
    controller.gamepad_mode = true;

    input_handler.register_key_binding(
        KeyBinding{
            "x",
            []() {
                control_enabled = !control_enabled;
                utils::set_window_outline_color(
                    utils::find_window(L"Navigation Detection", {}),
                    control_enabled ? RGB(0, 255, 0) : RGB(255, 0, 0)
                );
                controller.enabled(control_enabled);
            }
        }
    );
}


void run() {
    double current_time = utils::get_time_seconds();

    FrameInfo info = capture->get_frame(frame);
    if (!info.success || frame.empty()) {
        return;
    }

    TelemetryData* telemetry_data = telemetry.data();

    indicator_left = telemetry_data->truck_b.blinkerLeftActive;
    indicator_right = telemetry_data->truck_b.blinkerRightActive;

    utils::apply_route_advisor_crop(frame, true);

    // remove speed limit icon
    const int inverse_roi_width = static_cast<int>(round(frame.cols / 7.8f));
    const int inverse_roi_height = static_cast<int>(round(frame.rows / 3.95f));
    frame(cv::Rect(0, 0, inverse_roi_width, inverse_roi_height)).setTo(cv::Scalar(0));
    frame(cv::Rect(frame.cols - inverse_roi_width, 0, inverse_roi_width, inverse_roi_height)).setTo(cv::Scalar(0));

    cv::inRange(frame, lower_red, upper_red, mask_red);
    cv::inRange(frame, lower_green, upper_green, mask_green);
    cv::bitwise_or(mask_red, mask_green, mask_red_green);

    // set the inverse of the mask to black and the mask to gray on the original frame
    frame.setTo(cv::Scalar(0,0,0), ~mask_red_green);
    frame.setTo(cv::Scalar(128, 128, 128), mask_red_green);

    int y_coordinate_of_lane = static_cast<int>(round(mask_red_green.rows/2.5f));
    int y_coordinate_of_turn = static_cast<int>(round(mask_red_green.rows/6.0f));

    float tilt = 0.0f;
    if (turn_ahead_direction == TURN_LEFT) {
        tilt = 0.25f;
    } else if (turn_ahead_direction == TURN_RIGHT) {
        tilt = -0.25f;
    }

    vector<int> lane_edges = get_lane_edges(mask_red_green, y_coordinate_of_lane, tilt, detection_offset_lane_y);

    pair<float, float> lane_position = get_lane_position(lane_edges, y_coordinate_of_lane);
    float left_x_lane = lane_position.first;
    float right_x_lane = lane_position.second;
    float left_y_lane = round(y_coordinate_of_lane + detection_offset_lane_y + (frame.cols / 2.0f - left_x_lane) * tilt);
    float right_y_lane = round(y_coordinate_of_lane + detection_offset_lane_y + (frame.cols / 2.0f - right_x_lane) * tilt);
    if (right_x_lane == frame.cols - 1) {
        left_x_lane = 0.0f;
        right_x_lane = 0.0f;
        left_y_lane = y_coordinate_of_lane;
        right_y_lane = y_coordinate_of_lane;
    }

    vector<int> turn_edges = get_lane_edges(mask_red_green, y_coordinate_of_turn, 0.0f, detection_offset_lane_y);

    pair<float, float> turn_position = get_lane_position(turn_edges, y_coordinate_of_turn);
    float left_x_turn = turn_position.first;
    float right_x_turn = turn_position.second;
    if (right_x_turn == frame.cols - 1) {
        left_x_turn = 0;
        right_x_turn = 0;
    }

    float width_lane = right_x_lane - left_x_lane;
    float width_turn = right_x_turn - left_x_turn;
    float center_x_lane = (left_x_lane + right_x_lane) / 2.0f;
    float center_x_turn = (left_x_turn + right_x_turn) / 2.0f;

    int approve_x_left = static_cast<int>(round(mask_red_green.cols * 0.155f));
    int approve_x_right = static_cast<int>(round(mask_red_green.cols * 0.845f));

    int approve_upper_y_left = 0;
    int approve_lower_y_left = 0;
    for (int y = mask_red_green.rows - 1; y >= 0; --y) {
        if (mask_red_green.at<uint8_t>(y, approve_x_left) >= 128) {
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
    for (int y = mask_red_green.rows - 1; y >= 0; --y) {
        if (mask_red_green.at<uint8_t>(y, approve_x_right) >= 128) {
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
                detection_offset_lane_y = distance;
            } else {
                detection_offset_lane_y = 0;
            }
        } else {
            detection_offset_lane_y = 0;
        }
    } else {
        detection_offset_lane_y = 0;
    }

    if (width_turn == 0) {
        if (approve_upper_y_left != 0) {
            turn_ahead_detected = true;
            turn_ahead_direction = TURN_LEFT;
        }
        if (approve_upper_y_right != 0) {
            turn_ahead_detected = true;
            turn_ahead_direction = TURN_RIGHT;
        }
    } else {
        turn_ahead_detected = false;
        turn_ahead_direction = TURN_NONE;
    }

    if (approve_upper_y_left != 0 && approve_upper_y_right != 0) {
        turn_ahead_detected = false;
        turn_ahead_direction = TURN_NONE;
    }

    if (approve_upper_y_left == 0 && approve_upper_y_right == 0) {
        turn_ahead_detected = false;
        turn_ahead_direction = TURN_NONE;
    }

    if (turn_ahead_detected) {
        last_turn_ahead_detected = current_time;
        lane_change_current_lane = 0;
        lane_change_start_time = current_time;
        lane_change_start_offset = lane_change_offset;
    }

    bool indicator_changed_by_code = turn_ahead_detected;

    if (indicator_left != last_indicator_left) {
        indicator_left_wait_for_response = false;
    }
    if (indicator_right != last_indicator_right) {
        indicator_right_wait_for_response = false;
    }

    if (current_time - 1 > indicator_left_response_timer) {
        indicator_left_wait_for_response = false;
    }
    if (current_time - 1 > indicator_right_response_timer) {
        indicator_right_wait_for_response = false;
    }

    if (indicator_left && indicator_left != last_indicator_left && !indicator_changed_by_code && current_time - 1 > last_turn_ahead_detected) {
        lane_change_current_lane += 1;
        lane_change_start_time = current_time;
        lane_change_start_offset = lane_change_offset;
    }
    if (indicator_right && indicator_right != last_indicator_right && !indicator_changed_by_code && current_time - 1 > last_turn_ahead_detected) {
        lane_change_current_lane -= 1;
        lane_change_start_time = current_time;
        lane_change_start_offset = lane_change_offset;
    }

    lane_change_target_offset = static_cast<float>(frame.cols / 31.0f) * static_cast<float>(lane_change_current_lane);
    lane_change_progress = static_cast<float>(clamp((current_time - lane_change_start_time) / 3.0, 0.0, 1.0));
    lane_change_offset = lane_change_start_offset + (lane_change_target_offset - lane_change_start_offset) * lane_change_progress;


    float correction = 0.0f;
    if (width_lane != 0) {
        if (turn_ahead_detected == false) {
            correction = frame.cols / 2.0f - center_x_lane;
        } else if (turn_ahead_direction == TURN_LEFT) {
            correction = frame.cols / 2.0f - center_x_lane - width_lane / 40.0f;
        } else if (turn_ahead_direction == TURN_RIGHT) {
            correction = frame.cols / 2.0f - center_x_lane + width_lane / 40.0f;
        }
        correction += lane_change_offset;
    }


    // check for input updates
    input_handler.update();

    if (control_enabled) {
        correction = last_correction + (correction - last_correction) / 1.5f;
        last_correction = correction;

        if (telemetry_data->truck_f.speed > -0.1f) {
            controller.steering = -correction / 30.0f;
        } else {
            controller.steering = correction / 30.0f;
        }

        // handle indicators for turns
        if (turn_ahead_direction == TURN_LEFT && !indicator_left && !indicator_left_wait_for_response) {
            controller.lblinker = true;
            indicator_left_wait_for_response = true;
            indicator_left_response_timer = current_time;
        }
        if (turn_ahead_direction == TURN_RIGHT && !indicator_right && !indicator_right_wait_for_response) {
            controller.rblinker = true;
            indicator_right_wait_for_response = true;
            indicator_right_response_timer = current_time;
        }

        // handle indicators for lane changes
        if (lane_change_progress == 1.0f && indicator_left && !indicator_left_wait_for_response && !indicator_changed_by_code) {
            controller.lblinker = true;
            indicator_left_wait_for_response = true;
            indicator_left_response_timer = current_time;
        }
        if (lane_change_progress == 1.0f && indicator_right && !indicator_right_wait_for_response && !indicator_changed_by_code) {
            controller.rblinker = true;
            indicator_right_wait_for_response = true;
            indicator_right_response_timer = current_time;
        }
    } else {
        last_correction = 0.0f;
        controller.steering = 0.0f;
    }


    last_indicator_left = indicator_left;
    last_indicator_right = indicator_right;

    // send controller updates to game
    controller.update();


    if (width_lane != 0) {
        cv::line(
            frame,
            cv::Point(left_x_lane, left_y_lane),
            cv::Point(right_x_lane, right_y_lane),
            cv::Scalar(0, 255, 0),
            2
        );
    }

    if (width_turn != 0) {
        cv::line(
            frame,
            cv::Point(left_x_turn, y_coordinate_of_turn),
            cv::Point(right_x_turn, y_coordinate_of_turn),
            cv::Scalar(255, 255, 255),
            2
        );
    }

    if (approve_lower_y_left != 0) {
        cv::rectangle(
            frame,
            cv::Point(approve_x_left, approve_upper_y_left),
            cv::Point(approve_x_left, approve_lower_y_left),
            turn_ahead_direction == TURN_LEFT ? cv::Scalar(0, 255, 0) : cv::Scalar(255, 255, 255),
            2
        );
    }

    if (approve_lower_y_right != 0) {
        cv::rectangle(
            frame,
            cv::Point(approve_x_right, approve_upper_y_right),
            cv::Point(approve_x_right, approve_lower_y_right),
            turn_ahead_direction == TURN_RIGHT ? cv::Scalar(0, 255, 0) : cv::Scalar(255, 255, 255),
            2
        );
    }


    try {
        cv::getWindowImageRect("Navigation Detection");
    } catch (...) {
        cv::namedWindow("Navigation Detection", cv::WINDOW_NORMAL);
        cv::resizeWindow("Navigation Detection", frame.cols, frame.rows);
        cv::setWindowProperty("Navigation Detection", cv::WND_PROP_TOPMOST, 1);
        auto target_window = utils::find_window(L"Navigation Detection", {});
        utils::set_icon(target_window, L"assets/lite_icon.ico");
        utils::set_window_title_bar_color(target_window, RGB(0, 0, 0));
        utils::set_window_outline_color(target_window, control_enabled ? RGB(0, 255, 0) : RGB(255, 0, 0));
    }

    cv::imshow("Navigation Detection", frame);
    cv::waitKey(1);
}

}