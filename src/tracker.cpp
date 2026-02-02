#include "tracker.h"
#include <algorithm>
#include <cmath>
#include <limits>

using namespace std;


Tracker::Tracker(int max_unseen_count, float distance_threshold):
max_unseen_count_(max_unseen_count), distance_threshold_(distance_threshold) {}


/**
 * Update the tracker with new detections.
 * @param detections A vector of detected object positions.
 * @return A reference to the vector of tracked objects.
 */
std::vector<Tracker::Object>& Tracker::update(
    const std::vector<std::pair<float, float>>& detections,
    const utils::CameraCoordinates& camera_coords,
    const int window_width,
    const int window_height
) {
    if (detections.empty()) {
        for (auto& obj : objects_) {
            obj.unseen_count++;
        }
        objects_.erase(std::remove_if(objects_.begin(), objects_.end(), [&](const Object& obj) {
            if (obj.unseen_count > max_unseen_count_) {
                free_ids_.push_back(obj.id);
                return true;
            }
            return false;
        }), objects_.end());
        return objects_;
    }

    if (objects_.empty()) {
        objects_.reserve(detections.size());
        for (int i = 0; i < static_cast<int>(detections.size()); ++i) {
            int new_id;
            if (!free_ids_.empty()) {
                new_id = free_ids_.back();
                free_ids_.pop_back();
            } else {
                new_id = next_id_++;
            }
            Object obj{};
            obj.x = detections[i].first;
            obj.y = detections[i].second;
            obj.angles = utils::convert_to_angles(
                {obj.x, obj.y, 0.0f},
                window_width,
                window_height
            );
            obj.camera_coords = camera_coords;
            obj.id = new_id;
            obj.unseen_count = 0;
            objects_.push_back(obj);
        }
        return objects_;
    }

    const float cell_size = distance_threshold_;
    const float max_dist_sq = distance_threshold_ * distance_threshold_;
    const float inv_cell_size = 1.0f / cell_size;

    auto cell_key = [](int cx, int cy) -> long long {
        return (static_cast<long long>(cx) << 32) ^ static_cast<unsigned long long>(cy);
    };

    auto cell_coord = [inv_cell_size](float v) -> int {
        return static_cast<int>(std::floor(v * inv_cell_size));
    };

    keyed_detections_.clear();
    keyed_detections_.reserve(detections.size());

    for (int i = 0; i < static_cast<int>(detections.size()); ++i) {
        const int cx = cell_coord(detections[i].first);
        const int cy = cell_coord(detections[i].second);
        keyed_detections_.emplace_back(cell_key(cx, cy), i);
    }

    std::sort(keyed_detections_.begin(), keyed_detections_.end(), [](const auto& a, const auto& b) {
        return a.first < b.first;
    });

    unique_keys_.clear();
    key_starts_.clear();
    unique_keys_.reserve(keyed_detections_.size());
    key_starts_.reserve(keyed_detections_.size());

    for (int i = 0; i < static_cast<int>(keyed_detections_.size()); ++i) {
        if (i == 0 || keyed_detections_[i].first != keyed_detections_[i - 1].first) {
            unique_keys_.push_back(keyed_detections_[i].first);
            key_starts_.push_back(i);
        }
    }

    if (detection_used_.size() != detections.size()) {
        detection_used_.assign(detections.size(), 0);
    } else {
        std::fill(detection_used_.begin(), detection_used_.end(), 0);
    }

    key_to_pos_.clear();
    key_to_pos_.reserve(unique_keys_.size() * 2 + 1);
    for (int i = 0; i < static_cast<int>(unique_keys_.size()); ++i) {
        key_to_pos_[unique_keys_[i]] = i;
    }

    for (auto& obj : objects_) {
        const int ocx = cell_coord(obj.x);
        const int ocy = cell_coord(obj.y);

        float best_dist_sq = std::numeric_limits<float>::max();
        int best_idx = -1;

        for (int dx = -1; dx <= 1; ++dx) {
            for (int dy = -1; dy <= 1; ++dy) {
                const long long key = cell_key(ocx + dx, ocy + dy);
                auto it = key_to_pos_.find(key);
                if (it == key_to_pos_.end()) {
                    continue;
                }
                const int pos = it->second;
                const int start = key_starts_[pos];
                const int end = (pos + 1 < static_cast<int>(key_starts_.size()))
                    ? key_starts_[pos + 1]
                    : static_cast<int>(keyed_detections_.size());

                for (int k = start; k < end; ++k) {
                    const int idx = keyed_detections_[k].second;
                    if (detection_used_[idx]) {
                        continue;
                    }
                    const float dxp = detections[idx].first - obj.x;
                    const float dyp = detections[idx].second - obj.y;
                    const float dist_sq = dxp * dxp + dyp * dyp;
                    if (dist_sq < best_dist_sq) {
                        best_dist_sq = dist_sq;
                        best_idx = idx;
                    }
                }
            }
        }

        if (best_idx != -1 && best_dist_sq <= max_dist_sq) {
            detection_used_[best_idx] = 1;
            obj.x = detections[best_idx].first;
            obj.y = detections[best_idx].second;
            obj.unseen_count = 0;
        } else {
            obj.unseen_count++;
        }
    }

    objects_.erase(std::remove_if(objects_.begin(), objects_.end(), [&](const Object& obj) {
        if (obj.unseen_count > max_unseen_count_) {
            free_ids_.push_back(obj.id);
            return true;
        }
        return false;
    }), objects_.end());

    for (int i = 0; i < static_cast<int>(detections.size()); ++i) {
        if (detection_used_[i]) {
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
        obj.x = detections[i].first;
        obj.y = detections[i].second;
        obj.angles = utils::convert_to_angles(
            {obj.x, obj.y, 0.0f},
            window_width,
            window_height
        );
        obj.camera_coords = camera_coords;
        obj.id = new_id;
        obj.unseen_count = 0;
        objects_.push_back(obj);
    }

    return objects_;
}