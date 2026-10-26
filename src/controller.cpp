#include "controller.h"

#include "utils.h"

#include <algorithm>
#include <chrono>

using namespace std;


Controller::~Controller() {
    steering_pid_running_.store(false, memory_order_release);
    if (steering_pid_thread_.joinable()) {
        steering_pid_thread_.join();
    }
    speed_pid_running_.store(false, memory_order_release);
    if (speed_pid_thread_.joinable()) {
        speed_pid_thread_.join();
    }
}

void Controller::steering_pid_loop() {
    auto steering_pid = utils::PIDController(10.0f, 0.0f, 0.05f);

    ets2la_telemetry::TelemetryReader telemetry_reader;
    ets2la_telemetry::Telemetry telemetry;
    uint64_t last_simulation_time = 0;
    while (steering_pid_running_.load(memory_order_acquire)) {
        if (!telemetry_reader.get_telemetry(telemetry, 1000)) {
            continue;
        }

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
    }
}

void Controller::speed_pid_loop() {
    auto acceleration_pid = utils::PIDController(1.0f, 0.05f, 0.3f);
    acceleration_pid.set_integral_limit(5.0f);

    auto brake_pid = utils::PIDController(0.03f, 0.0f, 0.01f);
    brake_pid.set_integral_limit(1.0f);

    ets2la_telemetry::TelemetryReader telemetry_reader;
    ets2la_telemetry::Telemetry telemetry;
    uint64_t last_simulation_time = 0;
    while (speed_pid_running_.load(memory_order_acquire)) {
        if (!telemetry_reader.get_telemetry(telemetry, 1000)) {
            continue;
        }

        if (telemetry.game.simulation_time_us == last_simulation_time) {
            this_thread::sleep_for(chrono::milliseconds(1));
            continue;
        }
        last_simulation_time = telemetry.game.simulation_time_us;

        if (speed_control_.load(memory_order_acquire)) {
            const float target = speed_target_.load(memory_order_acquire);
            if (target < 3) {
                acceleration_output_.store(0.0f, memory_order_release);
                acceleration_pid.reset();
                brake_output_.store(0.2f, memory_order_release);
                brake_pid.reset();
            } else if (target - telemetry.truck.speed > -0.1f) {
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

    if (gamepad_mode && enabled_.load(memory_order_acquire)) {
        gamepad_mode_.store(gamepad_mode, memory_order_release);

        if (steering_pid_running_.load(memory_order_acquire) == false) {
            steering_pid_running_.store(true, memory_order_release);
            steering_pid_thread_ = thread(&Controller::steering_pid_loop, this);
        }

        steering_target_.store(steering, memory_order_release);
        steering = steering_output_.load(memory_order_acquire);

        controller_.set(ets2la_controller::Axis::steering, steering);
    } else if (steering_pid_running_.load(memory_order_acquire)) {
        steering_pid_running_.store(false, memory_order_release);
        if (steering_pid_thread_.joinable()) {
            steering_pid_thread_.join();
        }
    }

    if (target_speed.has_value() && enabled_.load(memory_order_acquire)) {
        speed_control_.store(target_speed.has_value(), memory_order_release);

        if (speed_pid_running_.load(memory_order_acquire) == false) {
            speed_pid_running_.store(true, memory_order_release);
            speed_pid_thread_ = thread(&Controller::speed_pid_loop, this);
        }

        speed_target_.store(*target_speed, memory_order_release);
        throttle = acceleration_output_.load(memory_order_acquire);
        brake = brake_output_.load(memory_order_acquire);

        controller_.set(ets2la_controller::Axis::throttle, throttle);
        controller_.set(ets2la_controller::Axis::brake, brake);
    } else if (speed_pid_running_.load(memory_order_acquire)) {
        speed_pid_running_.store(false, memory_order_release);
        if (speed_pid_thread_.joinable()) {
            speed_pid_thread_.join();
        }
    }

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