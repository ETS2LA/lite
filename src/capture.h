#pragma once

#include <opencv2/opencv.hpp>
#include <optional>
#include <string>

#include <winrt/Windows.Graphics.Capture.h>
#include <winrt/Windows.Graphics.DirectX.Direct3D11.h>
#include <winrt/Windows.Foundation.h>


class WindowCapture {
public:
	std::optional<std::string> window_name;
	std::optional<std::uint8_t> display_index;

	WindowCapture(
		std::optional<std::string> window_name = std::nullopt,
		std::optional<std::uint8_t> display_index = std::nullopt
	);

    void initialize();
	cv::Mat* get_frame();

private:
	bool initialized_ = false;
	cv::Mat* latest_frame_ = nullptr;

	winrt::Windows::Graphics::DirectX::Direct3D11::IDirect3DDevice d3d_device_;
    winrt::Windows::Graphics::Capture::GraphicsCaptureItem item_{nullptr};
    winrt::Windows::Graphics::Capture::Direct3D11CaptureFramePool frame_pool_{nullptr};
    winrt::Windows::Graphics::Capture::GraphicsCaptureSession session_{nullptr};

	cv::Mat* convert_frame_to_mat(
		winrt::Windows::Graphics::Capture::Direct3D11CaptureFrame const& frame
	);
};