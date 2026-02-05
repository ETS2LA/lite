#include "PositionEstimation/position_estimation.h"
#include "navigation_detection.h"
#include "utils.h"
#include "AR/ar.h"
#include <thread>


int main() {
    ScreenCapture* capture = new ScreenCapture(
        std::bind(
            utils::find_window,
            std::wstring(L"Truck Simulator"),
            std::vector<std::wstring>{L"Discord"}
        ),
        CaptureMode::BackgroundThread
    );
    capture->initialize();

    navigation_detection::initialize(capture);

    std::thread ar_thread([capture]() {
        AR ar(
            std::bind(
                utils::find_window,
                std::wstring(L"Truck Simulator"),
                std::vector<std::wstring>{L"Discord"}
            )
        );

        PositionEstimation position_estimation(capture);

        while (true) {
            auto start = utils::get_time_seconds();

            position_estimation.run(ar);

            ar.draw_wheel_trajectory({1.0f, 0.75f, 0.0f, 1.0f});

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