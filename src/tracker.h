#pragma once

#define NOMINMAX

#include "ObjectDetection/object_detection.h"
#include "utils.h"

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
    /**
     * Object structure representing a tracked object.
     * @param x X coordinate of the object's center.
     * @param y Y coordinate of the object's center.
     * @param width Width of the object's bounding box.
     * @param height Height of the object's bounding box.
     * @param vx Velocity in the X direction.
     * @param vy Velocity in the Y direction.
     * @param ax Acceleration in the X direction.
     * @param ay Acceleration in the Y direction.
     * @param has_velocity Flag indicating if the object has velocity information.
     * @param vwidth Velocity of the width change.
     * @param vheight Velocity of the height change.
     * @param angles_left Angles representing the left side of the object.
     * @param angles_right Angles representing the right side of the object.
     * @param angles_center Angles representing the center of the object.
     * @param first_camera_coords Camera coordinates when the object was first detected.
     * @param previous_camera_coords Camera coordinates from the previous frame.
     * @param id Unique identifier for the object.
     * @param unseen_time_seconds Time since the object was last seen.
     * @param age_seconds Total time the object has been tracked.
     * @param total_tracked_seconds Total time the object has been successfully tracked.
     * @param total_hits Total number of successful detections for the object.
     * @param confidence Confidence score of the object's detection.
     * @param confidence_sum Sum of confidence scores for averaging.
     * @param confidence_hit_count Count of successful detections for averaging confidence.
     * @param quality Quality score of the object based on tracking performance.
     * @param is_coasting Flag indicating if the object is currently being coasting (not detected).
     * @param class_id Class ID of the object.
     * @param pending_class_id Class ID that is pending confirmation for the object.
     * @param pending_class_seconds Time spent with the pending class ID before confirmation.
     * @param accuracy Accuracy score of the object's position estimation.
     * @param center_x Returns the X coordinate of the object's center.
     * @param left_x Returns the X coordinate of the left edge of the object's bounding box.
     * @param right_x Returns the X coordinate of the right edge of the object's bounding box.
     * @param half_left_x Returns the X coordinate of the left half of the object's bounding box.
     * @param half_right_x Returns the X coordinate of the right half of the object's bounding box.
     * @param bottom_y Returns the Y coordinate of the bottom edge of the object's bounding box.
     */
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

        utils::Angles angles_left;
        utils::Angles angles_right;
        utils::Angles angles_center;
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

        float center_x() const { return x; }
        float left_x() const { return x - width * 0.5f; }
        float right_x() const { return x + width * 0.5f; }
        float half_left_x() const { return x - width * 0.25f; }
        float half_right_x() const { return x + width * 0.25f; }
        float bottom_y() const { return y + height * 0.5f; }
    };

    /**
     * Configuration structure for the Tracker class.
     * @param distance_threshold_fraction Fraction of the window height used for distance thresholding.
     * @param matching_mode Matching mode for object association.
     * @param cost_iou_weight Weight for IoU in the matching cost calculation.
     * @param cost_distance_weight Weight for distance in the matching cost calculation.
     * @param gating_radius_factor Factor for gating radius in the matching process.
     * @param max_match_cost Maximum allowed cost for matching objects.
     * @param motion_model Motion model used for predicting object positions.
     * @param velocity_smoothing_seconds Time constant of the smoothing of the pixel velocity of a track, 0 means no smoothing.
     * @param base_max_unseen_time_seconds Base time a track may be coasted with no quality bonus.
     * @param max_unseen_time_bonus_seconds Extra coasting time at quality = 1.
     * @param quality_time_for_max_seconds Real match time needed to reach quality = 1.
     * @param max_unseen_time_hard_cap_seconds Cap on total allowed unseen time regardless of quality in seconds, <0 means no hard cap.
     * @param use_confidence_weighted_quality If true, quality also factors in the average detection confidence of past hits.
     * @param enable_class_tracking If true, the tracker will include class IDs in the matching cost.
     * @param class_mismatch_cost Cost of matching a detection to a track with a different class ID than the tracks confirmed class ID.
     * @param class_switch_confirm_seconds Time of real matches to the same new class required before the tracks confirmed class is switched over.
     * @param enable_class_groups If true (and class tracking is on), classes of the same general group (for example car, bus and truck are all "vehicle") count as the same class: no matching cost and no confirm time, the track simply takes the class of the latest detection.
     * @param enable_size_consistency_check If true, the tracker will check for size consistency between detections and tracks.
     * @param size_consistency_max_ratio A detection is rejected if its bbox area differs from the tracks expected area by more than this ratio.
     * @param registration_confidence_threshold Required confidence of a detection to register a new track.
     * @param continuation_hits_affect_confidence_quality If true, the confidence of detections that are part of a continuation will also affect the tracks quality score.
     */
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
        // time constant of the smoothing of the pixel velocity of a track (0 = no smoothing, the velocity of the last frame)
        float velocity_smoothing_seconds = 0.1f;

        // base time a track may be coasted with no quality bonus.
        float base_max_unseen_time_seconds = 0.15f;
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
        // if true (and class tracking is true), classes of the same general group count as the same class, no matching cost and no confirm time
        bool enable_class_groups = true;
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

    /**
     * Updates the tracker and returns the list of tracked objects.
     * @param detections The list of all detections from the object detector.
     * @param camera_coords The current camera coordinates.
     * @param window_width The width of the window in which the detections were made.
     * @param window_height The height of the window in which the detections were made.
     * @param dt_seconds The frame time delta in seconds.
     */
    std::vector<Object>& update(
        const std::vector<ObjectDetector::Detection> detections,
        const utils::CameraCoordinates& camera_coords,
        const int window_width,
        const int window_height,
        const float dt_seconds
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

    bool same_tracking_class(int class_id_a, int class_id_b) const;

    float compute_max_unseen_time(const Object& obj) const;
    float compute_quality(const Object& obj) const;

    Config config_;

    utils::Timer timer_;

    std::vector<Object> objects_;

    int next_id_ = 0;

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