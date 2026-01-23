#include "ar/ar.h"
#include <numbers>

using namespace std;


void AR::rectangle(
    const float x1,
    const float y1,
    const float x2,
    const float y2,
    float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    if (window_width_ <= 0 || window_height_ <= 0) return;

    const float left = min(x1, x2);
    const float right = max(x1, x2);
    const float top = min(y1, y2);
    const float bottom = max(y1, y2);

    if (radius > 0) {
        radius = min(radius, (right - left) * 0.5f);
        radius = min(radius, (bottom - top) * 0.5f);

        const int segments_per_corner = max(ceil(0.5f * numbers::pi_v<float> * sqrt(radius)), 3.0f);

        glColor4f(color.r, color.g, color.b, color.a);
        if (thickness > 0) {
            vector<pair<float, float>> inner_points;
            vector<pair<float, float>> outer_points;
            inner_points.reserve(segments_per_corner * 4 + 4);
            outer_points.reserve(segments_per_corner * 4 + 4);

            // top left corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = numbers::pi_v<float> + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                inner_points.emplace_back(
                    left + radius + (radius - thickness * 0.5f) * cosf(theta),
                    top + radius + (radius - thickness * 0.5f) * sinf(theta)
                );
                outer_points.emplace_back(
                    left + radius + (radius + thickness * 0.5f) * cosf(theta),
                    top + radius + (radius + thickness * 0.5f) * sinf(theta)
                );
            }
            // top right corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = (numbers::pi_v<float> * 1.5f) + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                inner_points.emplace_back(
                    right - radius + (radius - thickness * 0.5f) * cosf(theta),
                    top + radius + (radius - thickness * 0.5f) * sinf(theta)
                );
                outer_points.emplace_back(
                    right - radius + (radius + thickness * 0.5f) * cosf(theta),
                    top + radius + (radius + thickness * 0.5f) * sinf(theta)
                );
            }
            // bottom right corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = 0.0f + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                inner_points.emplace_back(
                    right - radius + (radius - thickness * 0.5f) * cosf(theta),
                    bottom - radius + (radius - thickness * 0.5f) * sinf(theta)
                );
                outer_points.emplace_back(
                    right - radius + (radius + thickness * 0.5f) * cosf(theta),
                    bottom - radius + (radius + thickness * 0.5f) * sinf(theta)
                );
            }
            // bottom left corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = (numbers::pi_v<float> * 0.5f) + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                inner_points.emplace_back(
                    left + radius + (radius - thickness * 0.5f) * cosf(theta),
                    bottom - radius + (radius - thickness * 0.5f) * sinf(theta)
                );
                outer_points.emplace_back(
                    left + radius + (radius + thickness * 0.5f) * cosf(theta),
                    bottom - radius + (radius + thickness * 0.5f) * sinf(theta)
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
            vector<pair<float, float>> points;
            points.reserve(segments_per_corner * 4 + 4);

            // top left corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = numbers::pi_v<float> + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                points.emplace_back(
                    left + radius + radius * cosf(theta),
                    top + radius + radius * sinf(theta)
                );
            }
            // top right corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = (numbers::pi_v<float> * 1.5f) + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                points.emplace_back(
                    right - radius + radius * cosf(theta),
                    top + radius + radius * sinf(theta)
                );
            }
            // bottom right corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = 0.0f + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                points.emplace_back(
                    right - radius + radius * cosf(theta),
                    bottom - radius + radius * sinf(theta)
                );
            }
            // bottom left corner
            for (int i = 0; i <= segments_per_corner; ++i) {
                float theta = (numbers::pi_v<float> * 0.5f) + (numbers::pi_v<float> * 0.5f) * static_cast<float>(i) / static_cast<float>(segments_per_corner);
                points.emplace_back(
                    left + radius + radius * cosf(theta),
                    bottom - radius + radius * sinf(theta)
                );
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

    } else {

        // ndc is normalized device coordinates (-1 to 1)
        const float left_ndc = (left / static_cast<float>(window_width_)) * 2.0f - 1.0f;
        const float right_ndc = (right / static_cast<float>(window_width_)) * 2.0f - 1.0f;
        const float top_ndc = 1.0f - (top / static_cast<float>(window_height_)) * 2.0f;
        const float bottom_ndc = 1.0f - (bottom / static_cast<float>(window_height_)) * 2.0f;

        glColor4f(color.r, color.g, color.b, color.a);
        if (thickness > 0) {
            const float max_thickness = min((right - left) * 0.5f, (bottom - top) * 0.5f);
            const float t = min(thickness, max_thickness);

            const float inner_left = left + t;
            const float inner_right = right - t;
            const float inner_top = top + t;
            const float inner_bottom = bottom - t;

            const float inner_left_ndc = (inner_left / static_cast<float>(window_width_)) * 2.0f - 1.0f;
            const float inner_right_ndc = (inner_right / static_cast<float>(window_width_)) * 2.0f - 1.0f;
            const float inner_top_ndc = 1.0f - (inner_top / static_cast<float>(window_height_)) * 2.0f;
            const float inner_bottom_ndc = 1.0f - (inner_bottom / static_cast<float>(window_height_)) * 2.0f;

            glBegin(GL_QUADS);
            glVertex2f(left_ndc, top_ndc);
            glVertex2f(right_ndc, top_ndc);
            glVertex2f(right_ndc, inner_top_ndc);
            glVertex2f(left_ndc, inner_top_ndc);
            glVertex2f(left_ndc, inner_bottom_ndc);
            glVertex2f(right_ndc, inner_bottom_ndc);
            glVertex2f(right_ndc, bottom_ndc);
            glVertex2f(left_ndc, bottom_ndc);
            glVertex2f(left_ndc, inner_top_ndc);
            glVertex2f(inner_left_ndc, inner_top_ndc);
            glVertex2f(inner_left_ndc, inner_bottom_ndc);
            glVertex2f(left_ndc, inner_bottom_ndc);
            glVertex2f(inner_right_ndc, inner_top_ndc);
            glVertex2f(right_ndc, inner_top_ndc);
            glVertex2f(right_ndc, inner_bottom_ndc);
            glVertex2f(inner_right_ndc, inner_bottom_ndc);
            glEnd();
        } else {
            glBegin(GL_QUADS);
            glVertex2f(left_ndc, top_ndc);
            glVertex2f(right_ndc, top_ndc);
            glVertex2f(right_ndc, bottom_ndc);
            glVertex2f(left_ndc, bottom_ndc);
            glEnd();
        }
    }
}


void AR::rectangle(
    const utils::ScreenCoordinate& top_left,
    const utils::ScreenCoordinate& bottom_right,
    float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    AR::rectangle(
        static_cast<float>(top_left.x),
        static_cast<float>(top_left.y),
        static_cast<float>(bottom_right.x),
        static_cast<float>(bottom_right.y),
        radius,
        thickness,
        color
    );
}


void AR::rectangle(
    const utils::Coordinate& top_left,
    const utils::Coordinate& bottom_right,
    float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::CameraCoordinate camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    utils::ScreenCoordinate top_left_screen = utils::convert_to_screen_coordinate(
        top_left,
        camera_coords,
        window_width_,
        window_height_
    );
    utils::ScreenCoordinate bottom_right_screen = utils::convert_to_screen_coordinate(
        bottom_right,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::rectangle(
        static_cast<float>(top_left_screen.x),
        static_cast<float>(top_left_screen.y),
        static_cast<float>(bottom_right_screen.x),
        static_cast<float>(bottom_right_screen.y),
        radius,
        thickness,
        color
    );
}


void AR::rectangle(
    const utils::Coordinate& top_left,
    const utils::Coordinate& bottom_right,
    const utils::CameraCoordinate& camera_coords,
    float radius,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::ScreenCoordinate top_left_screen = utils::convert_to_screen_coordinate(
        top_left,
        camera_coords,
        window_width_,
        window_height_
    );
    utils::ScreenCoordinate bottom_right_screen = utils::convert_to_screen_coordinate(
        bottom_right,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::rectangle(
        static_cast<float>(top_left_screen.x),
        static_cast<float>(top_left_screen.y),
        static_cast<float>(bottom_right_screen.x),
        static_cast<float>(bottom_right_screen.y),
        radius,
        thickness,
        color
    );
}