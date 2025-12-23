#include "controller.h"
#include "telemetry.h"
#include "capture.h"
#include "utils.h"

#include <opencv2/opencv.hpp>


int main() {
    ScreenCapture capture(
        std::bind(
            utils::find_window, std::wstring(L"Truck Simulator"),
            std::vector<std::wstring>{ L"Discord" }
        )
    );

    cv::Mat* frame;
    cv::Mat combined;
    cv::Mat mask_red, mask_green;

    cv::Scalar lower_red(0, 0, 160);
    cv::Scalar upper_red(110, 110, 255);
    cv::Scalar lower_green(0, 200, 0);
    cv::Scalar upper_green(230, 255, 150);

    cv::namedWindow("Frame", cv::WINDOW_NORMAL);
    cv::resizeWindow("Frame", 420, 219);

    while (true) {
        frame = capture.get_frame();

        if (!frame) {
            continue;
        }

        cv::cvtColor(*frame, *frame, cv::COLOR_BGRA2BGR);

        utils::apply_route_advisor_crop(*frame, true);

        mask_red = cv::Mat::zeros(frame->size(), CV_8U);
        mask_green = cv::Mat::zeros(frame->size(), CV_8U);

        cv::inRange(*frame, lower_red, upper_red, mask_red);
        cv::inRange(*frame, lower_green, upper_green, mask_green);
        cv::bitwise_or(mask_red, mask_green, combined);

        cv::rectangle(
            combined,
            cv::Point(0, 0),
            cv::Point(
                static_cast<int>(std::round(combined.cols/5.7f)),
                static_cast<int>(std::round(combined.rows/4.0f))
            ),
            cv::Scalar(0),
            -1
        );
        cv::rectangle(
            combined,
            cv::Point(combined.cols - 1, 0),
            cv::Point(
                static_cast<int>(std::round(combined.cols - 1 - combined.cols/5.7f)),
                static_cast<int>(std::round(combined.rows/4.0f))
            ),
            cv::Scalar(0),
            -1
        );

        cv::imshow("Frame", combined);
        cv::waitKey(1);
    }

    return 0;
}