#pragma once

#include <ets2la_telemetry/telemetry_reader.h>
#include <ets2la_controller/controller.h>

#include <optional>
#include <atomic>
#include <thread>


class Controller {
public:
    Controller() = default;
    ~Controller();

    void distance_speed(float distance, float target_speed);
    bool distance_speed_enabled();
    void disable_distance_speed();
    void update();
    void enabled(bool enabled);
    bool is_enabled() const;

    bool connected() const { return controller_.connected(); }
    const std::string& last_error() const { return controller_.last_error(); }
    void set(ets2la_controller::Axis axis, float value) { controller_.set(axis, value); }
    void set(ets2la_controller::Button button, bool down) { controller_.set(button, down); }
    void press(ets2la_controller::Button button) { controller_.press(button); }
    float get(ets2la_controller::Axis axis) const { return controller_.get(axis); }
    bool get(ets2la_controller::Button button) const { return controller_.get(button); }
    void release_all() { controller_.release_all(); }
    void commit() { controller_.commit(); }
    void heartbeat() { controller_.heartbeat(); }
    bool wait_frame(uint32_t timeout_ms = 1000) { return controller_.wait_frame(timeout_ms); }
    ets2la_controller::Latency latency() const { return controller_.latency(); }
    ets2la_controller::ControllerStats stats() const { return controller_.stats(); }
    void reset_stats() { controller_.reset_stats(); }
    void set_delivery_mode(ets2la_controller::DeliveryMode mode) {
        controller_.set_delivery_mode(mode);
    }

    bool gamepad_mode = false;
    std::optional<float> target_speed;
    float steering = 0.0f;

private:
    void steering_pid_loop();
    void speed_pid_loop();

    ets2la_telemetry::TelemetryReader telemetry_reader_;
    ets2la_telemetry::Telemetry telemetry_;
    ets2la_controller::Controller controller_;
    std::thread steering_pid_thread_;
    std::thread speed_pid_thread_;
    std::atomic<bool> steering_pid_running_{false};
    std::atomic<bool> speed_pid_running_{false};
    std::atomic<bool> enabled_{true};
    std::atomic<float> steering_target_{0.0f};
    std::atomic<float> steering_output_{0.0f};
    std::atomic<float> speed_target_{0.0f};
    std::atomic<float> acceleration_output_{0.0f};
    std::atomic<float> brake_output_{0.0f};
    std::atomic<bool> gamepad_mode_{false};
    std::atomic<bool> speed_control_{false};

    bool ds_enabled_ = false;
    float ds_target_distance_;
    float ds_target_speed_;
    float ds_start_speed_;
    float ds_current_distance_;
    float ds_current_time_;
    uint64_t ds_last_frame_index_;
};
