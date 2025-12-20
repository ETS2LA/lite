#include "controller.h"
#include "telemetry.h"
#include "capture.h"

#include <opencv2/opencv.hpp>


int main() {
    WindowCapture capture;
    capture.initialize();

    cv::Mat* frame;

    while (true) {
        frame = capture.get_frame();
        if (!frame) {
            continue;
        }
        cv::imshow("Captured Frame", *frame);
        cv::waitKey(1);
    }

    return 0;
}