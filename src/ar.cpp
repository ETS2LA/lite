#include "ar.h"

#define GLFW_EXPOSE_NATIVE_WIN32
#include <GLFW/glfw3native.h>

#include "utils.h"

using namespace std;


static void framebuffer_size_callback(GLFWwindow*, int w, int h) {
    glViewport(0, 0, w, h);
}


void window_state_update_thread(GLFWwindow* window, function<HWND()> target_window_handle_function) {
    while (true) {
        HWND target_hwnd = target_window_handle_function();
        if (!target_hwnd) {
            continue;
        }

        vector<int> target_position = utils::get_window_position(target_hwnd);

        if (target_position[2] - target_position[0] > 0 &&
            target_position[3] - target_position[1] > 0
        ) {
            // update AR window position and size to match target window
            glfwSetWindowPos(
                window,
                target_position[0],
                target_position[1]
            );
            glfwSetWindowSize(
                window,
                target_position[2] - target_position[0],
                target_position[3] - target_position[1]
            );
        }

        // when the target window is not the foreground window, hide the AR window
        HWND foreground_window = GetForegroundWindow();
        if (foreground_window != target_hwnd) {
            glfwHideWindow(window);
        } else {
            glfwShowWindow(window);
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
        window_state_update_thread,
        window_,
        target_window_handle_function_
    );
    position_thread_.detach();
}


AR::~AR() {
    glfwDestroyWindow(window_);
    glfwTerminate();
}


void AR::run() {
    if (!window_) return;

    glfwPollEvents();
    glClear(GL_COLOR_BUFFER_BIT);

    // draw semi-transparent white triangle
    glBegin(GL_TRIANGLES);
    glColor4f(1.0f, 1.0f, 1.0f, 0.5f);
    glVertex2f(-0.5f, -0.5f);
    glVertex2f(0.5f, -0.5f);
    glVertex2f(0.0f, 0.5f);
    glEnd();

    // draw opaque white outline around the triangle
    glLineWidth(3.0f);
    glBegin(GL_LINE_LOOP);
    glColor4f(1.0f, 1.0f, 1.0f, 1.0f);
    glVertex2f(-0.5f, -0.5f);
    glVertex2f(0.5f, -0.5f);
    glVertex2f(0.0f, 0.5f);
    glEnd();

    glfwSwapBuffers(window_);
}