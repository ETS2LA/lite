#include "capture.h"

#include <opencv2/opencv.hpp>

#include <d3d11.h>
#include <dxgi1_2.h>
#include <wrl.h>


using namespace std;
using Microsoft::WRL::ComPtr;


/**
 * Constructor for ScreenCapture using a specified capture region.
 * @param capture_region The region of the screen to capture.
 */
ScreenCapture::ScreenCapture(CaptureRegion capture_region):
capture_region_(capture_region) {}

/**
 * Constructor for ScreenCapture using a function to get the target window handle.
 * @param target_window_handle_function A function that returns the handle of the target window.
 */
ScreenCapture::ScreenCapture(function<HWND()> target_window_handle_function):
target_window_handle_function_(target_window_handle_function) {
    ScreenBounds screen_bounds = get_screen_bounds(0);
    capture_region_ = {0, screen_bounds.x, screen_bounds.y, screen_bounds.width, screen_bounds.height};
}


/**
 * Initialize the screen capture resources.
 * This function will be automatically called when get_frame() is invoked for the first time, but can also be called manually if needed.
 */
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


/**
 * Check if the ScreenCapture has been initialized.
 * @return True if initialized, false otherwise.
 */
bool ScreenCapture::is_initialized() {
    return initialized;
}


/**
 * Get the latest captured frame.
 * @param dst The destination cv::Mat to store the captured frame.
 * @return True if a frame was successfully captured, false otherwise.
*/
bool ScreenCapture::get_frame(cv::Mat& dst) {
    if (!initialized) {
        initialize();
        if (!initialized) {
            return false;
        }
    }

    if (target_window_handle_function_ != nullptr) {
        track_window();
    }

    scoped_lock lock(d3d_mutex_);

    DXGI_OUTDUPL_FRAME_INFO frame_info;
    ComPtr<IDXGIResource> desktop_resource;

    hr_ = output_duplication_->AcquireNextFrame(1, &frame_info, &desktop_resource);

    if (hr_ == DXGI_ERROR_WAIT_TIMEOUT) {
        return false;
    }

    if (hr_ == DXGI_ERROR_ACCESS_LOST) {
        fprintf(stderr, "Screen Capture: Access lost, recreating duplication\n");
        output_duplication_.Reset();
        hr_ = output1_->DuplicateOutput(d3d_device_.Get(), &output_duplication_);
        initialized = SUCCEEDED(hr_);
        return false;
    }

    if (FAILED(hr_)) {
        fprintf(stderr, "Screen Capture: AcquireNextFrame failed: 0x%X\n", hr_);
        return false;
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
                return false;
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

                roi_ = frame_buffer_(
                    cv::Rect(
                        capture_region_.x1,
                        capture_region_.y1,
                        capture_region_.x2 - capture_region_.x1,
                        capture_region_.y2 - capture_region_.y1
                    )
                );
                roi_.copyTo(dst);

                d3d_context_->Unmap(staging_texture_.Get(), 0);
            }
        }
    }

    output_duplication_->ReleaseFrame();

    return true;
}


/**
 * Get the screen position and screen size of a screen by its index.
 * @param screen_index The index of the screen to get the dimensions for.
 * @return The screen bounds structure containing x, y, width, and height.
 */
ScreenBounds ScreenCapture::get_screen_bounds(uint8_t screen_index) {
    vector<MONITORINFOEXW> monitors;
    EnumDisplayMonitors(
        nullptr,
        nullptr,
        [](HMONITOR hMon, HDC, LPRECT, LPARAM data) -> BOOL {
            auto vec = reinterpret_cast<vector<MONITORINFOEXW>*>(data);
            MONITORINFOEXW info{};
            info.cbSize = sizeof(info);
            if (GetMonitorInfoW(hMon, &info)) {
                vec->push_back(info);
            }
            return TRUE;
        },
        reinterpret_cast<LPARAM>(&monitors)
    );

    if (screen_index >= monitors.size()) {
        return ScreenBounds{0, 0, 0, 0};
    }

    const RECT& r = monitors[screen_index].rcMonitor;
    return ScreenBounds{r.left, r.top, r.right - r.left, r.bottom - r.top};
}


/**
 * Get the screen index of the screen that is closest to the given coordinates.
 * @param x The x coordinate.
 * @param y The y coordinate.
 * @return The index of the screen that contains the given coordinates.
 */
uint8_t ScreenCapture::get_screen_index(int x, int y) {
    vector<MONITORINFOEXW> monitors;
    EnumDisplayMonitors(
        nullptr,
        nullptr,
        [](HMONITOR hMon, HDC, LPRECT, LPARAM data) -> BOOL {
            auto vec = reinterpret_cast<vector<MONITORINFOEXW>*>(data);
            MONITORINFOEXW info{};
            info.cbSize = sizeof(info);
            if (GetMonitorInfoW(hMon, &info)) {
                vec->push_back(info);
            }
            return TRUE;
        },
        reinterpret_cast<LPARAM>(&monitors)
    );

    if (monitors.empty()) {
        return 0;
    }

    uint8_t best_index = 0;
    long long best_dist = LLONG_MAX;

    for (uint8_t i = 0; i < monitors.size(); ++i) {
        const RECT& r = monitors[i].rcMonitor;
        const long cx = (r.left + r.right) / 2;
        const long cy = (r.top + r.bottom) / 2;
        const long dx = cx - x;
        const long dy = cy - y;
        const long long d2 = 1LL * dx * dx + 1LL * dy * dy;
        if (d2 < best_dist) {
            best_dist = d2;
            best_index = i;
        }
    }

    return best_index;
}


/**
 * Get the position of the target window.
 * @return The window region structure containing x1, y1, x2, and y2.
 */
WindowRegion ScreenCapture::get_window_position() {
    WindowRegion region{0, 0, 0, 0};

    if (target_window_handle_function_ == nullptr) {
        return region;
    }

    HWND hwnd = target_window_handle_function_();

    RECT client_rect;
    if (!GetClientRect(hwnd, &client_rect)) {
        return region;
    }

    POINT top_left{client_rect.left, client_rect.top};
    POINT bottom_right{client_rect.right, client_rect.bottom};
    if (!ClientToScreen(hwnd, &top_left) || !ClientToScreen(hwnd, &bottom_right)) {
        return region;
    }

    region.x1 = top_left.x;
    region.y1 = top_left.y;
    region.x2 = bottom_right.x;
    region.y2 = bottom_right.y;

    return region;
}


/**
 * Validate the capture area, ensuring that it is within the bounds of the screen.
 * @param region The capture region to validate and adjust if necessary.
 */
void ScreenCapture::validate_capture_area(CaptureRegion& region) {
    ScreenBounds bounds = get_screen_bounds(region.screen_index);

    if (region.x1 > region.x2) {
        region.x2 = region.x1 + 1;
    }

    if (region.y1 > region.y2) {
        region.y2 = region.y1 + 1;
    }

    region.x1 = max(0, min(region.x1, bounds.width));
    region.y1 = max(0, min(region.y1, bounds.height));
    region.x2 = max(0, min(region.x2, bounds.width));
    region.y2 = max(0, min(region.y2, bounds.height));

    if (region.x1 == region.x2) {
        if (region.x1 == 0) {
            region.x2 = bounds.width;
        } else {
            region.x1 = 0;
        }
    }
    if (region.y1 == region.y2) {
        if (region.y1 == 0) {
            region.y2 = bounds.height;
        } else {
            region.y1 = 0;
        }
    }
}


/**
 * Check if the target window is currently the foreground window.
 * If no target window is set, this function returns false.
 * @return True if the target window is the foreground window, false otherwise.
 */
bool ScreenCapture::is_foreground_window() const {
    if (target_window_handle_function_ == nullptr) {
        return false;
    }

    HWND foreground_window = GetForegroundWindow();
    return foreground_window == target_window_handle_function_();
}


/**
 * Set the capture region for screen capturing.
 * @param region The new capture region to set.
 */
void ScreenCapture::set_capture_region(const CaptureRegion& region) {
    capture_region_ = region;
    validate_capture_area(capture_region_);

    output_duplication_.Reset();
    output1_.Reset();
    output_.Reset();

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
}


/**
 * Get the current capture region.
 * @return The current CaptureRegion structure.
 */
CaptureRegion ScreenCapture::get_capture_region() {
    return capture_region_;
}


/**
 * Track the target window and update the capture region if the window position has changed.
 */
void ScreenCapture::track_window() {
    auto now = chrono::high_resolution_clock::now();
    auto now_ms = chrono::time_point_cast<chrono::microseconds>(now);
    double current_time = now_ms.time_since_epoch().count() / 1e6;

    if (current_time - last_track_check_time_ < 0.2) {
        return;
    }
    last_track_check_time_ = current_time;

    auto window_position = ScreenCapture::get_window_position();

    if (window_position.x1 != last_window_position_.x1 ||
        window_position.y1 != last_window_position_.y1 ||
        window_position.x2 != last_window_position_.x2 ||
        window_position.y2 != last_window_position_.y2) {
        last_window_position_ = window_position;

        auto screen_index = ScreenCapture::get_screen_index(
            window_position.x1 + (window_position.x2 - window_position.x1) / 2,
            window_position.y1 + (window_position.y2 - window_position.y1) / 2
        );

        auto screen_bounds = ScreenCapture::get_screen_bounds(screen_index);

        capture_region_.screen_index = screen_index;
        capture_region_.x1 = window_position.x1 - screen_bounds.x;
        capture_region_.y1 = window_position.y1 - screen_bounds.y;
        capture_region_.x2 = window_position.x2 - screen_bounds.x;
        capture_region_.y2 = window_position.y2 - screen_bounds.y;
        set_capture_region(capture_region_);
    }
}