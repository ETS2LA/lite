#include "navigation_detection.h"

#define TURN_NONE 0
#define TURN_LEFT 1
#define TURN_RIGHT 2


using namespace std;

ScreenCapture capture(
    bind(
        utils::find_window, wstring(L"Truck Simulator"),
        vector<wstring>{ L"Discord" }
    )
);

SCSController controller;
SCSTelemetry telemetry;

static cv::Mat* temp_frame;
static cv::Mat frame;
static cv::Mat mask_red_green;
static cv::Mat mask_red;
static cv::Mat mask_green;

static cv::Scalar lower_red(0, 0, 160);
static cv::Scalar upper_red(110, 110, 255);
static cv::Scalar lower_green(0, 200, 0);
static cv::Scalar upper_green(230, 255, 150);

float last_correction = 0.0f;
bool turn_ahead_detected = false;
int turn_ahead_direction = TURN_NONE;


vector<int> get_lane_edges(const cv::Mat& frame, int y_coordinate, float tilt, int x_offset, int y_offset) {
    bool detecting_lane = false;
    vector<int> lane_edges;

    for (int x = 0; x < frame.cols; ++x) {
        int y = static_cast<int>(round(y_coordinate + y_offset + (frame.cols / 2 - x + x_offset) * tilt));
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
                lane_edges.push_back(x - x_offset);
            }
        } else {
            if (detecting_lane) {
                detecting_lane = false;
                lane_edges.push_back(x - x_offset);
            }
        }
    }

    if (lane_edges.size() < 2) {
        lane_edges.push_back(frame.cols);
    }

    return lane_edges;
}

pair<int, int> get_lane_position(const vector<int>& lane_edges) {
    int left_x_lane = 0;
    int right_x_lane = mask_red_green.cols - 1;
    if (lane_edges.size() >= 2) {
        double best_distance = numeric_limits<double>::max();
        for (size_t i = 0; i + 1 < lane_edges.size(); i += 2) {
            int left_x  = lane_edges[i];
            int right_x = lane_edges[i + 1];
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

void initialize() {
}


void run() {
    temp_frame = capture.get_frame();

    if (!temp_frame || temp_frame->empty()) {
        return;
    }
    frame = temp_frame->clone();
    TelemetryData* telemetry_data = telemetry.data();

    cv::cvtColor(frame, frame, cv::COLOR_BGRA2BGR);

    utils::apply_route_advisor_crop(frame, true);

    // remove speed limit and F5 to zoom icons
    const int inverse_roi_width = static_cast<int>(round(frame.cols / 5.7f));
    const int inverse_roi_height = static_cast<int>(round(frame.rows / 4.0f));
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

    // MARK: CHANGE
    int detection_offset_lane_y = 0;
    int x_offset = 0; // lane_change_offset
    int y_offset = detection_offset_lane_y;

    vector<int> lane_edges = get_lane_edges(mask_red_green, y_coordinate_of_lane, tilt, x_offset, y_offset);

    pair<int, int> lane_position = get_lane_position(lane_edges);
    int left_x_lane = lane_position.first;
    int right_x_lane = lane_position.second;
    int left_y_lane = static_cast<int>(round(y_coordinate_of_lane + detection_offset_lane_y + (frame.cols / 2.0f - left_x_lane - x_offset) * tilt));
    int right_y_lane = static_cast<int>(round(y_coordinate_of_lane + detection_offset_lane_y + (frame.cols / 2.0f - right_x_lane - x_offset) * tilt));
    if (right_x_lane == frame.cols - 1) {
        left_x_lane = 0;
        right_x_lane = 0;
        left_y_lane = y_coordinate_of_lane;
        right_y_lane = y_coordinate_of_lane;
    }

    vector<int> turn_edges = get_lane_edges(mask_red_green, y_coordinate_of_turn, 0.0f, x_offset, y_offset);

    pair<int, int> turn_position = get_lane_position(turn_edges);
    int left_x_turn = turn_position.first;
    int right_x_turn = turn_position.second;
    if (right_x_turn == frame.cols - 1) {
        left_x_turn = 0;
        right_x_turn = 0;
    }

    int width_lane = right_x_lane - left_x_lane;
    int width_turn = right_x_turn - left_x_turn;
    float center_x_lane = (left_x_lane + right_x_lane) / 2.0f;
    float center_x_turn = (left_x_turn + right_x_turn) / 2.0f;

    int approve_x_left = static_cast<int>(round(mask_red_green.cols * 0.25f));
    int approve_x_right = static_cast<int>(round(mask_red_green.cols * 0.75f));

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


    float correction = 0.0f;
    if (width_lane != 0) {
        if (turn_ahead_detected == false) {
            correction = frame.cols / 2.0f - center_x_lane;
        } else if (turn_ahead_direction == TURN_LEFT) {
            correction = frame.cols / 2.0f - center_x_lane - width_lane / 40.0f;
        } else if (turn_ahead_direction == TURN_RIGHT) {
            correction = frame.cols / 2.0f - center_x_lane + width_lane / 40.0f;
        }
    }

    correction = last_correction + (correction - last_correction) / 2.0f;
    last_correction = correction;

    if (telemetry_data->truck_f.speed > -0.1f) {
        controller.steering = -correction / 30.0f;
    } else {
        controller.steering = correction / 30.0f;
    }

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
        utils::set_icon(target_window, L"assets/favicon.ico");
        utils::set_window_title_bar_color(target_window, RGB(0, 0, 0));
    }

    cv::imshow("Navigation Detection", frame);
    cv::waitKey(1);
}

}