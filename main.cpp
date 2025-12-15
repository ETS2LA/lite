#include "controller.h"
#include "telemetry.h"
#include "capture.h"

#include <opencv2/opencv.hpp>
#include <chrono>
#include <thread>

#include <winrt/Windows.UI.Xaml.h>
#include <winrt/Windows.Graphics.Capture.h>


double getCurrentTimeInMilliseconds() {
	return static_cast<double>(
		std::chrono::duration_cast<std::chrono::nanoseconds>(
			std::chrono::high_resolution_clock::now().time_since_epoch()
		).count() * 1e-6
	);
}

int main() {
	WindowCapture capture;
	capture.initialize();

	cv::Mat* frame;

	while (true) {
		frame = capture.get_frame();
		cv::imshow("Captured Frame", *frame);
		cv::waitKey(1);
	}

	return 0;
}