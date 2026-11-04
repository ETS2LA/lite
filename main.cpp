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

    std::thread object_detection_thread([&shared_data]() {
        ObjectDetector object_detector(
            shared_data,
            ObjectDetector::Config{
                .device = ObjectDetector::Device::DirectML,
                .directml_adapter = 1,
                .confidence_threshold = 0.01
            }
        );

        while (true) {
            object_detector.run();
        }
    });
    object_detection_thread.detach();

    std::thread position_estimation_thread([&shared_data, ar]() {
        PositionEstimation position_estimation(shared_data, ar.get());
        utils::Timer timer;

        while (true) {
            position_estimation.run();

            auto fps = timer.get_fps();
            printf("PositionEstimation FPS: %.2f\n", fps);
        }
    });
    position_estimation_thread.detach();

    utils::Timer timer;
    NavigationDetection navigation_detection(shared_data, ar.get());
    ACC acc(shared_data, ar.get());
    while (true) {
        navigation_detection.update();
        acc.update();

        timer.limit_fps(20.0f);
    }

    return 0;
}