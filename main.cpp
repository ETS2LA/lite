#include "controller.h"
#include "telemetry.h"
#include "capture.h"
#include "utils.h"

#include <opencv2/opencv.hpp>


int main() {
    HWND target_window = utils::find_window(L"Truck Simulator", { L"Discord" });

    ScreenCapture capture(target_window);
    capture.initialize();

    cv::Mat* frame;

    cv::namedWindow("Captured Frame", cv::WINDOW_NORMAL);
    cv::resizeWindow("Captured Frame", 500, 300);

    while (true) {
        WindowRegion window_pos = capture.get_window_position();

        frame = capture.get_frame();

        if (!frame) {
            continue;
        }

        cv::imshow("Captured Frame", *frame);
        cv::waitKey(1);
    }

    return 0;
}