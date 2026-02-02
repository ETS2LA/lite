#include "AR/ar.h"
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

    glColor4f(color.r, color.g, color.b, color.a);
    if (thickness > 0) {
        vector<pair<float, float>> inner_points;
        vector<pair<float, float>> outer_points;
        inner_points.reserve(segments + 1);
        outer_points.reserve(segments + 1);

        for (int i = 0; i <= segments; ++i) {
            float theta = 2.0f * numbers::pi_v<float> * static_cast<float>(i) / static_cast<float>(segments);
            float dx = cosf(theta);
            float dy = sinf(theta);

            inner_points.emplace_back(
                x + (radius - thickness * 0.5f) * dx,
                y + (radius - thickness * 0.5f) * dy
            );
            outer_points.emplace_back(
                x + (radius + thickness * 0.5f) * dx,
                y + (radius + thickness * 0.5f) * dy
            );
        }

        glBegin(GL_TRIANGLE_STRIP);
        for (size_t i = 0; i < inner_points.size(); ++i) {
            const auto& [ix, iy] = inner_points[i];
            const auto& [ox, oy] = outer_points[i];

            glVertex2f(
                (ox / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - (oy / static_cast<float>(window_height_)) * 2.0f
            );
            glVertex2f(
                (ix / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - (iy / static_cast<float>(window_height_)) * 2.0f
            );
        }
        const auto& [ix0, iy0] = inner_points[0];
        const auto& [ox0, oy0] = outer_points[0];
        glVertex2f(
            (ox0 / static_cast<float>(window_width_)) * 2.0f - 1.0f,
            1.0f - (oy0 / static_cast<float>(window_height_)) * 2.0f
        );
        glVertex2f(
            (ix0 / static_cast<float>(window_width_)) * 2.0f - 1.0f,
            1.0f - (iy0 / static_cast<float>(window_height_)) * 2.0f
        );
        glEnd();
    } else {
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
    const utils::ScreenCoordinates& center,
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
    const utils::Coordinates& center,
    const float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::CameraCoordinates camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    utils::ScreenCoordinates screen_coords = utils::convert_to_screen_coordinate(
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
    const utils::Coordinates& center,
    const utils::CameraCoordinates& camera_coords,
    const float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::ScreenCoordinates screen_coords = utils::convert_to_screen_coordinate(
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