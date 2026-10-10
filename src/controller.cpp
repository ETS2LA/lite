#include "controller.h"
#include "utils.h"

#include <algorithm>
#include <chrono>

using namespace std;

Controller::~Controller() {
    pid_running_.store(false, memory_order_release);
    if (pid_thread_.joinable()) {
        pid_thread_.join();
    }
}

void Controller::pid_loop() {
    auto steering_pid = utils::PIDController(10.0f, 0.5f, 0.05f);
    steering_pid.set_integral_limit(1.0f);

    auto acceleration_pid = utils::PIDController(1.0f, 0.05f, 0.3f);
    acceleration_pid.set_integral_limit(5.0f);

    auto brake_pid = utils::PIDController(0.03f, 0.0f, 0.01f);
    brake_pid.set_integral_limit(1.0f);

    ets2la_telemetry::TelemetryReader telemetry_reader;
    ets2la_telemetry::Telemetry telemetry;
    uint64_t last_simulation_time = 0;
    while (pid_running_.load(memory_order_acquire)) {
        if (!telemetry_reader.get_telemetry(telemetry, 1000)) {
            continue;
        }

        // only update PID when telemetry data changed
        if (telemetry.game.simulation_time_us == last_simulation_time) {
            this_thread::sleep_for(chrono::milliseconds(1));
            continue;
        }
        last_simulation_time = telemetry.game.simulation_time_us;

        if (gamepad_mode_.load(memory_order_acquire)) {
            steering_output_.store(
                clamp(
                    steering_pid.update(
                        clamp(steering_target_.load(memory_order_acquire), -1.0f, 1.0f),
                        -clamp(telemetry.truck.effective_steering, -1.0f, 1.0f)
                    ),
                    -1.0f,
                    1.0f
                ),
                memory_order_release
            );
        }

        if (speed_control_.load(memory_order_acquire)) {
            const float target = speed_target_.load(memory_order_acquire);
            if (target - telemetry.truck.speed > -0.1f) {
                acceleration_output_.store(
                    clamp(
                        acceleration_pid.update(
                            target,
                            telemetry.truck.speed
                        ),
                        0.0f,
                        1.0f
                    ),
                    memory_order_release
                );
                brake_output_.store(0.0f, memory_order_release);
                brake_pid.reset();
            } else {
                acceleration_output_.store(0.0f, memory_order_release);
                brake_output_.store(
                    clamp(
                        -brake_pid.update(
                            target,
                            telemetry.truck.speed
                        ),
                        0.0f,
                        1.0f
                    ),
                    memory_order_release
                );
                acceleration_pid.reset();
            }
        }
    }
}

void Controller::update() {
    float throttle = 0.0f;
    float brake = 0.0f;

    if ((gamepad_mode || target_speed.has_value()) && enabled_.load(memory_order_acquire)) {
        // update atomic variables for PID loop
        gamepad_mode_.store(gamepad_mode, memory_order_release);
        speed_control_.store(target_speed.has_value(), memory_order_release);

        if (pid_running_.load(memory_order_acquire) == false) {
            pid_running_.store(true, memory_order_release);
            pid_thread_ = thread(&Controller::pid_loop, this);
        }

        // set and get steering values for steering PID
        if (gamepad_mode) {
            steering_target_.store(steering, memory_order_release);  // steering value from the ControllerData
            steering = steering_output_.load(memory_order_acquire);
        }
        // set and get speed values for speed PID
        if (target_speed.has_value()) {
            speed_target_.store(*target_speed, memory_order_release);
            throttle = acceleration_output_.load(memory_order_acquire);
            brake = brake_output_.load(memory_order_acquire);
        }
    } else if (pid_running_.load(memory_order_acquire)) {
        pid_running_.store(false, memory_order_release);
        if (pid_thread_.joinable()) {
            pid_thread_.join();
        }
    }

    controller_.set(ets2la_controller::Axis::steering, steering);
    controller_.set(ets2la_controller::Axis::throttle, throttle);
    controller_.set(ets2la_controller::Axis::brake, brake);
    controller_.commit();
}

void Controller::enabled(bool enabled) {
    enabled_.store(enabled, memory_order_release);

    if (!enabled) {
        steering = 0.0f;
        target_speed.reset();
        controller_.release_all();
    }
}

bool Controller::is_enabled() const {
    return enabled_.load(memory_order_acquire);
}