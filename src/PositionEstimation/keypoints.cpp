#include "PositionEstimation/position_estimation.h"

using namespace std;


inline int bias_towards_center(const double x, const double gamma, const double center) {
    double d = x - center;
    double sign = (d >= 0.0) ? 1.0 : -1.0;
    double dnorm = abs(d) / center;
    double compressed = pow(dnorm, gamma);
    double y = center + sign * center * compressed;
    int y_int = static_cast<int>(round(y));
    return y_int;
}


vector<pair<float, float>> PositionEstimation::get_keypoints(cv::Mat& frame) {
	vector<pair<float, float>> points;
	if (frame.empty()) {
		return points;
	}

	if (frame.channels() == 1) {
		frame_gray_ = frame;
	} else {
		cv::cvtColor(frame, frame_gray_, cv::COLOR_BGR2GRAY);
	}

    float frame_mean = cv::mean(frame_gray_)[0];
    feature_detector_->setThreshold(bias_towards_center(frame_mean * 0.4, 2.0, 50.0));

	vector<cv::KeyPoint> keypoints;
	feature_detector_->detect(frame_gray_, keypoints);

	points.reserve(keypoints.size());
	for (const auto& kp : keypoints) {
		points.emplace_back(kp.pt.x, kp.pt.y);
	}

	return points;
}


vector<pair<float, float>> PositionEstimation::get_keypoints() {
    capture_->get_frame(frame_);
    return get_keypoints(frame_);
}