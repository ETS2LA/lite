#include "object_detection.h"
#include "ets2la_capture/frame_reader.h"
#include <dml_provider_factory.h>

#include <algorithm>
#include <array>
#include <filesystem>
#include <numeric>
#include <stdexcept>


using namespace std;

namespace {

ets2la_capture::Frame capture_frame;
ets2la_capture::FrameReader reader;
cv::Mat frame;
float confidence_threshold = 0.25f;
float nms_threshold = 0.75f;


Ort::SessionOptions make_session_options(
    const ObjectDetectionDevice device,
    const int directml_adapter
) {
    Ort::SessionOptions options;
    options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_EXTENDED);
    if (device == ObjectDetectionDevice::DirectML) {
        Ort::ThrowOnError(OrtSessionOptionsAppendExecutionProvider_DML(options, directml_adapter));
    }
    return options;
}

std::filesystem::path model_path() {
    wchar_t executable_path[MAX_PATH]{};
    const DWORD length = GetModuleFileNameW(nullptr, executable_path, MAX_PATH);
    if (length == 0 || length == MAX_PATH) {
        throw std::runtime_error("Could not determine the executable path.");
    }
    return std::filesystem::path(executable_path).parent_path() / "assets" / "yolo26n_2026-09-10-22-00-00.onnx";
}

} // namespace


ObjectDetector::ObjectDetector(
    AR *ar,
    const ObjectDetectionDevice device,
    const int directml_adapter
)
    : environment_(ORT_LOGGING_LEVEL_WARNING, "ETS2LA-Lite object detection"),
            session_options_(make_session_options(device, directml_adapter)),
            session_(environment_, model_path().wstring().c_str(), session_options_) {
    draw_list_ = ar->get_draw_list("object_detection");

    Ort::AllocatorWithDefaultOptions allocator;
    input_name_ = session_.GetInputNameAllocated(0, allocator).get();
    output_name_ = session_.GetOutputNameAllocated(0, allocator).get();

    const auto input_shape = session_.GetInputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();
    if (input_shape.size() == 4 && input_shape[2] > 0 && input_shape[3] > 0) {
        input_height_ = static_cast<size_t>(input_shape[2]);
        input_width_ = static_cast<size_t>(input_shape[3]);
    }
}


std::vector<ObjectDetection> ObjectDetector::infer(const cv::Mat& frame) {
    const float scale = min(
        static_cast<float>(input_width_) / static_cast<float>(frame.cols),
        static_cast<float>(input_height_) / static_cast<float>(frame.rows)
    );
    const int resized_width = cvRound(frame.cols * scale);
    const int resized_height = cvRound(frame.rows * scale);
    const int pad_x = static_cast<int>(input_width_) - resized_width;
    const int pad_y = static_cast<int>(input_height_) - resized_height;

    cv::Mat bgr_frame;
    if (frame.channels() == 3) {
        bgr_frame = frame;
    } else if (frame.channels() == 4) {
        cv::cvtColor(frame, bgr_frame, cv::COLOR_BGRA2BGR);
    } else {
        throw std::runtime_error("Object detection requires a BGR or BGRA frame.");
    }

    cv::Mat resized;
    cv::resize(bgr_frame, resized, cv::Size(resized_width, resized_height));
    cv::Mat letterboxed(static_cast<int>(input_height_), static_cast<int>(input_width_), CV_8UC3, cv::Scalar(114, 114, 114));
    resized.copyTo(letterboxed(cv::Rect(pad_x / 2, pad_y / 2, resized_width, resized_height)));

    cv::Mat rgb;
    cv::cvtColor(letterboxed, rgb, cv::COLOR_BGR2RGB);
    rgb.convertTo(rgb, CV_32FC3, 1.0 / 255.0);

    std::vector<float> input_tensor_values(3 * input_width_ * input_height_);
    std::array<cv::Mat, 3> channels = {
        cv::Mat(static_cast<int>(input_height_), static_cast<int>(input_width_), CV_32FC1, input_tensor_values.data()),
        cv::Mat(static_cast<int>(input_height_), static_cast<int>(input_width_), CV_32FC1, input_tensor_values.data() + input_width_ * input_height_),
        cv::Mat(static_cast<int>(input_height_), static_cast<int>(input_width_), CV_32FC1, input_tensor_values.data() + 2 * input_width_ * input_height_)
    };
    cv::split(rgb, channels);

    const std::array<int64_t, 4> input_shape = {1, 3, static_cast<int64_t>(input_height_), static_cast<int64_t>(input_width_)};
    Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
        memory_info,
        input_tensor_values.data(),
        input_tensor_values.size(),
        input_shape.data(),
        input_shape.size()
    );

    const char* input_names[] = {input_name_.c_str()};
    const char* output_names[] = {output_name_.c_str()};
    auto output_tensors = session_.Run(Ort::RunOptions{nullptr}, input_names, &input_tensor, 1, output_names, 1);

    const auto tensor_info = output_tensors[0].GetTensorTypeAndShapeInfo();
    const auto output_shape = tensor_info.GetShape();
    const float* output = output_tensors[0].GetTensorData<float>();
    if (output_shape.size() != 3 || output_shape[0] != 1) {
        throw std::runtime_error("Unsupported YOLO ONNX output shape.");
    }

    const bool nms_output = output_shape[2] == 6;
    const bool channels_first = !nms_output && output_shape[1] < output_shape[2];
    const size_t attributes = static_cast<size_t>(nms_output ? 6 : (channels_first ? output_shape[1] : output_shape[2]));
    const size_t candidates = static_cast<size_t>(channels_first ? output_shape[2] : output_shape[1]);
    if (attributes < 5 || (!nms_output && attributes > class_names_.size() + 5)) {
        throw std::runtime_error("Unsupported YOLO ONNX output attributes.");
    }

    std::vector<cv::Rect> boxes;
    std::vector<float> scores;
    std::vector<int> class_ids;
    for (size_t candidate = 0; candidate < candidates; ++candidate) {
        auto value = [&](size_t attribute) {
            return channels_first ? output[attribute * candidates + candidate] : output[candidate * attributes + attribute];
        };

        float best_score = value(4);
        int best_class = static_cast<int>(value(5));
        if (!nms_output) {
            best_score = 0.0f;
            best_class = -1;
            for (size_t class_index = 0; class_index < attributes - 4; ++class_index) {
                const float score = value(class_index + 4);
                if (score > best_score) {
                    best_score = score;
                    best_class = static_cast<int>(class_index);
                }
            }
        }
        if (best_score < confidence_threshold || best_class < 0 || best_class >= static_cast<int>(class_names_.size())) {
            continue;
        }

        const float left = (value(0) - static_cast<float>(pad_x / 2)) / scale;
        const float top = (value(1) - static_cast<float>(pad_y / 2)) / scale;
        const float right = (value(2) - static_cast<float>(pad_x / 2)) / scale;
        const float bottom = (value(3) - static_cast<float>(pad_y / 2)) / scale;
        cv::Rect box(
            cvRound(left),
            cvRound(top),
            cvRound(right - left),
            cvRound(bottom - top)
        );
        box &= cv::Rect(0, 0, frame.cols, frame.rows);
        if (box.area() > 0) {
            boxes.push_back(box);
            scores.push_back(best_score);
            class_ids.push_back(best_class);
        }
    }

    std::vector<int> kept;
    for (int class_id = 0; class_id < static_cast<int>(class_names_.size()); ++class_id) {
        std::vector<cv::Rect> class_boxes;
        std::vector<float> class_scores;
        std::vector<int> class_indices;
        for (size_t index = 0; index < class_ids.size(); ++index) {
            if (class_ids[index] == class_id) {
                class_boxes.push_back(boxes[index]);
                class_scores.push_back(scores[index]);
                class_indices.push_back(static_cast<int>(index));
            }
        }

        std::vector<int> class_kept;
        cv::dnn::NMSBoxes(class_boxes, class_scores, confidence_threshold, nms_threshold, class_kept);
        for (const int index : class_kept) {
            kept.push_back(class_indices[index]);
        }
    }
    std::vector<ObjectDetection> detections;
    detections.reserve(kept.size());
    for (const int index : kept) {
        detections.push_back({boxes[index], class_ids[index], scores[index]});
    }
    return detections;
}


void ObjectDetector::draw(const std::vector<ObjectDetection>& detections) const {
    draw_list_->clear();
    for (const auto& detection : detections) {
        draw_list_->rectangle(
            static_cast<float>(detection.box.x),
            static_cast<float>(detection.box.y),
            static_cast<float>(detection.box.x + detection.box.width),
            static_cast<float>(detection.box.y + detection.box.height),
            3.0f,
            1.0f,
            utils::ColorFloat(0.0f, 1.0f, 0.0f, 1.0f)
        );
        const std::string label = format("{} {:.2f}", class_names_[detection.class_id], detection.confidence);
        const std::wstring wide_label(label.begin(), label.end());
        draw_list_->text(
            wide_label,
            static_cast<float>(detection.box.x),
            static_cast<float>(detection.box.y) - 14,
            13.0f,
            utils::ColorFloat(0.0f, 1.0f, 0.0f, 1.0f)
        );
    }
    draw_list_->publish();
}


vector<ObjectDetection> ObjectDetector::run() {
    if (!reader.ok()) {
        this_thread::sleep_for(std::chrono::milliseconds(1000));
        reader.init();
        return {};
    }
    if (!reader.get_latest_frame(capture_frame)) {
        return {};
    }
    cv::Mat frame(capture_frame.height, capture_frame.width, CV_8UC4, capture_frame.data.data());

    window_width = frame.cols;
    window_height = frame.rows;

    const auto detections = infer(frame);
    draw(detections);

    return detections;
}