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

    cv::namedWindow("Captured Frame", cv::WINDOW_NORMAL);
    cv::resizeWindow("Captured Frame", 500, 300);

    while (true) {
        frame = capture.get_frame();

        if (!frame) {
            continue;
        }

        cv::imshow("Captured Frame", *frame);

        auto ra_frame = frame->clone();
        utils::apply_route_advisor_crop(ra_frame, false);
        cv::imshow("Route Advisor", ra_frame);

        cv::waitKey(1);
    }

    return 0;
}