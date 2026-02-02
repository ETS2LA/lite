#pragma once

#define NOMINMAX

#include <opencv2/opencv.hpp>
#include <functional>
#include <windows.h>
#include <chrono>
#include <mutex>

#include <d3d11.h>
#include <dxgi1_2.h>
#include <wrl.h>


/**
 * Screen bounds structure defining the position and size of a screen.
 * @param x The x coordinate of the screen.
 * @param y The y coordinate of the screen.
 * @param width The width of the screen.
 * @param height The height of the screen.
 */
struct ScreenBounds {
    int x;
    int y;
    int width;
    int height;
};

/**
 * Window region structure defining the position of a window.
 * @param x1 The left coordinate of the window.
 * @param y1 The top coordinate of the window.
 * @param x2 The right coordinate of the window.
 * @param y2 The bottom coordinate of the window.
 */
struct WindowRegion {
    int x1;
    int y1;
    int x2;
    int y2;
};

/**
 * Capture region structure defining the screen index and coordinates.
 * @param screen_index The index of the screen to capture from.
 * @param x1 The left coordinate of the capture region.
 * @param y1 The top coordinate of the capture region.
 * @param x2 The right coordinate of the capture region.
 * @param y2 The bottom coordinate of the capture region.
 */
struct CaptureRegion {
    uint8_t screen_index;
    int x1;
    int y1;
    int x2;
    int y2;
};


class ScreenCapture {
public:
    ScreenCapture(CaptureRegion capture_region);
    ScreenCapture(std::function<HWND()> target_window_handle_function);

    void initialize();
    bool is_initialized();
    bool get_frame(cv::Mat& dst);
    ScreenBounds get_screen_bounds(uint8_t screen_index);
    uint8_t get_screen_index(int x, int y);
    WindowRegion get_window_position();
    void validate_capture_area(CaptureRegion& region);
    bool is_foreground_window() const;
    void set_capture_region(const CaptureRegion& region);
    CaptureRegion get_capture_region();

private:
    bool initialized = false;
    cv::Mat roi_;
    cv::Mat frame_buffer_;
    CaptureRegion capture_region_{0, 0, 0, 0};
    std::function<HWND()> target_window_handle_function_;

    std::mutex d3d_mutex_;
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

    void track_window();
    WindowRegion last_window_position_{0, 0, 0, 0};
    double last_track_check_time_ = 0.0;
};