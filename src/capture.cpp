#include "capture.h"

#include <opencv2/opencv.hpp>

#include <d3d11.h>
#include <dxgi1_2.h>
#include <wrl.h>


using namespace std;
using Microsoft::WRL::ComPtr;


ScreenCapture::ScreenCapture(CaptureRegion capture_region):
capture_region_(capture_region) {}

ScreenCapture::ScreenCapture(HWND target_window_handle):
target_window_handle_(target_window_handle) {}


void ScreenCapture::initialize() {
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
        fprintf(stderr, "Screen Capture: D3D11CreateDevice failed: 0x%X\n", hr_);
        return;
    }

    hr_ = d3d_device_.As(&dxgi_device_);
    if (FAILED(hr_)) {
        fprintf(stderr, "Screen Capture: dxgi_device.As failed: 0x%X\n", hr_);
        return;
    }
    hr_ = dxgi_device_->GetAdapter(&adapter_);
    if (FAILED(hr_)) {
        fprintf(stderr, "Screen Capture: GetAdapter failed: 0x%X\n", hr_);
        return;
    }

    hr_ = adapter_->EnumOutputs(capture_region_.screen_index, &output_);
    if (FAILED(hr_)) {
        fprintf(stderr, "Screen Capture: EnumOutputs failed for index %d: 0x%X\n", static_cast<int>(capture_region_.screen_index), hr_);
        return;
    }
    hr_ = output_.As(&output1_);
    if (FAILED(hr_)) {
        fprintf(stderr, "Screen Capture: output.As failed: 0x%X\n", hr_);
        return;
    }

    hr_ = output1_->DuplicateOutput(d3d_device_.Get(), &output_duplication_);
    if (FAILED(hr_)) {
        fprintf(stderr, "Screen Capture: DuplicateOutput failed: 0x%X\n", hr_);
        return;
    }

    initialized = true;

    validate_capture_area(capture_region_);
}


cv::Mat* ScreenCapture::get_frame() {
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
        fprintf(stderr, "Screen Capture: Access lost, recreating duplication\n");
        output_duplication_.Reset();
        hr_ = output1_->DuplicateOutput(d3d_device_.Get(), &output_duplication_);
        initialized = SUCCEEDED(hr_);
        return has_frame_ ? &latest_frame_ : nullptr;
    }

    if (FAILED(hr_)) {
        fprintf(stderr, "Screen Capture: AcquireNextFrame failed: 0x%X\n", hr_);
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
                fprintf(stderr, "Screen Capture: CreateTexture2D (staging) failed: 0x%X\n", hr_);
                return has_frame_ ? &latest_frame_ : nullptr;
            }
            frame_buffer_.create(static_cast<int>(desc.Height), static_cast<int>(desc.Width), CV_8UC4);
        }

        if (staging_texture_) {
            d3d_context_->CopyResource(staging_texture_.Get(), acquired_desktop_image.Get());

            D3D11_MAPPED_SUBRESOURCE mapped{};
            hr_ = d3d_context_->Map(staging_texture_.Get(), 0, D3D11_MAP_READ, 0, &mapped);
            if (SUCCEEDED(hr_)) {
                const UINT row_bytes = desc.Width * 4;
                if (mapped.RowPitch == row_bytes) {
                    const SIZE_T total_bytes = static_cast<SIZE_T>(row_bytes) * desc.Height;
                    memcpy(frame_buffer_.data, mapped.pData, total_bytes);
                } else {
                    cv::Mat wrapped(
                        static_cast<int>(desc.Height),
                        static_cast<int>(desc.Width),
                        CV_8UC4,
                        mapped.pData,
                        mapped.RowPitch
                    );
                    wrapped.copyTo(frame_buffer_);
                }

                latest_frame_ = frame_buffer_(
                    cv::Rect(
                        capture_region_.x1,
                        capture_region_.y1,
                        capture_region_.x2 - capture_region_.x1,
                        capture_region_.y2 - capture_region_.y1
                    )
                ).clone();

                d3d_context_->Unmap(staging_texture_.Get(), 0);
                has_frame_ = true;
            }
        }
    }

    output_duplication_->ReleaseFrame();

    return has_frame_ ? &latest_frame_ : nullptr;
}


ScreenBounds ScreenCapture::get_screen_bounds(uint8_t screen_index) {
    if (!initialized) {
        initialize();
        if (!initialized) {
            return ScreenBounds{0, 0, 0, 0};
        }
    }

    ComPtr<IDXGIOutput> temp_output;
    HRESULT hr = adapter_->EnumOutputs(screen_index, &temp_output);
    if (FAILED(hr)) {
        fprintf(stderr, "Screen Capture: EnumOutputs failed for index %d: 0x%X\n", static_cast<int>(screen_index), hr);
        return ScreenBounds{0, 0, 0, 0};
    }

    DXGI_OUTPUT_DESC output_desc;
    hr = temp_output->GetDesc(&output_desc);
    if (FAILED(hr)) {
        fprintf(stderr, "Screen Capture: GetDesc failed for output index %d: 0x%X\n", static_cast<int>(screen_index), hr);
        return ScreenBounds{0, 0, 0, 0};
    }

    RECT desktop_rect = output_desc.DesktopCoordinates;
    ScreenBounds bounds;
    bounds.x = desktop_rect.left;
    bounds.y = desktop_rect.top;
    bounds.width = desktop_rect.right - desktop_rect.left;
    bounds.height = desktop_rect.bottom - desktop_rect.top;

    return bounds;
}


uint8_t ScreenCapture::get_screen_index(int x, int y) {
    if (!initialized) {
        initialize();
        if (!initialized) {
            return 0;
        }
    }

    uint8_t screen_index = 0;
    int closest_distance = INT_MAX;

    ComPtr<IDXGIOutput> temp_output;
    for (uint8_t i = 0; adapter_->EnumOutputs(i, &temp_output) != DXGI_ERROR_NOT_FOUND; ++i) {
        DXGI_OUTPUT_DESC output_desc;
        HRESULT hr = temp_output->GetDesc(&output_desc);
        if (FAILED(hr)) {
            fprintf(stderr, "Screen Capture: GetDesc failed for output index %d: 0x%X\n", static_cast<int>(i), hr);
            continue;
        }

        RECT desktop_rect = output_desc.DesktopCoordinates;
        int center_x = (desktop_rect.left + desktop_rect.right) / 2;
        int center_y = (desktop_rect.top + desktop_rect.bottom) / 2;

        int delta_x = center_x - x;
        int delta_y = center_y - y;
        int distance = delta_x * delta_x + delta_y * delta_y;

        if (distance < closest_distance) {
            closest_distance = distance;
            screen_index = i;
        }
    }

    return screen_index;
}


void ScreenCapture::validate_capture_area(CaptureRegion& region) {
    ScreenBounds bounds = get_screen_bounds(region.screen_index);

    if (region.x1 > region.x2) {
        region.x2 = region.x1 + 1;
    }

    if (region.y1 > region.y2) {
        region.y2 = region.y1 + 1;
    }

    region.x1 = max(0, min(region.x1, bounds.width - 1));
    region.y1 = max(0, min(region.y1, bounds.height - 1));
    region.x2 = max(0, min(region.x2, bounds.width - 1));
    region.y2 = max(0, min(region.y2, bounds.height - 1));

    if (region.x1 == region.x2) {
        if (region.x1 == 0) {
            region.x2 = bounds.width - 1;
        } else {
            region.x1 = 0;
        }
    }
    if (region.y1 == region.y2) {
        if (region.y1 == 0) {
            region.y2 = bounds.height - 1;
        } else {
            region.y1 = 0;
        }
    }
}


bool ScreenCapture::is_foreground_window() const {
    if (target_window_handle_ == nullptr) {
        return false;
    }

    HWND foreground_window = GetForegroundWindow();
    return foreground_window == target_window_handle_;
}


WindowRegion ScreenCapture::get_window_position() {
    WindowRegion region{0, 0, 0, 0};

    if (target_window_handle_ == nullptr) {
        return region;
    }

    RECT rect;
    if (GetWindowRect(target_window_handle_, &rect)) {
        region.x1 = rect.left;
        region.y1 = rect.top;
        region.x2 = rect.right;
        region.y2 = rect.bottom;
    }

    return region;
}