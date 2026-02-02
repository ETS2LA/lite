#pragma once

#define NOMINMAX

#include "utils.h"

#include <unordered_map>
#include <vector>


class Tracker {
public:
    struct Object {
        float x;
        float y;
        utils::Angles angles;
        utils::CameraCoordinates camera_coords;
        int id;
        int unseen_count;
        float accuracy = 0.0f;
    };

    Tracker(int max_unseen_count = 3, float distance_threshold = 50.0f);
    std::vector<Object>& update(
        const std::vector<std::pair<float, float>>& detections,
        const utils::CameraCoordinates& camera_coords,
        const int window_width,
        const int window_height
    );

private:
    int max_unseen_count_;
    float distance_threshold_;

    std::vector<Object> objects_;
    int next_id_ = 0;
    std::vector<int> free_ids_;

    std::vector<std::pair<long long, int>> keyed_detections_;
    std::vector<long long> unique_keys_;
    std::vector<int> key_starts_;
    std::vector<unsigned char> detection_used_;
    std::unordered_map<long long, int> key_to_pos_;
};