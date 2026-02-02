#include "AR/ar.h"
#include <numbers>

using namespace std;


void AR::line(
    const float x1,
    const float y1,
    const float x2,
    const float y2,
    const float roundness,
    const float thickness,
    const utils::ColorFloat& color
) {
    if (window_width_ <= 0 || window_height_ <= 0) return;

    glColor4f(color.r, color.g, color.b, color.a);
    vector<pair<float, float>> points;

    if (roundness <= 0.0f) {
        points.reserve(4);

        float dx = x2 - x1;
        float dy = y2 - y1;
        float length = sqrtf(dx * dx + dy * dy);
        if (length == 0.0f) return;

        float ux = dx / length;
        float uy = dy / length;

        float half_thickness = thickness * 0.5f;

        float px = -uy * half_thickness;
        float py = ux * half_thickness;

        float ex = ux * half_thickness;
        float ey = uy * half_thickness;

        float sx = x1 - ex;
        float sy = y1 - ey;
        float ex2 = x2 + ex;
        float ey2 = y2 + ey;

        points.emplace_back(sx + px, sy + py);
        points.emplace_back(ex2 + px, ey2 + py);
        points.emplace_back(ex2 - px, ey2 - py);
        points.emplace_back(sx - px, sy - py);

        glBegin(GL_QUADS);
        for (const auto& [px, py] : points) {
            glVertex2f(
                (px / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - (py / static_cast<float>(window_height_)) * 2.0f
            );
        }
        glEnd();
    } else {
        float dx = x2 - x1;
        float dy = y2 - y1;
        float length = sqrtf(dx * dx + dy * dy);
        if (length == 0.0f) return;

        float ux = dx / length;
        float uy = dy / length;

        const float half_thickness = thickness * 0.5f;
        float radius = half_thickness * max(0.0f, min(roundness, 1.0f));

        float ex = ux * half_thickness;
        float ey = uy * half_thickness;

        const float origin_x = x1 - ex;
        const float origin_y = y1 - ey;

        const float expanded_length = length + thickness;

        radius = min(radius, half_thickness);
        radius = min(radius, expanded_length * 0.5f);
        if (radius <= 0.0f) {
            AR::line(x1, y1, x2, y2, 0.0f, thickness, color);
            return;
        }

        const int segments_per_corner = max(ceil(0.5f * numbers::pi_v<float> * sqrt(radius)), 3.0f);

        const float left = 0.0f;
        const float right = expanded_length;
        const float top = half_thickness;
        const float bottom = -half_thickness;

        const float nx = -uy;
        const float ny = ux;

        auto to_world = [&](float local_x, float local_y) {
            const float wx = origin_x + local_x * ux + local_y * nx;
            const float wy = origin_y + local_x * uy + local_y * ny;
            points.emplace_back(wx, wy);
        };

        points.reserve(static_cast<size_t>(segments_per_corner * 4 + 4));

        // top left corner
        for (int i = 0; i <= segments_per_corner; ++i) {
            float theta = numbers::pi_v<float> - (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
            float lx = left + radius + radius * cosf(theta);
            float ly = (top - radius) + radius * sinf(theta);
            to_world(lx, ly);
        }
        // top right corner
        for (int i = 0; i <= segments_per_corner; ++i) {
            float theta = numbers::pi_v<float> * 0.5f - (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
            float lx = right - radius + radius * cosf(theta);
            float ly = (top - radius) + radius * sinf(theta);
            to_world(lx, ly);
        }
        // bottom right corner
        for (int i = 0; i <= segments_per_corner; ++i) {
            float theta = 0.0f - (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
            float lx = right - radius + radius * cosf(theta);
            float ly = (bottom + radius) + radius * sinf(theta);
            to_world(lx, ly);
        }
        // bottom left corner
        for (int i = 0; i <= segments_per_corner; ++i) {
            float theta = -numbers::pi_v<float> * 0.5f - (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
            float lx = left + radius + radius * cosf(theta);
            float ly = (bottom + radius) + radius * sinf(theta);
            to_world(lx, ly);
        }

        glBegin(GL_TRIANGLE_FAN);
        for (const auto& [px, py] : points) {
            glVertex2f(
                (px / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - (py / static_cast<float>(window_height_)) * 2.0f
            );
        }
        glEnd();
    }
}


void AR::line(
    const utils::ScreenCoordinates& start,
    const utils::ScreenCoordinates& end,
    const float roundness,
    const float thickness,
    const utils::ColorFloat& color
) {
    AR::line(
        static_cast<float>(start.x),
        static_cast<float>(start.y),
        static_cast<float>(end.x),
        static_cast<float>(end.y),
        roundness,
        thickness,
        color
    );
}


void AR::line(
    const utils::Coordinates& start,
    const utils::Coordinates& end,
    const float roundness,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::CameraCoordinates camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    utils::ScreenCoordinates screen_start = utils::convert_to_screen_coordinate(
        start,
        camera_coords,
        window_width_,
        window_height_
    );
    utils::ScreenCoordinates screen_end = utils::convert_to_screen_coordinate(
        end,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::line(
        static_cast<float>(screen_start.x),
        static_cast<float>(screen_start.y),
        static_cast<float>(screen_end.x),
        static_cast<float>(screen_end.y),
        roundness,
        thickness,
        color
    );
}


void AR::line(
    const utils::Coordinates& start,
    const utils::Coordinates& end,
    const utils::CameraCoordinates& camera_coords,
    const float roundness,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::ScreenCoordinates screen_start = utils::convert_to_screen_coordinate(
        start,
        camera_coords,
        window_width_,
        window_height_
    );
    utils::ScreenCoordinates screen_end = utils::convert_to_screen_coordinate(
        end,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::line(
        static_cast<float>(screen_start.x),
        static_cast<float>(screen_start.y),
        static_cast<float>(screen_end.x),
        static_cast<float>(screen_end.y),
        roundness,
        thickness,
        color
    );
}