#include "PositionEstimation/position_estimation.h"
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

        utils::Timer timer;
        while (true) {
            ar->draw_wheel_trajectory({1.0f, 0.75f, 0.0f, 1.0f});

            ar->run();

            timer.limit_fps(120.0f);
        }
    });
    ar_thread.detach();

    auto ar = ar_future.get();
    std::thread position_estimation_thread([ar]() {
        PositionEstimation position_estimation(ar.get());
        ObjectDetector object_detector(ObjectDetectionDevice::DirectML, 1);
        utils::Timer timer;

        while (true) {
            auto detections = object_detector.run();

            // remove all detections from class 0, 1, 2
            //std::vector<ObjectDetection> filtered_detections;
            //for (const auto& detection : detections) {
            //    if (detection.class_id != 0 && detection.class_id != 1 && detection.class_id != 2) {
            //        filtered_detections.push_back(detection);
            //    }
            //}

            position_estimation.run(
                detections,
                object_detector.window_width,
                object_detector.window_height
            );
            //timer.limit_fps(10.0f);
            auto fps = timer.get_fps();
            printf("PositionEstimation FPS: %.2f\n", fps);
        }
    });
    position_estimation_thread.detach();

    utils::Timer timer;
    while (true) {
        navigation_detection::run();

        timer.limit_fps(20.0f);
    }

    return 0;
}