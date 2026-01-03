#include "navigation_detection.h"
#include "utils.h"
#include "ar.h"
#include <thread>


int main() {
    navigation_detection::initialize();

    std::thread ar_thread([]() {
        AR ar(
            std::bind(
                utils::find_window,
                std::wstring(L"Truck Simulator"),
                std::vector<std::wstring>{ L"Discord" }
            )
        );

        while (true) {
            auto start = utils::get_time_seconds();

            ar.run();

            auto end = utils::get_time_seconds();
            double elapsed = end - start;

            // target 120FPS because its twice the game telemetry update rate
            if (elapsed < 0.0083) {
                std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>((0.0083 - elapsed) * 1000)));
            }
        }
    });
    ar_thread.detach();

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