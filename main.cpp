#include "NavigationDetection/navigation_detection.h"
#include "PositionEstimation/position_estimation.h"
#include "ObjectDetection/object_detection.h"
#include "shared_data.h"
#include "ACC/acc.h"
#include "utils.h"
#include "AR/ar.h"

#include <future>
#include <memory>
#include <thread>


int main() {
    SharedData shared_data;
    NavigationDetection navigation_detection(shared_data);

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
            ar->run();

            timer.limit_fps(120.0f);
        }
    });
    ar_thread.detach();

    auto ar = ar_future.get();
    std::thread position_estimation_thread([ar, &shared_data]() {
        PositionEstimation position_estimation(ar.get(), shared_data);
        ObjectDetector object_detector(ObjectDetectionDevice::DirectML, 1);
        utils::Timer timer;

        while (true) {
            auto detections = object_detector.run();

            position_estimation.run(
                detections,
                object_detector.window_width,
                object_detector.window_height
            );

            auto fps = timer.get_fps();
            printf("PositionEstimation FPS: %.2f\n", fps);
        }
    });
    position_estimation_thread.detach();

    ACC acc(shared_data);
    utils::Timer timer;
    while (true) {
        navigation_detection.update();
        acc.update();

        timer.limit_fps(20.0f);
    }

    return 0;
}