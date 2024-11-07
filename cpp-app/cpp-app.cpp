#include "cpp-app.h"

#include <opencv2/opencv.hpp>
#include <opencv2/core/utils/logger.hpp>

int main() {
	if (std::filesystem::exists(PATH + "cache") == false) {
		std::filesystem::create_directory(PATH + "cache");
	}

	// This is just to test OpenCV
	std::cout << "Close the window to continue!" << std::endl;
	cv::utils::logging::setLogLevel(cv::utils::logging::LogLevel::LOG_LEVEL_SILENT);
	cv::Mat Frame = cv::Mat(300, 600, CV_8UC3, cv::Scalar(0, 0, 0));
	cv::imshow("Close the window to continue!", Frame);
	cv::waitKey(0);

	UI::Initialize();

	PyTorch::ExampleTensor();
	PyTorch::Initialize("Glas42", "NavigationDetectionAI", true);

	if (BUILD_TYPE == "Release") {
		system("pause");
	}
}