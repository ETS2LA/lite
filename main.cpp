#include "PositionEstimation/position_estimation.h"
#include "TrafficLights/traffic_lights.h"
#include "navigation_detection.h"
#include "utils.h"
#include "AR/ar.h"
#include "object_detection.h"
#include <future>
#include <memory>
#include <thread>


int main() {
    //ScreenCapture* capture = new ScreenCapture(
    //    std::bind(
    //        utils::find_window,
    //        std::wstring(L"Truck Simulator"),
    //        std::vector<std::wstring>{L"Discord"}
    //    ),
    //    CaptureMode::BackgroundThread
    //);
    //capture->initialize();

    navigation_detection::initialize();

    std::promise<std::shared_ptr<AR>> ar_ready;
    auto ar_future = ar_ready.get_future();

    std::thread ar_thread([ar_ready = std::move(ar_ready)]() mutable {
        auto ar = std::make_shared<AR>(
            std::bind(
                utils::find_window,
                std::wstring(L"Truck Simulator"),
                std::vector<std::wstring>{L"Discord"}
            )
        );
        ar_ready.set_value(ar);

        while (true) {
            auto start = utils::get_time_seconds();

            ar->draw_wheel_trajectory({1.0f, 0.75f, 0.0f, 1.0f});

            ar->run();

            auto end = utils::get_time_seconds();
            double elapsed = end - start;

            // target 120FPS because its twice the game telemetry update rate
            if (elapsed < 0.0083) {
                std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>((0.0083 - elapsed) * 1000)));
            }
        }
    });
    ar_thread.detach();

    auto ar = ar_future.get();
    std::thread position_estimation_thread([ar]() {
        PositionEstimation position_estimation;
        ObjectDetector object_detector(ar.get(), ObjectDetectionDevice::DirectML, 0);

        while (true) {
            auto detections = object_detector.run();
            position_estimation.run(
                detections,
                object_detector.window_width,
                object_detector.window_height
            );
        }
    });
    position_estimation_thread.detach();

    //std::thread traffic_lights_thread([capture]() {
    //    traffic_lights::initialize(capture);
//
    //    while (true) {
    //        traffic_lights::run();
    //    }
    //});
    //traffic_lights_thread.detach();

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