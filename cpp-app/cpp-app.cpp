#include "cpp-app.h"

int main() {
	if (std::filesystem::exists(PATH + "cache") == false) {
		std::filesystem::create_directory(PATH + "cache");
	}


	// This is just to test OpenCV
	std::cout << "Close the window to continue!" << std::endl;
	cv::utils::logging::setLogLevel(cv::utils::logging::LogLevel::LOG_LEVEL_SILENT);
	cv::Mat Frame = cv::Mat(300, 600, CV_8UC3, cv::Scalar(0, 0, 0));
	cv::imshow("Close the window to continue!", Frame);
	cv::waitKey(1);

	HWND HWND = FindWindowW(NULL, L"Close the window to continue!");
	std::uint32_t CaptionColor[3] = { 0, 0, 0 };
	std::uint32_t BorderColor[3] = { 0, 0, 255 };

	std::uint32_t ConvertedCaptionColor = (CaptionColor[0] << 16) | (CaptionColor[1] << 8) | CaptionColor[2];
	std::uint32_t ConvertedBorderColor = (BorderColor[0] << 16) | (BorderColor[1] << 8) | BorderColor[2];

	DwmSetWindowAttribute(HWND, DWMWA_CAPTION_COLOR, &ConvertedCaptionColor, sizeof(ConvertedCaptionColor));
	DwmSetWindowAttribute(HWND, DWMWA_BORDER_COLOR, &ConvertedBorderColor, sizeof(ConvertedBorderColor));

	cv::imshow("Close the window to continue!", Frame);
	cv::waitKey(0);


	UI::Initialize();

	PyTorch::ExampleTensor();
	PyTorch::Initialize("Glas42", "NavigationDetectionAI", true);

	PyTorch::Loaded("NavigationDetectionAI");


	if (BUILD_TYPE == "Release") {
		system("pause");
	}
}