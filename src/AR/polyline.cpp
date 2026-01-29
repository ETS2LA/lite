#include "AR/ar.h"
#include <numbers>

using namespace std;


void AR::polyline(
    const vector<pair<float, float>>& points,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color
) {
    if (window_width_ <= 0 || window_height_ <= 0) return;

    if (thickness > 0.0f) {
        if (rounded) {
            for (const auto& [px, py] : points) {
                AR::circle(
                    px,
                    py,
                    thickness * 0.5f,
                    -1.0f,
                    color
                );
            }

            glColor4f(color.r, color.g, color.b, color.a);
            for (size_t i = 0; i < points.size() - (closed ? 0 : 1); ++i) {
                const auto& [x1, y1] = points[i];
                const auto& [x2, y2] = points[(i + 1) % points.size()];

                float dx = x2 - x1;
                float dy = y2 - y1;
                float length = sqrtf(dx * dx + dy * dy);
                if (length == 0.0f) continue;

                float ux = dx / length;
                float uy = dy / length;

                const float half_thickness = thickness * 0.5f;

                float px = -uy * half_thickness;
                float py = ux * half_thickness;

                glBegin(GL_QUADS);
                glVertex2f(
                    ((x1 + px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y1 + py) / static_cast<float>(window_height_)) * 2.0f
                );
                glVertex2f(
                    ((x2 + px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y2 + py) / static_cast<float>(window_height_)) * 2.0f
                );
                glVertex2f(
                    ((x2 - px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y2 - py) / static_cast<float>(window_height_)) * 2.0f
                );
                glVertex2f(
                    ((x1 - px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y1 - py) / static_cast<float>(window_height_)) * 2.0f
                );
                glEnd();
            }
        } else {
            const size_t n = points.size();
            if (n < 2) return;

            const float half_thickness = thickness * 0.5f;

            auto to_ndc = [&](float x, float y) {
                float nx = (x / static_cast<float>(window_width_)) * 2.0f - 1.0f;
                float ny = 1.0f - ((y / static_cast<float>(window_height_)) * 2.0f);
                return pair<float, float>{nx, ny};
            };

            const size_t seg_count = closed ? n : (n - 1);
            vector<pair<float, float>> seg_u(max((size_t)1, seg_count));
            vector<pair<float, float>> seg_n(max((size_t)1, seg_count));
            for (size_t i = 0; i < seg_count; ++i) {
                const auto& a = points[i];
                const auto& b = points[(i + 1) % n];
                float dx = b.first - a.first;
                float dy = b.second - a.second;
                float length = sqrtf(dx * dx + dy * dy);
                float ux, uy;
                if (length == 0.0f) {
                    ux = 0.0f;
                    uy = 0.0f;
                } else {
                    ux = dx / length;
                    uy = dy / length;
                }
                seg_u[i] = {ux, uy};
                seg_n[i] = {-uy, ux};
            }

            // compute left and right offset points
            vector<pair<float, float>> left(n), right(n);
            for (size_t i = 0; i < n; ++i) {
                const auto& p = points[i];
                if (!closed && i == 0) {
                    auto [nx, ny] = seg_n[0];
                    left[i] = {p.first + nx * half_thickness, p.second + ny * half_thickness};
                    right[i] = {p.first - nx * half_thickness, p.second - ny * half_thickness};
                    continue;
                }
                if (!closed && i == n - 1) {
                    auto [nx, ny] = seg_n[n - 2];
                    left[i] = {p.first + nx * half_thickness, p.second + ny * half_thickness};
                    right[i] = {p.first - nx * half_thickness, p.second - ny * half_thickness};
                    continue;
                }

                size_t seg_prev = (i == 0) ? (seg_count - 1) : (i - 1);
                size_t seg_next = i % seg_count;

                auto [ux1, uy1] = seg_u[seg_prev];
                auto [nx1, ny1] = seg_n[seg_prev];
                auto [ux2, uy2] = seg_u[seg_next];
                auto [nx2, ny2] = seg_n[seg_next];

                float p1x = p.first + nx1 * half_thickness;
                float p1y = p.second + ny1 * half_thickness;
                float p2x = p.first + nx2 * half_thickness;
                float p2y = p.second + ny2 * half_thickness;

                float a1x = ux1;
                float a1y = uy1;
                float a2x = ux2;
                float a2y = uy2;

                float rx = p2x - p1x;
                float ry = p2y - p1y;
                float det = a1x * (-a2y) - a1y * (-a2x);

                bool used_bevel = false;
                pair<float, float> left_corner;
                pair<float, float> right_corner;

                if (fabs(det) < 1e-6f) {
                    left_corner = {p.first + (nx1 + nx2) * 0.5f * half_thickness, p.second + (ny1 + ny2) * 0.5f * half_thickness};
                    right_corner = {p.first - (nx1 + nx2) * 0.5f * half_thickness, p.second - (ny1 + ny2) * 0.5f * half_thickness};
                } else {
                    float t1 = (rx * (-a2y) - ry * (-a2x)) / det;
                    left_corner = {p1x + a1x * t1, p1y + a1y * t1};
                    right_corner = {2.0f * p.first - left_corner.first, 2.0f * p.second - left_corner.second};
                }

                left[i] = left_corner;
                right[i] = right_corner;
            }

            glColor4f(color.r, color.g, color.b, color.a);
            glBegin(GL_TRIANGLES);
            size_t last = (closed ? n : n - 1);
            for (size_t i = 0; i < last; ++i) {
                size_t i2 = (i + 1) % n;
                auto [lx1, ly1] = to_ndc(left[i].first, left[i].second);
                auto [lx2, ly2] = to_ndc(left[i2].first, left[i2].second);
                auto [rx2, ry2] = to_ndc(right[i2].first, right[i2].second);
                auto [rx1, ry1] = to_ndc(right[i].first, right[i].second);

                glVertex2f(lx1, ly1);
                glVertex2f(lx2, ly2);
                glVertex2f(rx2, ry2);

                glVertex2f(lx1, ly1);
                glVertex2f(rx2, ry2);
                glVertex2f(rx1, ry1);
            }
            glEnd();

            // add square endcaps for open polylines
            if (!closed) {
                {
                    auto [ux, uy] = seg_u[0];
                    float ex = -ux * half_thickness;
                    float ey = -uy * half_thickness;
                    auto [l0x, l0y] = to_ndc(left[0].first, left[0].second);
                    auto [r0x, r0y] = to_ndc(right[0].first, right[0].second);
                    auto [le0x, le0y] = to_ndc(left[0].first + ex, left[0].second + ey);
                    auto [re0x, re0y] = to_ndc(right[0].first + ex, right[0].second + ey);

                    glBegin(GL_TRIANGLES);
                    glVertex2f(le0x, le0y);
                    glVertex2f(l0x, l0y);
                    glVertex2f(r0x, r0y);

                    glVertex2f(le0x, le0y);
                    glVertex2f(r0x, r0y);
                    glVertex2f(re0x, re0y);
                    glEnd();
                }

                {
                    auto [ux, uy] = seg_u[seg_count - 1];
                    float ex = ux * half_thickness;
                    float ey = uy * half_thickness;
                    size_t last_i = n - 1;
                    auto [lnx, lny] = to_ndc(left[last_i].first, left[last_i].second);
                    auto [rnx, rny] = to_ndc(right[last_i].first, right[last_i].second);
                    auto [lex, ley] = to_ndc(left[last_i].first + ex, left[last_i].second + ey);
                    auto [rex, rey] = to_ndc(right[last_i].first + ex, right[last_i].second + ey);

                    glBegin(GL_TRIANGLES);
                    glVertex2f(lnx, lny);
                    glVertex2f(lex, ley);
                    glVertex2f(rnx, rny);

                    glVertex2f(lex, ley);
                    glVertex2f(rex, rey);
                    glVertex2f(rnx, rny);
                    glEnd();
                }
            }
        }
    } else {
        // simply filled polygon, thickness, closed and rounded parameters are ignored
        glColor4f(color.r, color.g, color.b, color.a);
        glBegin(GL_POLYGON);
        for (const auto& [px, py] : points) {
            glVertex2f(
                (px / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - (py / static_cast<float>(window_height_)) * 2.0f
            );
        }
        glEnd();
    }
}


void AR::polyline(
    const std::vector<utils::ScreenCoordinate>& points,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color
) {
    std::vector<std::pair<float, float>> pts;
    pts.reserve(points.size());
    for (const auto& p : points) {
        pts.emplace_back(static_cast<float>(p.x), static_cast<float>(p.y));
    }

    AR::polyline(
        pts,
        closed,
        rounded,
        thickness,
        color
    );
}


void AR::polyline(
    const std::vector<utils::Coordinate>& points,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color
) {
    utils::CameraCoordinate camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    std::vector<std::pair<float, float>> pts;
    pts.reserve(points.size());
    for (const auto& p : points) {
        utils::ScreenCoordinate screen_p = utils::convert_to_screen_coordinate(
            p,
            camera_coords,
            window_width_,
            window_height_
        );
        pts.emplace_back(static_cast<float>(screen_p.x), static_cast<float>(screen_p.y));
    }

    AR::polyline(
        pts,
        closed,
        rounded,
        thickness,
        color
    );
}


void AR::polyline(
    const std::vector<utils::Coordinate>& points,
    const utils::CameraCoordinate& camera_coords,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color
) {
    std::vector<std::pair<float, float>> pts;
    pts.reserve(points.size());
    for (const auto& p : points) {
        utils::ScreenCoordinate screen_p = utils::convert_to_screen_coordinate(
            p,
            camera_coords,
            window_width_,
            window_height_
        );
        pts.emplace_back(static_cast<float>(screen_p.x), static_cast<float>(screen_p.y));
    }

    AR::polyline(
        pts,
        closed,
        rounded,
        thickness,
        color
    );
}