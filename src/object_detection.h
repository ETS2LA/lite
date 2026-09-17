#pragma once

#include "AR/ar.h"

#include <opencv2/opencv.hpp>
#include <onnxruntime_cxx_api.h>

#include <string>
#include <vector>


struct ObjectDetection {
    cv::Rect box;
    int class_id;
    float confidence;
};

enum class ObjectDetectionDevice {
    CPU,
    DirectML
};


class ObjectDetector {
public:
    explicit ObjectDetector(
        AR *ar,
        ObjectDetectionDevice device = ObjectDetectionDevice::CPU,
        int directml_adapter = 0
    );
    std::vector<ObjectDetection> run();

    size_t window_width = 100;
    size_t window_height = 100;

private:
    std::vector<ObjectDetection> infer(const cv::Mat& frame);
    void draw(const std::vector<ObjectDetection>& detections) const;

    std::shared_ptr<DrawList> draw_list_;
    Ort::Env environment_;
    Ort::SessionOptions session_options_;
    Ort::Session session_;
    std::string input_name_;
    std::string output_name_;
    size_t input_width_ = 640;
    size_t input_height_ = 640;
    std::vector<std::string> class_names_ = {
        "car", "bus", "truck", "stoplight", "streetlamp", "sign",
        "short post", "long pole", "curved pole", "lane line", "tree trunk",
        "bridge pier", "traffic cone", "traffic delineator"
    };
};