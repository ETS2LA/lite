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
    auto throttle_pid = utils::PIDController(1.0f, 0.05f, 0.3f);
    throttle_pid.set_integral_limit(5.0f);

    auto brake_pid = utils::PIDController(0.8f, 0.0f, 0.3f);
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
            if (target - telemetry.truck.speed > -0.1f) {
                throttle_output_.store(
                    clamp(
                        throttle_pid.update(
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
                throttle_output_.store(0.0f, memory_order_release);
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
                throttle_pid.reset();
            }
            if (target < 0.75) {
                brake_output_.store(
                    max(
                        0.2f,
                        brake_output_.load(memory_order_acquire)
                    ),
                    memory_order_release
                );
            }
        }
    }
}

void Controller::distance_speed(float distance, float target_speed) {
    if (!telemetry_reader_.get_latest_telemetry(telemetry_)) {
        return;
    } else {
        ds_start_speed_ = telemetry_.truck.speed;
        ds_current_time_ = telemetry_.game.paused_simulation_time_us;
    }
    ds_enabled_ = true;
    ds_target_distance_ = distance;
    ds_target_speed_ = target_speed;
    ds_current_distance_ = 0;
}

bool Controller::distance_speed_enabled() {
    return ds_enabled_;
}

void Controller::disable_distance_speed() {
    ds_enabled_ = false;
}

void Controller::update() {
    float throttle = 0.0f;
    float brake = 0.0f;

    if (gamepad_mode && steering.has_value() && enabled_.load(memory_order_acquire)) {
        gamepad_mode_.store(gamepad_mode, memory_order_release);

        if (steering_pid_running_.load(memory_order_acquire) == false) {
            steering_pid_running_.store(true, memory_order_release);
            steering_pid_thread_ = thread(&Controller::steering_pid_loop, this);
        }

        steering_target_.store(*steering, memory_order_release);

        controller_.set(ets2la_controller::Axis::steering, steering_output_.load(memory_order_acquire));
    } else if (steering_pid_running_.load(memory_order_acquire)) {
        steering_pid_running_.store(false, memory_order_release);
        if (steering_pid_thread_.joinable()) {
            steering_pid_thread_.join();
        }
    }

    if (ds_enabled_ &&
        telemetry_reader_.get_latest_telemetry(telemetry_) &&
        telemetry_.frame_index != ds_last_frame_index_
    ) {
        ds_last_frame_index_ = telemetry_.frame_index;

        ds_current_distance_ += telemetry_.truck.speed * ((
            telemetry_.game.paused_simulation_time_us -
            ds_current_time_
        ) / 1000000.0);
        ds_current_time_ = telemetry_.game.paused_simulation_time_us;

        float progress = clamp(
            ds_current_distance_ / ds_target_distance_,
            0.0f,
            1.0f
        );

        // 6x^5 - 15x^4 + 10x^3 D=[0; 1] W=[0; 1]
        float ratio = 6 * pow(progress, 5) - 15 * pow(progress, 4) + 10 * pow(progress, 3);

        target_speed = ratio * ds_target_speed_ + (1 - ratio) * ds_start_speed_;

        if (target_speed < 0.75f && progress < 0.95f) {
            target_speed = 0.75f;
        } else if (target_speed < 0.75f) {
            target_speed = 0.0f;
        }

        if (progress >= 1.0f) {
            target_speed = ds_target_speed_;
            disable_distance_speed();
        }
    }

    if (target_speed.has_value() && enabled_.load(memory_order_acquire)) {
        speed_control_.store(target_speed.has_value(), memory_order_release);

        if (speed_pid_running_.load(memory_order_acquire) == false) {
            speed_pid_running_.store(true, memory_order_release);
            speed_pid_thread_ = thread(&Controller::speed_pid_loop, this);
        }

        speed_target_.store(*target_speed, memory_order_release);
        throttle = throttle_output_.load(memory_order_acquire);
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
        steering.reset();
        target_speed.reset();
        controller_.release_all();
    }
}

bool Controller::is_enabled() const {
    return enabled_.load(memory_order_acquire);
}