#pragma once

#include <onnxruntime_cxx_api.h>
#include <opencv2/opencv.hpp>

#include <string>
#include <vector>

class SharedData;


/**
 * Check if the class is a vehicle.
 * @param class_id The class ID to check.
 * @return True if the class is a vehicle, false otherwise.
 */
inline bool is_vehicle(const int class_id) {
    return class_id >= 0 && class_id <= 2;
}


class ObjectDetector {
public:
    /**
     * Detection struct.
     * @param box The bounding box of the detection.
     * @param class_id The class ID of the detection.
     * @param confidence The confidence of the detection.
     */
    struct Detection {
        cv::Rect box;
        int class_id;
        float confidence;
    };

    /**
     * Detections struct.
     * @param detections The list of detections.
     * @param frame_width The width of the frame in which the detections were made.
     * @param frame_height The height of the frame in which the detections were made.
     */
    struct Detections {
        std::vector<Detection> detections;
        size_t frame_width;
        size_t frame_height;
    };

    enum class Device {
        CPU,
        DirectML
    };

    // The classes that the object detection model can detect.
    inline static const std::vector<std::string> classes = {
        "car",
        "bus",
        "truck",
        "stoplight",
        "streetlamp",
        "sign",
        "short post",
        "long pole",
        "curved pole",
        "lane line",
        "tree trunk",
        "bridge pier",
        "traffic cone",
        "traffic delineator"
    };

    /**
     * Configuration struct for the ObjectDetector.
     * @param device The type of device to run the object detection model on.
     * @param directml_adapter The index of the DirectML adapter to use, if device is DirectML.
     * @param confidence_threshold The minimum confidence of a detection to be considered valid.
     * @param same_class_nms_threshold The NMS threshold for detections of the same class.
     * @param different_class_nms_threshold The NMS threshold for detections of different classes.
     */
    struct Config{
        // the type of device to run the object detection model on
        Device device = Device::CPU;
        // the index of the DirectML adapter to use, if device is DirectML
        int directml_adapter = 0;
        // minimum confidence of a detection to be considered valid
        float confidence_threshold = 0.2f;
        // NMS thresholds for detections of the same class
        float same_class_nms_threshold = 0.3f;
        // NMS thresholds for detections of different classes
        float different_class_nms_threshold = 0.75f;
    };

    void run();
    explicit ObjectDetector(SharedData& shared_data, const Config& config = Config());

private:
    Detections infer(const cv::Mat& frame);

    Config config_;
    SharedData& shared_data_;

    Ort::Env environment_;
    Ort::SessionOptions session_options_;
    Ort::Session session_;
    std::string input_name_;
    std::string output_name_;
    size_t input_width_ = 640;
    size_t input_height_ = 640;
};