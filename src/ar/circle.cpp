#include "ar/ar.h"
#include <numbers>

using namespace std;


void AR::circle(
    const float x,
    const float y,
    const float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    if (window_width_ <= 0 || window_height_ <= 0) return;

    const int segments = max(ceil(2.0f * numbers::pi_v<float> * sqrt(radius)), 4.0f);

    if (thickness > 0) {
        glLineWidth(thickness);
        glColor4f(color.r, color.g, color.b, color.a);
        glBegin(GL_LINE_LOOP);
        for (int i = 0; i < segments; ++i) {
            float theta = 2.0f * numbers::pi_v<float> * static_cast<float>(i) / static_cast<float>(segments);
            float dx = radius * cosf(theta);
            float dy = radius * sinf(theta);

            glVertex2f(
                ((x + dx) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - ((y + dy) / static_cast<float>(window_height_)) * 2.0f
            );
        }
        glEnd();
    } else {
        glColor4f(color.r, color.g, color.b, color.a);
        glBegin(GL_TRIANGLE_FAN);
        glVertex2f(
            (x / static_cast<float>(window_width_)) * 2.0f - 1.0f,
            1.0f - (y / static_cast<float>(window_height_)) * 2.0f
        );
        for (int i = 0; i <= segments; ++i) {
            float theta = 2.0f * numbers::pi_v<float> * static_cast<float>(i) / static_cast<float>(segments);
            float dx = radius * cosf(theta);
            float dy = radius * sinf(theta);

            glVertex2f(
                ((x + dx) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - ((y + dy) / static_cast<float>(window_height_)) * 2.0f
            );
        }
        glEnd();
    }
}


void AR::circle(
    const utils::ScreenCoordinate& center,
    const float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    AR::circle(
        static_cast<float>(center.x),
        static_cast<float>(center.y),
        radius,
        thickness,
        color
    );
}


void AR::circle(
    const utils::Coordinate& center,
    const float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::CameraCoordinate camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    utils::ScreenCoordinate screen_coords = utils::convert_to_screen_coordinate(
        center,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::circle(
        static_cast<float>(screen_coords.x),
        static_cast<float>(screen_coords.y),
        radius,
        thickness,
        color
    );
}


void AR::circle(
    const utils::Coordinate& center,
    const utils::CameraCoordinate& camera_coords,
    const float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::ScreenCoordinate screen_coords = utils::convert_to_screen_coordinate(
        center,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::circle(
        static_cast<float>(screen_coords.x),
        static_cast<float>(screen_coords.y),
        radius,
        thickness,
        color
    );
}