#pragma once

#include <opencv2/opencv.hpp>

#include <d3d11.h>
#include <dxgi1_2.h>
#include <wrl.h>


class WindowCapture {
public:
	bool initialized = false;
	std::wstring window_name = L"";
	std::uint8_t display_index = 0;

	WindowCapture();
	explicit WindowCapture(const std::wstring& window_name);
	explicit WindowCapture(std::uint8_t display_index);

    void initialize();
	cv::Mat* get_frame();

private:
	bool has_frame_ = false;
	cv::Mat latest_frame_;

	HRESULT hr_ = S_OK;
	D3D_FEATURE_LEVEL feature_level_ = D3D_FEATURE_LEVEL_11_0;
	Microsoft::WRL::ComPtr<ID3D11Device> d3d_device_;
    Microsoft::WRL::ComPtr<ID3D11DeviceContext> d3d_context_;
	Microsoft::WRL::ComPtr<IDXGIDevice> dxgi_device_;
	Microsoft::WRL::ComPtr<IDXGIAdapter> adapter_;
	Microsoft::WRL::ComPtr<IDXGIOutput> output_;
	Microsoft::WRL::ComPtr<IDXGIOutput1> output1_;
    Microsoft::WRL::ComPtr<IDXGIOutputDuplication> output_duplication_;
	Microsoft::WRL::ComPtr<ID3D11Texture2D> staging_texture_;
};