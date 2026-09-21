#pragma once

#define NOMINMAX

#include "utils.h"
#include "object_detection.h"

#include <unordered_map>
#include <vector>


enum class MotionModel {
    ConstantVelocity,
    ConstantAcceleration
};

enum class MatchingMode {
    IoUAndDistance,
    DistanceOnly
};


class Tracker {
public:
    struct Object {
        float x;
        float y;
        float width;
        float height;

        float vx = 0.0f;
        float vy = 0.0f;
        float ax = 0.0f;
        float ay = 0.0f;
        bool has_velocity = false;

        float vwidth = 0.0f;
        float vheight = 0.0f;

        utils::Angles angles;
        utils::CameraCoordinates first_camera_coords;
        utils::CameraCoordinates previous_camera_coords;

        int id;

        float unseen_time_seconds = 0.0f;
        float age_seconds = 0.0f;
        float total_tracked_seconds = 0.0f;
        int total_hits = 0;

        float confidence = 0.0f;
        float confidence_sum = 0.0f;
        int confidence_hit_count = 0;
        float quality = 0.0f;
        bool is_coasting = false;

        int class_id = -1;
        int pending_class_id = -1;
        float pending_class_seconds = 0.0f;

        float accuracy = 0.0f;

        float ground_anchor_x() const { return x; }
        float ground_anchor_y() const { return y + height * 0.5f; }
    };

    struct Config {
        // fraction of the window height
        float distance_threshold_fraction = 0.2f;

        // combined IoU + distance cost or distance only matching
        MatchingMode matching_mode = MatchingMode::DistanceOnly;

        // if IoUAndDistance mode:
        float cost_iou_weight = 0.6f;
        float cost_distance_weight = 0.4f;
        float gating_radius_factor = 1.5f;
        float max_match_cost = 1.2f;

        // motion model used for predicting object positions
        MotionModel motion_model = MotionModel::ConstantVelocity;

        // base time a track may be coasted with no quality bonus.
        float base_max_unseen_time_seconds = 0.0f;
        // extra coasting time at quality = 1
        float max_unseen_time_bonus_seconds = 0.0f;
        // real match time needed to reach quality = 1
        float quality_time_for_max_seconds = 3.0f;
        // cap on total allowed unseen time regardless of quality in seconds, <0 means no hard cap
        float max_unseen_time_hard_cap_seconds = -1.0f;
        // if true, quality also factors in the average detection confidence of past hits
        bool use_confidence_weighted_quality = false;

        // if true, the tracker will include class IDs in the matching cost
        bool enable_class_tracking = true;
        // cost of matching a detection to a track with a different class ID than the tracks confirmed class ID
        float class_mismatch_cost = 0.5f;
        // time of real matches to the same new class required before the tracks confirmed class is switched over
        float class_switch_confirm_seconds = 0.5f;

        // this check compares bbox area ratios
        bool enable_size_consistency_check = true;
        // a detection is rejected if its bbox area differs from the tracks expected area by more than this ratio
        float size_consistency_max_ratio = 1.5f;

        // required confidence of a detection to register a new track
        float registration_confidence_threshold = 0.5f;
        // if true, the confidence of detections that are part of a continuation will also affect the tracks quality score
        bool continuation_hits_affect_confidence_quality = false;
    };

    explicit Tracker(const Config& config = Config());

    std::vector<Object>& update(
        const std::vector<ObjectDetection>& detections,
        const utils::CameraCoordinates& camera_coords,
        const int window_width,
        const int window_height
    );

private:
    struct Candidate {
        int object_index;
        int detection_index;
        float cost;
    };

    void apply_camera_rotation(
        std::vector<Object>& objects,
        utils::CameraCoordinates camera_coords,
        const int window_width,
        const int window_height
    );

    void predict_motion(std::vector<Object>& objects, float dt_seconds);

    float compute_max_unseen_time(const Object& obj) const;
    float compute_quality(const Object& obj) const;

    Config config_;

    utils::Timer timer_;

    std::vector<Object> objects_;
    int next_id_ = 0;
    std::vector<int> free_ids_;

    std::vector<float> predicted_x_;
    std::vector<float> predicted_y_;
    std::vector<float> predicted_w_;
    std::vector<float> predicted_h_;

    std::vector<std::pair<long long, int>> keyed_detections_;
    std::vector<long long> unique_keys_;
    std::vector<int> key_starts_;
    std::vector<unsigned char> detection_used_;
    std::unordered_map<long long, int> key_to_pos_;

    std::vector<Candidate> candidates_;
    std::vector<unsigned char> object_matched_;
};