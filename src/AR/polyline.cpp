#include "AR/ar.h"

using namespace std;


void AR::polyline(
    const vector<pair<float, float>>& points,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color
) {
    AR::polyline_pixels(points, closed, rounded, thickness, color, nullptr);
}


void AR::polyline_pixels(
    const vector<pair<float, float>>& points,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color,
    const OcclusionDepth* occlusion
) {
    if (window_width_ <= 0 || window_height_ <= 0) return;

    const vector<float>* inverse_depths = nullptr;
    if (
        occlusion &&
        occlusion->mode == OcclusionDepth::Mode::Vertices &&
        occlusion->vertex_inverse_depths &&
        occlusion->vertex_inverse_depths->size() == points.size()
    ) {
        inverse_depths = occlusion->vertex_inverse_depths;
    }
    const OcclusionDepth* active_occlusion = inverse_depths ? occlusion : nullptr;

    auto set_vertex_depth = [&](const size_t point_index) {
        if (inverse_depths) {
            glTexCoord1f((*inverse_depths)[point_index]);
        }
    };

    if (thickness > 0.0f) {
        if (rounded) {
            for (size_t i = 0; i < points.size(); ++i) {
                OcclusionDepth point_depth;
                if (inverse_depths) {
                    point_depth.mode = OcclusionDepth::Mode::Constant;
                    point_depth.inverse_depth_a = (*inverse_depths)[i];
                }
                AR::circle_pixels(
                    points[i].first,
                    points[i].second,
                    thickness * 0.5f,
                    -1.0f,
                    color,
                    inverse_depths ? &point_depth : nullptr
                );
            }

            OcclusionScope occlusion_scope(*this, active_occlusion);

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

                const size_t start_index = i;
                const size_t end_index = (i + 1) % points.size();

                glBegin(GL_QUADS);
                set_vertex_depth(start_index);
                glVertex2f(
                    ((x1 + px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y1 + py) / static_cast<float>(window_height_)) * 2.0f
                );
                set_vertex_depth(end_index);
                glVertex2f(
                    ((x2 + px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y2 + py) / static_cast<float>(window_height_)) * 2.0f
                );
                glVertex2f(
                    ((x2 - px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y2 - py) / static_cast<float>(window_height_)) * 2.0f
                );
                set_vertex_depth(start_index);
                glVertex2f(
                    ((x1 - px) / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                    1.0f - ((y1 - py) / static_cast<float>(window_height_)) * 2.0f
                );
                glEnd();
            }
        } else {
            const size_t n = points.size();
            if (n < 2) return;

            OcclusionScope occlusion_scope(*this, active_occlusion);

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

                if (fabs(det) < 1e-4f) {
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

                set_vertex_depth(i);
                glVertex2f(lx1, ly1);
                set_vertex_depth(i2);
                glVertex2f(lx2, ly2);
                glVertex2f(rx2, ry2);

                set_vertex_depth(i);
                glVertex2f(lx1, ly1);
                set_vertex_depth(i2);
                glVertex2f(rx2, ry2);
                set_vertex_depth(i);
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
                    set_vertex_depth(0);
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
                    set_vertex_depth(last_i);
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
        OcclusionScope occlusion_scope(*this, active_occlusion);

        glColor4f(color.r, color.g, color.b, color.a);
        glBegin(GL_POLYGON);
        for (size_t i = 0; i < points.size(); ++i) {
            set_vertex_depth(i);
            glVertex2f(
                (points[i].first / static_cast<float>(window_width_)) * 2.0f - 1.0f,
                1.0f - (points[i].second / static_cast<float>(window_height_)) * 2.0f
            );
        }
        glEnd();
    }
}


void AR::polyline(
    const vector<utils::ScreenCoordinates>& points,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color
) {
    vector<pair<float, float>> pts;
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
    const vector<utils::Coordinates>& points,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color,
    const bool occlusion
) {
    utils::CameraCoordinates camera_coords = utils::get_6th_camera_coordinate(telemetry_);

    vector<pair<float, float>> pts;
    vector<float> inverse_depths;
    pts.reserve(points.size());
    inverse_depths.reserve(points.size());
    for (const auto& p : points) {
        utils::ScreenProjection screen_proj = utils::convert_to_screen_coordinate(
            p,
            camera_coords,
            window_width_,
            window_height_
        );
        if (screen_proj.distance < 0) {
            continue;
        }
        pts.emplace_back(
            static_cast<float>(screen_proj.coordinates.x),
            static_cast<float>(screen_proj.coordinates.y)
        );
        inverse_depths.push_back(inverse_depth(screen_proj));
    }

    OcclusionDepth depth;
    depth.mode = OcclusionDepth::Mode::Vertices;
    depth.vertex_inverse_depths = &inverse_depths;
    AR::polyline_pixels(
        pts,
        closed,
        rounded,
        thickness,
        color,
        occlusion ? &depth : nullptr
    );
}


void AR::polyline(
    const vector<utils::Coordinates>& points,
    const utils::CameraCoordinates& camera_coords,
    const bool closed,
    const bool rounded,
    const float thickness,
    const utils::ColorFloat& color,
    const bool occlusion
) {
    vector<pair<float, float>> pts;
    vector<float> inverse_depths;
    pts.reserve(points.size());
    inverse_depths.reserve(points.size());
    for (const auto& p : points) {
        utils::ScreenProjection screen_proj = utils::convert_to_screen_coordinate(
            p,
            camera_coords,
            window_width_,
            window_height_
        );
        if (screen_proj.distance < 0) {
            continue;
        }
        pts.emplace_back(
            static_cast<float>(screen_proj.coordinates.x),
            static_cast<float>(screen_proj.coordinates.y)
        );
        inverse_depths.push_back(inverse_depth(screen_proj));
    }

    OcclusionDepth depth;
    depth.mode = OcclusionDepth::Mode::Vertices;
    depth.vertex_inverse_depths = &inverse_depths;
    AR::polyline_pixels(
        pts,
        closed,
        rounded,
        thickness,
        color,
        occlusion ? &depth : nullptr
    );
}