#include "capture.h"

#include <opencv2/opencv.hpp>

#include <d3d11.h>
#include <dxgi1_2.h>
#include <wrl.h>


using namespace std;
using Microsoft::WRL::ComPtr;


WindowCapture::WindowCapture() {
	display_index = 0;
}

WindowCapture::WindowCapture(const wstring& window_name):
window_name(window_name) {}

WindowCapture::WindowCapture(uint8_t display_index):
display_index(display_index) {}


void WindowCapture::initialize() {
	if (initialized) {
		return;
	}

    UINT createFlags = D3D11_CREATE_DEVICE_BGRA_SUPPORT;
    hr_ = D3D11CreateDevice(
        nullptr,
		D3D_DRIVER_TYPE_HARDWARE,
		nullptr,
        createFlags,
		nullptr,
		0,
		D3D11_SDK_VERSION,
        &d3d_device_,
		&feature_level_,
		&d3d_context_
	);

	if (FAILED(hr_)) {
		cerr << "Screen Capture: D3D11CreateDevice failed: 0x" << hex << hr_ << dec << "\n";
		return;
	}

    hr_ = d3d_device_.As(&dxgi_device_);
	if (FAILED(hr_)) {
		cerr << "Screen Capture: dxgi_device.As failed: 0x" << hex << hr_ << dec << "\n";
		return;
	}
    hr_ = dxgi_device_->GetAdapter(&adapter_);
    if (FAILED(hr_)) {
		cerr << "Screen Capture: GetAdapter failed: 0x" << hex << hr_ << dec << "\n";
		return;
	}

    hr_ = adapter_->EnumOutputs(display_index, &output_);
    if (FAILED(hr_)) {
		cerr << "Screen Capture: EnumOutputs failed for index " << display_index << ": 0x" << hex << hr_ << dec << "\n";
		return;
	}
    hr_ = output_.As(&output1_);
    if (FAILED(hr_)) {
		cerr << "Screen Capture: output.As failed: 0x" << hex << hr_ << dec << "\n";
		return;
	}

    hr_ = output1_->DuplicateOutput(d3d_device_.Get(), &output_duplication_);
	if (FAILED(hr_)) {
		cerr << "Screen Capture: DuplicateOutput failed: 0x" << hex << hr_ << dec << "\n";
		return;
	}

	initialized = true;
}


cv::Mat* WindowCapture::get_frame() {
	if (!initialized) {
		initialize();
		if (!initialized) {
			return has_frame_ ? &latest_frame_ : nullptr;
		}
	}

	DXGI_OUTDUPL_FRAME_INFO frame_info;
	ComPtr<IDXGIResource> desktop_resource;

	hr_ = output_duplication_->AcquireNextFrame(1, &frame_info, &desktop_resource);

	if (hr_ == DXGI_ERROR_WAIT_TIMEOUT) {
		return has_frame_ ? &latest_frame_ : nullptr;
	}

	if (hr_ == DXGI_ERROR_ACCESS_LOST) {
		cerr << "Screen Capture: Access lost, recreating duplication" << "\n";
		output_duplication_.Reset();
		hr_ = output1_->DuplicateOutput(d3d_device_.Get(), &output_duplication_);
		initialized = SUCCEEDED(hr_);
		return has_frame_ ? &latest_frame_ : nullptr;
	}

	if (FAILED(hr_)) {
		cerr << "Screen Capture: AcquireNextFrame failed: 0x" << hex << hr_ << dec << "\n";
		return has_frame_ ? &latest_frame_ : nullptr;
	}

	ComPtr<ID3D11Texture2D> acquired_desktop_image;
	hr_ = desktop_resource.As(&acquired_desktop_image);
	if (SUCCEEDED(hr_) && acquired_desktop_image) {
		D3D11_TEXTURE2D_DESC desc;
		acquired_desktop_image->GetDesc(&desc);

		bool recreate = !staging_texture_;
		if (staging_texture_) {
			D3D11_TEXTURE2D_DESC current_desc{};
			staging_texture_->GetDesc(&current_desc);
			recreate = current_desc.Width != desc.Width || current_desc.Height != desc.Height;
		}

		if (recreate) {
			D3D11_TEXTURE2D_DESC staging_desc = desc;
			staging_desc.Usage = D3D11_USAGE_STAGING;
			staging_desc.BindFlags = 0;
			staging_desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
			staging_desc.MiscFlags = 0;

			staging_texture_.Reset();
			hr_ = d3d_device_->CreateTexture2D(&staging_desc, nullptr, &staging_texture_);
			if (FAILED(hr_)) {
				cerr << "Screen Capture: CreateTexture2D (staging) failed: 0x" << hex << hr_ << dec << "\n";
			}
			latest_frame_.create(static_cast<int>(desc.Height), static_cast<int>(desc.Width), CV_8UC4);
		}

		if (staging_texture_) {
			d3d_context_->CopyResource(staging_texture_.Get(), acquired_desktop_image.Get());

			D3D11_MAPPED_SUBRESOURCE mapped{};
            hr_ = d3d_context_->Map(staging_texture_.Get(), 0, D3D11_MAP_READ, 0, &mapped);
            if (SUCCEEDED(hr_)) {
                const UINT row_bytes = desc.Width * 4;
                if (mapped.RowPitch == row_bytes) {
                    const SIZE_T total_bytes = static_cast<SIZE_T>(row_bytes) * desc.Height;
                    std::memcpy(latest_frame_.data, mapped.pData, total_bytes);
                } else {
                    cv::Mat wrapped(
                        static_cast<int>(desc.Height),
                        static_cast<int>(desc.Width),
                        CV_8UC4,
                        mapped.pData,
                        mapped.RowPitch
                    );
                    wrapped.copyTo(latest_frame_);
                }
                d3d_context_->Unmap(staging_texture_.Get(), 0);
                has_frame_ = true;
            }
		}
	}

	output_duplication_->ReleaseFrame();

	return has_frame_ ? &latest_frame_ : nullptr;
}