#include "tracker.h"
#include <algorithm>
#include <cmath>
#include <limits>

using namespace std;


namespace {

inline float box_center_x(const cv::Rect& box) {
    return static_cast<float>(box.x) + static_cast<float>(box.width) * 0.5f;
}

inline float box_center_y(const cv::Rect& box) {
    return static_cast<float>(box.y) + static_cast<float>(box.height) * 0.5f;
}

inline float iou(float ax, float ay, float aw, float ah, float bx, float by, float bw, float bh) {
    const float a_left = ax - aw * 0.5f, a_right = ax + aw * 0.5f;
    const float a_top = ay - ah * 0.5f, a_bottom = ay + ah * 0.5f;
    const float b_left = bx - bw * 0.5f, b_right = bx + bw * 0.5f;
    const float b_top = by - bh * 0.5f, b_bottom = by + bh * 0.5f;

    const float inter_left = max(a_left, b_left);
    const float inter_top = max(a_top, b_top);
    const float inter_right = min(a_right, b_right);
    const float inter_bottom = min(a_bottom, b_bottom);

    const float inter_w = max(0.0f, inter_right - inter_left);
    const float inter_h = max(0.0f, inter_bottom - inter_top);
    const float inter_area = inter_w * inter_h;
    if (inter_area <= 0.0f) {
        return 0.0f;
    }

    const float union_area = aw * ah + bw * bh - inter_area;
    return union_area > 0.0f ? inter_area / union_area : 0.0f;
}

}


Tracker::Tracker(const Config& config): config_(config) {
    timer_.start();
}


void Tracker::apply_camera_rotation(
    vector<Object>& objects,
    utils::CameraCoordinates camera_coords,
    const int window_width,
    const int window_height
) {
    for (auto& obj : objects) {
        const utils::Angles angles = utils::convert_to_angles(
            {obj.x, obj.y, 0.0},
            window_width,
            window_height
        );

        const double azimuth_rad = utils::degrees_to_radians(static_cast<double>(angles.azimuth));
        const double elevation_rad = utils::degrees_to_radians(static_cast<double>(angles.elevation));

        const utils::Coordinates ray_prev_cam{
            tan(azimuth_rad),
            -tan(elevation_rad),
            -1.0
        };

        const utils::Coordinates ray_world = utils::rotate_vector(
            ray_prev_cam,
            {
                -obj.previous_camera_coords.pitch,
                -obj.previous_camera_coords.yaw,
                -obj.previous_camera_coords.roll
            }
        );

        utils::CameraCoordinates current_rotation_only = camera_coords;
        current_rotation_only.x = 0.0;
        current_rotation_only.y = 0.0;
        current_rotation_only.z = 0.0;

        const utils::ScreenCoordinates projected = utils::convert_to_screen_coordinate(
            ray_world,
            current_rotation_only,
            window_width,
            window_height
        );

        if (projected.distance < 0.0) {
            obj.previous_camera_coords = camera_coords;
            continue;
        }

        obj.x = static_cast<float>(projected.x);
        obj.y = static_cast<float>(projected.y);
        obj.previous_camera_coords = camera_coords;
    }
}


void Tracker::predict_motion(vector<Object>& objects, float dt_seconds) {
    predicted_x_.resize(objects.size());
    predicted_y_.resize(objects.size());
    predicted_w_.resize(objects.size());
    predicted_h_.resize(objects.size());

    for (size_t i = 0; i < objects.size(); ++i) {
        const Object& obj = objects[i];

        float dx = obj.vx * dt_seconds;
        float dy = obj.vy * dt_seconds;
        if (config_.motion_model == MotionModel::ConstantAcceleration) {
            dx += 0.5f * obj.ax * dt_seconds * dt_seconds;
            dy += 0.5f * obj.ay * dt_seconds * dt_seconds;
        }

        predicted_x_[i] = obj.x + dx;
        predicted_y_[i] = obj.y + dy;
        predicted_w_[i] = max(1.0f, obj.width + obj.vwidth * dt_seconds);
        predicted_h_[i] = max(1.0f, obj.height + obj.vheight * dt_seconds);
    }
}


float Tracker::compute_quality(const Object& obj) const {
    const float time_ratio = min(
        1.0f,
        obj.total_tracked_seconds / max(0.001f, config_.quality_time_for_max_seconds)
    );

    if (!config_.use_confidence_weighted_quality || obj.confidence_hit_count == 0) {
        return time_ratio;
    }

    const float avg_confidence = obj.confidence_sum / static_cast<float>(obj.confidence_hit_count);
    return time_ratio * avg_confidence;
}


float Tracker::compute_max_unseen_time(const Object& obj) const {
    float max_unseen = config_.base_max_unseen_time_seconds + obj.quality * config_.max_unseen_time_bonus_seconds;
    if (config_.max_unseen_time_hard_cap_seconds >= 0.0f) {
        max_unseen = min(max_unseen, config_.max_unseen_time_hard_cap_seconds);
    }
    return max_unseen;
}


vector<Tracker::Object>& Tracker::update(
    const vector<ObjectDetection>& detections,
    const utils::CameraCoordinates& camera_coords,
    const int window_width,
    const int window_height
) {
    const float dt = static_cast<float>(max(timer_.get_delta_time(), 1e-6));

    const float effective_distance_threshold = max(
        1.0f,
        config_.distance_threshold_fraction * static_cast<float>(window_height)
    );

    apply_camera_rotation(objects_, camera_coords, window_width, window_height);

    vector<float> compensated_x(objects_.size());
    vector<float> compensated_y(objects_.size());
    for (size_t i = 0; i < objects_.size(); ++i) {
        compensated_x[i] = objects_[i].x;
        compensated_y[i] = objects_[i].y;
    }

    predict_motion(objects_, dt);

    {
        vector<Object> kept;
        vector<float> kept_px, kept_py, kept_pw, kept_ph, kept_cx, kept_cy;
        kept.reserve(objects_.size());
        for (size_t i = 0; i < objects_.size(); ++i) {
            if (predicted_x_[i] < 0 || predicted_x_[i] >= window_width ||
                predicted_y_[i] < 0 || predicted_y_[i] >= window_height) {
                free_ids_.push_back(objects_[i].id);
                continue;
            }
            kept.push_back(objects_[i]);
            kept_px.push_back(predicted_x_[i]);
            kept_py.push_back(predicted_y_[i]);
            kept_pw.push_back(predicted_w_[i]);
            kept_ph.push_back(predicted_h_[i]);
            kept_cx.push_back(compensated_x[i]);
            kept_cy.push_back(compensated_y[i]);
        }
        objects_.swap(kept);
        predicted_x_.swap(kept_px);
        predicted_y_.swap(kept_py);
        predicted_w_.swap(kept_pw);
        predicted_h_.swap(kept_ph);
        compensated_x.swap(kept_cx);
        compensated_y.swap(kept_cy);
    }

    if (objects_.empty()) {
        for (const auto& det : detections) {
            if (det.confidence < config_.registration_confidence_threshold) {
                continue;
            }

            int new_id;
            if (!free_ids_.empty()) {
                new_id = free_ids_.back();
                free_ids_.pop_back();
            } else {
                new_id = next_id_++;
            }
            Object obj{};
            obj.x = box_center_x(det.box);
            obj.y = box_center_y(det.box);
            obj.width = static_cast<float>(det.box.width);
            obj.height = static_cast<float>(det.box.height);
            obj.angles = utils::convert_to_angles(
                {obj.ground_anchor_x(), obj.ground_anchor_y(), 0.0f},
                window_width,
                window_height
            );
            obj.first_camera_coords = camera_coords;
            obj.previous_camera_coords = camera_coords;
            obj.id = new_id;
            obj.class_id = det.class_id;
            obj.confidence = det.confidence;
            obj.confidence_sum = det.confidence;
            obj.confidence_hit_count = 1;
            obj.total_hits = 1;
            obj.total_tracked_seconds = dt;
            obj.age_seconds = dt;
            obj.quality = compute_quality(obj);
            objects_.push_back(obj);
        }
        return objects_;
    }

    const float cell_size = effective_distance_threshold;
    const float inv_cell_size = 1.0f / cell_size;

    auto cell_key = [](int cx, int cy) -> long long {
        return (static_cast<long long>(cx) << 32) ^ static_cast<unsigned long long>(cy);
    };
    auto cell_coord = [inv_cell_size](float v) -> int {
        return static_cast<int>(floor(v * inv_cell_size));
    };

    keyed_detections_.clear();
    keyed_detections_.reserve(detections.size());
    for (int i = 0; i < static_cast<int>(detections.size()); ++i) {
        const float cx = box_center_x(detections[i].box);
        const float cy = box_center_y(detections[i].box);
        keyed_detections_.emplace_back(cell_key(cell_coord(cx), cell_coord(cy)), i);
    }
    sort(keyed_detections_.begin(), keyed_detections_.end(), [](const auto& a, const auto& b) {
        return a.first < b.first;
    });

    unique_keys_.clear();
    key_starts_.clear();
    for (int i = 0; i < static_cast<int>(keyed_detections_.size()); ++i) {
        if (i == 0 || keyed_detections_[i].first != keyed_detections_[i - 1].first) {
            unique_keys_.push_back(keyed_detections_[i].first);
            key_starts_.push_back(i);
        }
    }

    key_to_pos_.clear();
    key_to_pos_.reserve(unique_keys_.size() * 2 + 1);
    for (int i = 0; i < static_cast<int>(unique_keys_.size()); ++i) {
        key_to_pos_[unique_keys_[i]] = i;
    }

    candidates_.clear();
    const float gating_radius = effective_distance_threshold * config_.gating_radius_factor;
    const bool use_iou = (config_.matching_mode == MatchingMode::IoUAndDistance);

    for (int oi = 0; oi < static_cast<int>(objects_.size()); ++oi) {
        const int ocx = cell_coord(predicted_x_[oi]);
        const int ocy = cell_coord(predicted_y_[oi]);
        const Object& obj = objects_[oi];

        for (int dxCell = -1; dxCell <= 1; ++dxCell) {
            for (int dyCell = -1; dyCell <= 1; ++dyCell) {
                const auto it = key_to_pos_.find(cell_key(ocx + dxCell, ocy + dyCell));
                if (it == key_to_pos_.end()) continue;

                const int pos = it->second;
                const int start = key_starts_[pos];
                const int end = (pos + 1 < static_cast<int>(key_starts_.size()))
                    ? key_starts_[pos + 1]
                    : static_cast<int>(keyed_detections_.size());

                for (int k = start; k < end; ++k) {
                    const int di = keyed_detections_[k].second;
                    const auto& det = detections[di];
                    const float det_cx = box_center_x(det.box);
                    const float det_cy = box_center_y(det.box);
                    const float det_w = static_cast<float>(det.box.width);
                    const float det_h = static_cast<float>(det.box.height);

                    if (config_.enable_size_consistency_check) {
                        const float expected_area = max(1.0f, predicted_w_[oi] * predicted_h_[oi]);
                        const float det_area = max(1.0f, det_w * det_h);
                        const float ratio = max(expected_area / det_area, det_area / expected_area);
                        if (ratio > config_.size_consistency_max_ratio) {
                            continue;
                        }
                    }

                    const float dx = det_cx - predicted_x_[oi];
                    const float dy = det_cy - predicted_y_[oi];
                    const float dist = sqrt(dx * dx + dy * dy);

                    float overlap = 0.0f;
                    if (use_iou) {
                        overlap = iou(predicted_x_[oi], predicted_y_[oi], predicted_w_[oi], predicted_h_[oi],
                                      det_cx, det_cy, det_w, det_h);
                        if (overlap <= 0.0f && dist > gating_radius) {
                            continue;
                        }
                    } else {
                        if (dist > gating_radius) {
                            continue;
                        }
                    }

                    float cost = use_iou
                        ? (config_.cost_iou_weight * (1.0f - overlap) + config_.cost_distance_weight * (dist / effective_distance_threshold))
                        : (dist / effective_distance_threshold);

                    if (config_.enable_class_tracking && obj.class_id >= 0 && det.class_id != obj.class_id) {
                        cost += config_.class_mismatch_cost;
                    }

                    if (cost > config_.max_match_cost) {
                        continue;
                    }

                    candidates_.push_back({oi, di, cost});
                }
            }
        }
    }

    sort(candidates_.begin(), candidates_.end(), [](const Candidate& a, const Candidate& b) {
        return a.cost < b.cost;
    });

    if (detection_used_.size() != detections.size()) {
        detection_used_.assign(detections.size(), 0);
    } else {
        fill(detection_used_.begin(), detection_used_.end(), 0);
    }
    object_matched_.assign(objects_.size(), 0);

    for (const auto& c : candidates_) {
        if (object_matched_[c.object_index] || detection_used_[c.detection_index]) {
            continue;
        }
        object_matched_[c.object_index] = 1;
        detection_used_[c.detection_index] = 1;

        Object& obj = objects_[c.object_index];
        const auto& det = detections[c.detection_index];
        const float det_cx = box_center_x(det.box);
        const float det_cy = box_center_y(det.box);
        const float det_w = static_cast<float>(det.box.width);
        const float det_h = static_cast<float>(det.box.height);

        const float new_vx = (det_cx - compensated_x[c.object_index]) / dt;
        const float new_vy = (det_cy - compensated_y[c.object_index]) / dt;
        if (config_.motion_model == MotionModel::ConstantAcceleration && obj.has_velocity) {
            obj.ax = (new_vx - obj.vx) / dt;
            obj.ay = (new_vy - obj.vy) / dt;
        }
        obj.vx = new_vx;
        obj.vy = new_vy;
        obj.has_velocity = true;

        obj.vwidth = (det_w - obj.width) / dt;
        obj.vheight = (det_h - obj.height) / dt;

        obj.x = det_cx;
        obj.y = det_cy;
        obj.width = det_w;
        obj.height = det_h;

        obj.unseen_time_seconds = 0.0f;
        obj.age_seconds += dt;
        obj.total_tracked_seconds += dt;
        obj.total_hits++;
        obj.confidence = det.confidence;

        if (config_.continuation_hits_affect_confidence_quality ||
            det.confidence >= config_.registration_confidence_threshold) {
            obj.confidence_sum += det.confidence;
            obj.confidence_hit_count++;
        }
        obj.is_coasting = false;

        if (config_.enable_class_tracking) {
            if (obj.class_id < 0) {
                obj.class_id = det.class_id;
            } else if (det.class_id != obj.class_id) {
                if (det.class_id == obj.pending_class_id) {
                    obj.pending_class_seconds += dt;
                } else {
                    obj.pending_class_id = det.class_id;
                    obj.pending_class_seconds = dt;
                }
                if (obj.pending_class_seconds >= config_.class_switch_confirm_seconds) {
                    obj.class_id = obj.pending_class_id;
                    obj.pending_class_id = -1;
                    obj.pending_class_seconds = 0.0f;
                }
            } else {
                obj.pending_class_id = -1;
                obj.pending_class_seconds = 0.0f;
            }
        } else {
            obj.class_id = det.class_id;
        }

        obj.quality = compute_quality(obj);
    }

    {
        vector<Object> kept;
        kept.reserve(objects_.size());
        for (int oi = 0; oi < static_cast<int>(objects_.size()); ++oi) {
            Object& obj = objects_[oi];
            if (object_matched_[oi]) {
                kept.push_back(obj);
                continue;
            }

            obj.x = predicted_x_[oi];
            obj.y = predicted_y_[oi];
            obj.width = predicted_w_[oi];
            obj.height = predicted_h_[oi];
            obj.unseen_time_seconds += dt;
            obj.age_seconds += dt;
            obj.is_coasting = true;

            if (obj.unseen_time_seconds > compute_max_unseen_time(obj)) {
                free_ids_.push_back(obj.id);
                continue;
            }
            kept.push_back(obj);
        }
        objects_.swap(kept);
    }

    for (int i = 0; i < static_cast<int>(detections.size()); ++i) {
        if (detection_used_[i]) {
            continue;
        }
        const auto& det = detections[i];
        if (det.confidence < config_.registration_confidence_threshold) {
            continue;
        }

        int new_id;
        if (!free_ids_.empty()) {
            new_id = free_ids_.back();
            free_ids_.pop_back();
        } else {
            new_id = next_id_++;
        }

        Object obj{};
        obj.x = box_center_x(det.box);
        obj.y = box_center_y(det.box);
        obj.width = static_cast<float>(det.box.width);
        obj.height = static_cast<float>(det.box.height);
        obj.angles = utils::convert_to_angles(
            {obj.ground_anchor_x(), obj.ground_anchor_y(), 0.0f},
            window_width,
            window_height
        );
        obj.first_camera_coords = camera_coords;
        obj.previous_camera_coords = camera_coords;
        obj.id = new_id;
        obj.class_id = det.class_id;
        obj.confidence = det.confidence;
        obj.confidence_sum = det.confidence;
        obj.confidence_hit_count = 1;
        obj.total_hits = 1;
        obj.total_tracked_seconds = dt;
        obj.age_seconds = dt;
        obj.quality = compute_quality(obj);
        objects_.push_back(obj);
    }

    return objects_;
}