#include "controller.h"
#include "telemetry.h"
#include "capture.h"
#include "utils.h"

#include "navigation_detection.h"



int main() {
    navigation_detection::initialize();

    while (true) {
        auto start = utils::get_time_seconds();

        navigation_detection::run();

        auto end = utils::get_time_seconds();
        double elapsed = end - start;
        if (elapsed < 0.050) {
            std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>((0.050 - elapsed) * 1000)));
        }
    }

    return 0;
}