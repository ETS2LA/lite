#include "controller.h"
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
pid_output_(0.0f),
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
    float kp = 10.0f;
    float ki = 0.5f;
    float kd = 0.05f;
    float integral = 0.0f;
    float previous_error = 0.0f;

    SCSTelemetry telemetry;
    unsigned long long last_simulated_time = 0;
    auto last_time = std::chrono::high_resolution_clock::now();

    while (pid_running_.load(std::memory_order_relaxed)) {
        TelemetryData* telemetry_data = telemetry.data();

        // only update PID when telemetry data changed
        if (telemetry_data->simulatedTime == last_simulated_time) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
            continue;
        }
        last_simulated_time = telemetry_data->simulatedTime;

        auto current_time = std::chrono::high_resolution_clock::now();
        float dt = std::chrono::duration<float>(current_time - last_time).count();
        last_time = current_time;
        if (dt <= 0.0f) {
            continue;
        }

        float target = clamp(steering_target_.load(std::memory_order_relaxed), -1.0f, 1.0f);
        float feedback = -clamp(telemetry_data->truck_f.gameSteer, -1.0f, 1.0f);
        float error = target - feedback;

        integral += error * dt;
        float derivative = (error - previous_error) / dt;
        float output = clamp(kp * error + ki * integral + kd * derivative, -1.0f, 1.0f);

        pid_output_.store(output, std::memory_order_relaxed);
        integral = clamp(integral, -1.0f, 1.0f);
        previous_error = error;
    }
}


/**
 * Update the controller state and send it to the game if enabled.
 * @param gamepad_mode Whether to use gamepad mode (PID control) or direct control
 */
void SCSController::update(bool gamepad_mode) {
    if (gamepad_mode && enabled_.load(std::memory_order_relaxed)) {
        if (pid_running_.load(std::memory_order_relaxed) == false) {
            pid_running_.store(true, std::memory_order_relaxed);
            pid_thread_ = thread(&SCSController::pid_loop, this);
        }
        // set and get steering values for PID
        steering_target_.store(steering, std::memory_order_relaxed);  // steering value from the ControllerData
        steering = pid_output_.load(std::memory_order_relaxed);
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
}


/**
 * Check if the controller input is enabled.
 * @return True if enabled, false otherwise
 */
bool SCSController::is_enabled() const {
    return enabled_.load(std::memory_order_relaxed);
}