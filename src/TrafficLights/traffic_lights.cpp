#include "TrafficLights/traffic_lights.h"

using namespace std;

namespace traffic_lights {


ScreenCapture* capture;

static cv::Mat frame;
static cv::Scalar lower_red(0, 0, 200, 0);
static cv::Scalar upper_red(110, 110, 255, 255);
//static cv::Scalar lower_green(0, 200, 0, 0);
//static cv::Scalar upper_green(230, 255, 150, 255);
//static cv::Scalar lower_yellow(50, 170, 200, 0);
//static cv::Scalar upper_yellow(170, 240, 255, 255);

const float width_height_ratio = 0.2f;
const float circlepercent = 0.785f;
const float maxcircleoffset = 0.15f;
const float circle_plus_offset = circlepercent + maxcircleoffset;
const float circle_minus_offset = circlepercent - maxcircleoffset;


void traffic_lights::initialize(ScreenCapture* screen_capture) {
    capture = screen_capture;
}


void traffic_lights::run() {
    FrameInfo info = capture->get_frame(frame);
    if (!info.success || frame.empty()) {
        return;
    }
    frame = frame(cv::Rect(0, 0, frame.cols, static_cast<int>(frame.rows * 0.6f)));

    int min_rect_size = frame.rows / 100;
    int max_rect_size = frame.rows / 4;


    /*
    # Python variant of traffic light detection algorithm:
    mask_red = cv2.inRange(rgb_frame, lower_red, upper_red)
    mask_green = cv2.inRange(rgb_frame, lower_green, upper_green)
    mask_yellow = cv2.inRange(rgb_frame, lower_yellow, upper_yellow)
    combined_mask = cv2.bitwise_or(mask_red, cv2.bitwise_or(mask_green, mask_yellow))
    filtered_frame_colored = cv2.bitwise_and(frame, frame, mask=combined_mask)
    filtered_frame_bw = cv2.cvtColor(filtered_frame_colored, cv2.COLOR_BGR2GRAY)
    final_frame = frame
    contours, _ = cv2.findContours(filtered_frame_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if min_rect_size < w and max_rect_size > w and min_rect_size < h and max_rect_size > h:
            if w / h - 1 < width_height_ratio * 2 and w / h - 1 > -width_height_ratio:
                red_pixel_count = cv2.countNonZero(mask_red[y:y+h, x:x+w])
                green_pixel_count = cv2.countNonZero(mask_green[y:y+h, x:x+w])
                yellow_pixel_count = cv2.countNonZero(mask_yellow[y:y+h, x:x+w])
                total_pixels = w * h
                red_ratio = red_pixel_count / total_pixels
                green_ratio = green_pixel_count / total_pixels
                yellow_ratio = yellow_pixel_count / total_pixels
                if (green_ratio < circleplusoffset and green_ratio > circleminusoffset and red_ratio < 0.1 and yellow_ratio < 0.1 or 
                    red_ratio < circleplusoffset and red_ratio > circleminusoffset and green_ratio < 0.1 and yellow_ratio < 0.1 or 
                    yellow_ratio < circleplusoffset and yellow_ratio > circleminusoffset and green_ratio < 0.1 and red_ratio < 0.1):
                    if red_ratio > green_ratio and red_ratio > yellow_ratio:
                        colorstr = "Red"
                        offset = y + h * 2
                    elif yellow_ratio > red_ratio and yellow_ratio > green_ratio:
                        colorstr = "Yellow"
                        offset = y + h * 0.5
                    elif green_ratio > red_ratio and green_ratio > yellow_ratio:
                        colorstr = "Green"
                        offset = y - h
                    else:
                        colorstr = "Red"
                        offset = y + h * 2
                    point_mask = []
                    point_mask.append((round(x + w * 0.05), round(y + h * 0.05), False))
                    point_mask.append((round(x + w * 0.5), round(y + h * 0.2), True))
                    point_mask.append((round(x + w * 0.95), round(y + h * 0.05), False))
                    point_mask.append((round(x + w * 0.3), round(y + h * 0.6), True))
                    point_mask.append((round(x + w * 0.5), round(y + h * 0.5), True))
                    point_mask.append((round(x + w * 0.7), round(y + h * 0.6), True))
                    point_mask.append((round(x + w * 0.05), round(y + h * 0.95), False))
                    point_mask.append((round(x + w * 0.5), round(y + h * 0.8), True))
                    point_mask.append((round(x + w * 0.95), round(y + h * 0.95), False))
                    as_expected = True
                    for i in range(len(point_mask)):
                        point_x, point_y, expected = point_mask[i]
                        color = filtered_frame_bw[point_y, point_x]
                        color = True if color != 0 else False
                        if color != 0 == expected:
                            as_expected = False
                            break
                    if as_expected:
                        coordinates.append((round(x + w * 0.5), round(offset), w, h, colorstr))
    */

    // C++ variant of the above Python algorithm:
    cv::Mat mask_red;
    //cv::Mat mask_green;
    //cv::Mat mask_yellow;
    cv::inRange(frame, lower_red, upper_red, mask_red);
    //cv::inRange(frame, lower_green, upper_green, mask_green);
    //cv::inRange(frame, lower_yellow, upper_yellow, mask_yellow);

    //cv::Mat combined_mask;
    //cv::bitwise_or(mask_red, mask_green, combined_mask);
    //cv::bitwise_or(combined_mask, mask_yellow, combined_mask);

    cv::Mat filtered_frame_colored;
    cv::bitwise_and(frame, frame, filtered_frame_colored, mask_red);

    cv::Mat filtered_frame_bw;
    cv::cvtColor(filtered_frame_colored, filtered_frame_bw, cv::COLOR_BGR2GRAY);

    vector<vector<cv::Point>> contours;
    cv::findContours(filtered_frame_bw.clone(), contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

    for (const auto& contour : contours) {
        cv::Rect rect = cv::boundingRect(contour);
        int x = rect.x;
        int y = rect.y;
        int w = rect.width;
        int h = rect.height;

        if (w > min_rect_size && w < max_rect_size && h > min_rect_size && h < max_rect_size) {
            float wh_ratio = static_cast<float>(w) / static_cast<float>(h) - 1.0f;
            if (wh_ratio < width_height_ratio * 2.0f && wh_ratio > -width_height_ratio) {
                int red_pixel_count = cv::countNonZero(mask_red(rect));
                //int green_pixel_count = cv::countNonZero(mask_green(rect));
                //int yellow_pixel_count = cv::countNonZero(mask_yellow(rect));

                float total_pixels = static_cast<float>(w * h);
                float red_ratio = static_cast<float>(red_pixel_count) / total_pixels;
                //float green_ratio = static_cast<float>(green_pixel_count) / total_pixels;
                //float yellow_ratio = static_cast<float>(yellow_pixel_count) / total_pixels;

                bool matches_circle_density = (
                    //(green_ratio < circle_plus_offset && green_ratio > circle_minus_offset && red_ratio < 0.1f && yellow_ratio < 0.1f) ||
                    (red_ratio < circle_plus_offset && red_ratio > circle_minus_offset) //) && green_ratio < 0.1f && yellow_ratio < 0.1f) ||
                    //(yellow_ratio < circle_plus_offset && yellow_ratio > circle_minus_offset && green_ratio < 0.1f && red_ratio < 0.1f)
                );

                if (matches_circle_density) {
                    int state = TRAFFIC_LIGHT_RED;
                    float offset = static_cast<float>(y) + static_cast<float>(h) * 2.0f;

                    //if (yellow_ratio > red_ratio && yellow_ratio > green_ratio) {
                    //    state = TRAFFIC_LIGHT_YELLOW;
                    //    offset = static_cast<float>(y) + static_cast<float>(h) * 0.5f;
                    //} else if (green_ratio > red_ratio && green_ratio > yellow_ratio) {
                    //    state = TRAFFIC_LIGHT_GREEN;
                    //    offset = static_cast<float>(y) - static_cast<float>(h);
                    //}

                    vector<tuple<int, int, bool>> point_mask = {
                        {cvRound(x + w * 0.05f), cvRound(y + h * 0.05f), false},
                        {cvRound(x + w * 0.5f), cvRound(y + h * 0.2f), true},
                        {cvRound(x + w * 0.95f), cvRound(y + h * 0.05f), false},
                        {cvRound(x + w * 0.3f), cvRound(y + h * 0.6f), true},
                        {cvRound(x + w * 0.5f), cvRound(y + h * 0.5f), true},
                        {cvRound(x + w * 0.7f), cvRound(y + h * 0.6f), true},
                        {cvRound(x + w * 0.05f), cvRound(y + h * 0.95f), false},
                        {cvRound(x + w * 0.5f), cvRound(y + h * 0.8f), true},
                        {cvRound(x + w * 0.95f), cvRound(y + h * 0.95f), false}
                    };

                    bool as_expected = true;
                    for (const auto& point : point_mask) {
                        int point_x = get<0>(point);
                        int point_y = get<1>(point);
                        bool expected = get<2>(point);

                        if (point_x < 0 || point_x >= filtered_frame_bw.cols || point_y < 0 || point_y >= filtered_frame_bw.rows) {
                            as_expected = false;
                            break;
                        }

                        bool color_present = filtered_frame_bw.at<uchar>(point_y, point_x) != 0;
                        if (color_present != expected) {
                            as_expected = false;
                            break;
                        }
                    }

                    if (as_expected) {
                        int center_x = cvRound(x + w * 0.5f);
                        int center_y = cvRound(offset);
                        center_y = max(0, min(center_y, frame.rows - 1));

                        cv::rectangle(
                            frame,
                            rect,
                            state == TRAFFIC_LIGHT_GREEN ?
                            cv::Scalar(0, 255, 0) : (state == TRAFFIC_LIGHT_YELLOW ?
                            cv::Scalar(0, 255, 255) : cv::Scalar(0, 0, 255)),
                            3
                        );
                    }
                }
            }
        }
    }


    try {
        cv::getWindowImageRect("Traffic Lights");
    } catch (...) {
        cv::namedWindow("Traffic Lights", cv::WINDOW_NORMAL);
        cv::resizeWindow("Traffic Lights", frame.cols, frame.rows);
        cv::setWindowProperty("Traffic Lights", cv::WND_PROP_TOPMOST, 1);
        auto target_window = utils::find_window(L"Traffic Lights", {});
        utils::set_icon(target_window, L"assets/lite_icon.ico");
        utils::set_window_title_bar_color(target_window, RGB(0, 0, 0));
    }
    cv::imshow("Traffic Lights", frame);
    cv::waitKey(1);
}

}