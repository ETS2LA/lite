#include "cpp-app.h"

int main() {
	if (std::filesystem::exists(PATH + "cache") == false) {
		std::filesystem::create_directory(PATH + "cache");
	}


	CustomUI::Create(L"Custom UI", 100, 100, 700, 500);

	std::cout << "Close the window to continue!" << std::endl;

	cv::Mat Frame = OpenCV::EmptyImage(500, 200, 3, 0, 0, 0);
	OpenCV::ShowImage("Close the window to continue!", Frame, false);
	OpenCV::SetWindowCaptionColor(L"Close the window to continue!", 0, 0, 0);
	OpenCV::SetWindowBorderColor(L"Close the window to continue!", 200, 0, 0);
	OpenCV::ShowImage("Close the window to continue!", Frame, true);

	PyTorch::LoadExampleModel();

	PyTorch::ExampleTensor();
	PyTorch::Initialize("Glas42", "NavigationDetectionAI", true);
	PyTorch::Loaded("NavigationDetectionAI");


	if (BUILD_TYPE == "Release") {
		system("pause");
	}
}