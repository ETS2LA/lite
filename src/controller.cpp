#include "controller.h"
#include "utils.h"

#include <windows.h>
#include <algorithm>
#include <chrono>
#include <iostream>
#include <thread>

using namespace std;


SCSController::SCSController():
initialized(false),
map_file(NULL),
buffer(NULL),
pid_running_(false),
steering_target_(0.0f),
steering_output_(0.0f),
speed_target_(0.0f),
acceleration_output_(0.0f),
brake_output_(0.0f),
enabled_(true)
{
    memset(static_cast<ControllerData*>(this), 0, sizeof(ControllerData));

    size_t shm_size = sizeof(ControllerData);

    map_file = CreateFileMappingA(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        (DWORD)shm_size,
        "Local\\SCSControls"
    );

    if (map_file == NULL) {
        printf("Could not create file mapping object (%lu).\n", GetLastError());
        return;
    }

    buffer = MapViewOfFile(
        map_file,
        FILE_MAP_ALL_ACCESS,
        0,
        0,
        shm_size
    );

    if (buffer == NULL) {
        printf("Could not map view of file (%lu).\n", GetLastError());
        CloseHandle(map_file);
        map_file = NULL;
        return;
    }

    initialized = true;
}

SCSController::~SCSController() {
    pid_running_.store(false, std::memory_order_relaxed);
    if (pid_thread_.joinable()) {
        pid_thread_.join();
    }
    if (buffer) {
        UnmapViewOfFile(buffer);
        buffer = NULL;
    }
    if (map_file) {
        CloseHandle(map_file);
        map_file = NULL;
    }
}


void SCSController::pid_loop() {
    auto steering_pid = utils::PIDController(10.0f, 0.5f, 0.05f);
    steering_pid.set_integral_limit(1.0f);

    auto acceleration_pid = utils::PIDController(1.0f, 0.05f, 0.3f);
    acceleration_pid.set_integral_limit(1.0f);

    auto brake_pid = utils::PIDController(0.03f, 0.00f, 0.01f);
    brake_pid.set_integral_limit(1.0f);

    SCSTelemetry telemetry;
    unsigned long long last_simulated_time = 0;

    while (pid_running_.load(std::memory_order_relaxed)) {
        TelemetryData* telemetry_data = telemetry.data();

        // only update PID when telemetry data changed
        if (telemetry_data->simulatedTime == last_simulated_time) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
            continue;
        }
        last_simulated_time = telemetry_data->simulatedTime;

        if (gamepad_mode_.load(std::memory_order_relaxed)) {
            steering_output_.store(
                clamp(
                    steering_pid.update(
                        clamp(steering_target_.load(std::memory_order_relaxed), -1.0f, 1.0f),
                        -clamp(telemetry_data->truck_f.gameSteer, -1.0f, 1.0f)
                    ),
                    -1.0f,
                    1.0f
                ),
                std::memory_order_relaxed
            );
        }

        if (speed_control_.load(std::memory_order_relaxed)) {
            if (speed_target_ - telemetry_data->truck_f.speed > -0.1f) {
                acceleration_output_.store(
                    clamp(
                        acceleration_pid.update(
                            speed_target_.load(std::memory_order_relaxed),
                            telemetry_data->truck_f.speed
                        ),
                        0.0f,
                        1.0f
                    ),
                    std::memory_order_relaxed
                );
                brake_output_.store(0.0f, std::memory_order_relaxed);
                brake_pid.reset();
            } else {
                acceleration_output_.store(0.0f, std::memory_order_relaxed);
                brake_output_.store(
                    clamp(
                        -brake_pid.update(
                            speed_target_.load(std::memory_order_relaxed),
                            telemetry_data->truck_f.speed
                        ),
                        0.0f,
                        1.0f
                    ),
                    std::memory_order_relaxed
                );
                acceleration_pid.reset();
            }
        }
    }
}


/**
 * Update the controller state and send it to the game if enabled.
 * @param gamepad_mode Whether to use gamepad mode (PID control) or direct control
 * @param target_speed The target speed for PID control (if enabled)
 */
void SCSController::update() {
    if ((gamepad_mode || target_speed.has_value()) && enabled_.load(std::memory_order_relaxed)) {
        // update atomic variables for PID loop
        gamepad_mode_.store(gamepad_mode, std::memory_order_relaxed);
        speed_control_.store(target_speed.has_value(), std::memory_order_relaxed);

        if (pid_running_.load(std::memory_order_relaxed) == false) {
            pid_running_.store(true, std::memory_order_relaxed);
            pid_thread_ = thread(&SCSController::pid_loop, this);
        }

        // set and get steering values for steering PID
        if (gamepad_mode) {
            steering_target_.store(steering, std::memory_order_relaxed);  // steering value from the ControllerData
            steering = steering_output_.load(std::memory_order_relaxed);
        }
        // set and get speed values for speed PID
        if (target_speed.has_value()) {
            speed_target_.store(target_speed.value(), std::memory_order_relaxed);
            aforward = acceleration_output_.load(std::memory_order_relaxed);
            abackward = brake_output_.load(std::memory_order_relaxed);
            printf("Acceleration: %06.2f, Brake: %06.2f, Target Speed: %.2f\n", aforward, abackward, speed_target_.load(std::memory_order_relaxed)*3.6f);
        }
    } else if (pid_running_.load(std::memory_order_relaxed)) {
        pid_running_.store(false, std::memory_order_relaxed);
        if (pid_thread_.joinable()) {
            pid_thread_.join();
        }
    }

    if (initialized && buffer) {
        memcpy(buffer, static_cast<ControllerData*>(this), sizeof(ControllerData));
    }

    // set indicators back to false
    lblinker = false;
    rblinker = false;
}


/**
 * Enable or disable the controller input.
 * The enabled state only affects the PID control mode.
 * @param enabled Whether to enable or disable the controller
 */
void SCSController::enabled(bool enabled) {
    enabled_.store(enabled, std::memory_order_relaxed);

    if (!enabled) {
        steering = 0.0f;
        aforward = 0.0f;
        abackward = 0.0f;
        target_speed = nullopt;
    }
}


/**
 * Check if the controller input is enabled.
 * @return True if enabled, false otherwise
 */
bool SCSController::is_enabled() const {
    return enabled_.load(std::memory_order_relaxed);
}