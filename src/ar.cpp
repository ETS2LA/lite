#include "ar.h"

#define GLFW_EXPOSE_NATIVE_WIN32
#include <GLFW/glfw3native.h>

#include <cmath>
#include <numbers>
#include <vector>

#include "utils.h"

using namespace std;


static void framebuffer_size_callback(GLFWwindow*, int w, int h) {
    glViewport(0, 0, w, h);
}


void AR::window_state_update_thread() {
    while (true) {
        HWND target_hwnd = target_window_handle_function_();
        if (!target_hwnd) {
            continue;
        }

        vector<int> target_position = utils::get_window_position(target_hwnd);

        if (target_position[2] - target_position[0] > 0 &&
            target_position[3] - target_position[1] > 0
        ) {
            window_width_ = target_position[2] - target_position[0];
            window_height_ = target_position[3] - target_position[1];

            // update AR window position and size to match target window
            glfwSetWindowPos(
                window_,
                target_position[0],
                target_position[1]
            );
            glfwSetWindowSize(
                window_,
                window_width_,
                window_height_
            );
        }

        // when the target window is not the foreground window, hide the AR window
        HWND foreground_window = GetForegroundWindow();
        if (foreground_window != target_hwnd) {
            glfwHideWindow(window_);
        } else {
            ShowWindow(glfwGetWin32Window(window_), SW_SHOWNOACTIVATE);
        }

        this_thread::sleep_for(chrono::milliseconds(100));
    }
}


AR::AR(function<HWND()> target_window_handle_function):
target_window_handle_function_(target_window_handle_function) {
    glfwInit();

    // make black pixels transparent
    glClearColor(0.0f, 0.0f, 0.0f, 0.0f);
    glfwWindowHint(GLFW_TRANSPARENT_FRAMEBUFFER, GLFW_TRUE);

    window_ = glfwCreateWindow(100, 100, "AR", nullptr, nullptr);
    if (!window_) {
        glfwTerminate();
        return;
    }

    glfwMakeContextCurrent(window_);
    glfwSetFramebufferSizeCallback(window_, framebuffer_size_callback);

    // enable alpha blending
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    // enable antialiasing
    glEnable(GL_LINE_SMOOTH);

    HWND hwnd = glfwGetWin32Window(window_);
    utils::set_icon(hwnd, L"assets/ar_icon.ico");

    // set window attributes
    glfwSetWindowAttrib(window_, GLFW_DECORATED, GLFW_FALSE);
    glfwSetWindowAttrib(window_, GLFW_RESIZABLE, GLFW_TRUE);
    glfwSetWindowAttrib(window_, GLFW_FLOATING, GLFW_TRUE);
    glfwSetWindowAttrib(window_, GLFW_FOCUSED, GLFW_FALSE);

    // make window click-through
    SetWindowLongW(
        hwnd,
        GWL_EXSTYLE,
        GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED | WS_EX_TRANSPARENT
    );

    // make window invisible to screen captures
    BOOL success = SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE);
    if (!success) {
        fprintf(stderr, "Failed to hide AR window from screen capture.\n");
    }

    // start a thread to update window position
    position_thread_ = thread(
        &AR::window_state_update_thread,
        this
    );
    position_thread_.detach();

    // run one initial window update
    glfwSwapBuffers(window_);
}


AR::~AR() {
    glfwDestroyWindow(window_);
    glfwTerminate();
}


double calculate_front_wheel_radius(double steering_angle, double wheelbase) {
    if (abs(steering_angle) < 0.001) {
        return INFINITY;
    }
    steering_angle = utils::degrees_to_radians(steering_angle);
    return wheelbase / sin(steering_angle);
}


double calculate_back_wheel_radius(double steering_angle, double wheelbase) {
    if (abs(steering_angle) < 0.001) {
        return INFINITY;
    }
    steering_angle = utils::degrees_to_radians(steering_angle);
    return wheelbase / tan(steering_angle);
}


void AR::draw_wheel_trajectory() {
    utils::Rotation truck_rotation{
        static_cast<float>(telemetry_data_->truck_dp.rotationY * 360.0),
        static_cast<float>(telemetry_data_->truck_dp.rotationX * 360.0),
        static_cast<float>(telemetry_data_->truck_dp.rotationZ * 360.0)
    };

    vector<utils::Coordinate> wheel_coords;
    vector<double> wheel_angles;
    for (int i = 0; i < telemetry_data_->config_ui.truckWheelCount; ++i) {
        if (telemetry_data_->config_b.truckWheelSimulated[i]) {
            utils::Coordinate wheel_vector{
                telemetry_data_->config_fv.truckWheelPositionX[i],
                telemetry_data_->config_fv.truckWheelPositionY[i],
                telemetry_data_->config_fv.truckWheelPositionZ[i]
            };
            wheel_vector = utils::rotate_vector(wheel_vector, truck_rotation);
            utils::Coordinate coord{
                telemetry_data_->truck_dp.coordinateX + wheel_vector.x,
                telemetry_data_->truck_dp.coordinateY + wheel_vector.y,
                telemetry_data_->truck_dp.coordinateZ + wheel_vector.z
            };
            wheel_coords.push_back(coord);

            if (telemetry_data_->config_b.truckWheelSteerable[i]) {
                wheel_angles.push_back(
                    telemetry_data_->truck_f.truck_wheelSteering[i] * 360.0f
                );
            }
        }
    }

    if (wheel_coords.size() < 4 || wheel_angles.size() < 2) {
        return;
    }

    utils::Coordinate front_left_wheel = wheel_coords[0];
    utils::Coordinate front_right_wheel = wheel_coords[1];

    utils::Coordinate back_left_wheel{0, 0, 0};
    utils::Coordinate back_right_wheel{0, 0, 0};

    for (int i = wheel_angles.size(); i < wheel_coords.size(); ++i) {
        if (i % 2 == 0) {
            back_left_wheel.x += wheel_coords[i].x;;
            back_left_wheel.y += wheel_coords[i].y;
            back_left_wheel.z += wheel_coords[i].z;
        } else {
            back_right_wheel.x += wheel_coords[i].x;;
            back_right_wheel.y += wheel_coords[i].y;
            back_right_wheel.z += wheel_coords[i].z;
        }
    }

    back_left_wheel.x /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_left_wheel.y /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_left_wheel.z /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.x /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.y /= (wheel_coords.size() - wheel_angles.size()) / 2;
    back_right_wheel.z /= (wheel_coords.size() - wheel_angles.size()) / 2;

    double wheel_base_left = sqrt(
        pow(front_left_wheel.x - back_left_wheel.x, 2) +
        pow(front_left_wheel.y - back_left_wheel.y, 2) +
        pow(front_left_wheel.z - back_left_wheel.z, 2)
    );
    double wheel_base_right = sqrt(
        pow(front_right_wheel.x - back_right_wheel.x, 2) +
        pow(front_right_wheel.y - back_right_wheel.y, 2) +
        pow(front_right_wheel.z - back_right_wheel.z, 2)
    );

    double front_left_wheel_radius = calculate_front_wheel_radius(
        wheel_angles[0],
        wheel_base_left
    );
    double front_right_wheel_radius = calculate_front_wheel_radius(
        wheel_angles[1],
        wheel_base_right
    );
    double back_left_wheel_radius = calculate_back_wheel_radius(
        wheel_angles[0],
        wheel_base_left
    );
    double back_right_wheel_radius = calculate_back_wheel_radius(
        wheel_angles[1],
        wheel_base_right
    );

    if (front_left_wheel_radius == INFINITY) front_left_wheel_radius = 1000000.0;
    if (front_right_wheel_radius == INFINITY) front_right_wheel_radius = 1000000.0;
    if (back_left_wheel_radius == INFINITY) back_left_wheel_radius = 1000000.0;
    if (back_right_wheel_radius == INFINITY) back_right_wheel_radius = 1000000.0;

    utils::Coordinate left_offset_local{
        -back_left_wheel_radius - 0.3,
        0.0,
        0.0
    };
    utils::Coordinate left_offset_world = utils::rotate_vector(left_offset_local, truck_rotation);
    utils::Coordinate left_circle_center{
        back_left_wheel.x + left_offset_world.x,
        telemetry_data_->truck_dp.coordinateY + left_offset_world.y,
        back_left_wheel.z + left_offset_world.z
    };

    utils::Coordinate right_offset_local{
        -back_right_wheel_radius + 0.3,
        0.0,
        0.0
    };
    utils::Coordinate right_offset_world = utils::rotate_vector(right_offset_local, truck_rotation);
    utils::Coordinate right_circle_center{
        back_right_wheel.x + right_offset_world.x,
        telemetry_data_->truck_dp.coordinateY + right_offset_world.y,
        back_right_wheel.z + right_offset_world.z
    };

    utils::CameraCoordinate camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    glLineWidth(3.0f);
    glColor4f(1.0f, 0.75f, 0.0f, 1.0f);
    glBegin(GL_LINE_STRIP);
    for (int i = 0; i <= 45; ++i) {
        double angle = utils::degrees_to_radians(
            i * (1.0 / -front_left_wheel_radius) * 30.0 - utils::radians_to_degrees(atan(wheel_base_left / front_left_wheel_radius))
        );

        utils::Coordinate local_point{
            front_left_wheel_radius * cos(angle),
            0.0,
            front_left_wheel_radius * sin(angle)
        };
        utils::Coordinate world_point = utils::rotate_vector(local_point, truck_rotation);

        double x = left_circle_center.x + world_point.x;
        double y = left_circle_center.y + world_point.y;
        double z = left_circle_center.z + world_point.z;

        utils::ScreenCoordinate screen_coords = utils::convert_to_screen_coordinate(
            {x, y, z},
            camera_coords,
            window_width_,
            window_height_
        );
        if (screen_coords.distance < 0) {
            continue;
        }

        glVertex2f(
            (screen_coords.x / window_width_) * 2 - 1,
            1 - (screen_coords.y / window_height_) * 2
        );
    }
    glEnd();

    glBegin(GL_LINE_STRIP);
    for (int i = 0; i <= 45; ++i) {
        double angle = utils::degrees_to_radians(
            i * (1.0 / -front_right_wheel_radius) * 30.0 - utils::radians_to_degrees(atan(wheel_base_right / front_right_wheel_radius))
        );

        utils::Coordinate local_point{
            front_right_wheel_radius * cos(angle),
            0.0,
            front_right_wheel_radius * sin(angle)
        };
        utils::Coordinate world_point = utils::rotate_vector(local_point, truck_rotation);

        double x = right_circle_center.x + world_point.x;
        double y = right_circle_center.y + world_point.y;
        double z = right_circle_center.z + world_point.z;

        utils::ScreenCoordinate screen_coords = utils::convert_to_screen_coordinate(
            {x, y, z},
            camera_coords,
            window_width_,
            window_height_
        );
        if (screen_coords.distance < 0) {
            continue;
        }

        glVertex2f(
            (screen_coords.x / window_width_) * 2 - 1,
            1 - (screen_coords.y / window_height_) * 2
        );
    }
    glEnd();
}


void AR::run() {
    if (!window_) return;
    glfwPollEvents();

    telemetry_data_ = telemetry_.data();
    if (!telemetry_data_->sdkActive || telemetry_data_->paused) {
        return;
    }

    utils::Coordinate world_coords{
        10350,
        45,
        -9166
    };

    utils::CameraCoordinate camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    utils::ScreenCoordinate screen_coords = utils::convert_to_screen_coordinate(
        world_coords,
        camera_coords,
        window_width_,
        window_height_
    );

    glClear(GL_COLOR_BUFFER_BIT);

    glPointSize(50.0f);
    glBegin(GL_POINTS);
    glColor4f(1.0f, 0.0f, 0.0f, 1.0f);
    glVertex2f(
        (screen_coords.x / window_width_) * 2 - 1,
        1 - (screen_coords.y / window_height_) * 2
    );
    glEnd();

    AR::draw_wheel_trajectory();

    glfwSwapBuffers(window_);
}