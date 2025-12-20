#pragma once

#define NOMINMAX

#include <opencv2/opencv.hpp>

#include <d3d11.h>
#include <dxgi1_2.h>
#include <wrl.h>


struct ScreenBounds {
    int x;
    int y;
    int width;
    int height;
};

struct WindowRegion {
    int x1;
    int y1;
    int x2;
    int y2;
};

struct CaptureRegion {
    uint8_t screen_index;
    int x1;
    int y1;
    int x2;
    int y2;
};


class ScreenCapture {
public:
    bool initialized = false;
    std::wstring window_name = L"";

    ScreenCapture(CaptureRegion capture_region);
    explicit ScreenCapture(HWND target_window_handle);

    void initialize();
    cv::Mat* get_frame();

    /**
     * Get the screen position and screen size of a screen by its index.
     * @param screen_index The index of the screen to get the dimensions for.
     * @return The screen bounds structure containing x, y, width, and height.
     */
    ScreenBounds get_screen_bounds(uint8_t screen_index);

    /**
     * Get the screen index of the screen that is closest to the given coordinates.
     * @param x The x coordinate.
     * @param y The y coordinate.
     * @return The index of the screen that contains the given coordinates.
     */
    uint8_t get_screen_index(int x, int y);

    /**
     * Validate the capture area, ensuring that it is within the bounds of the screen.
     * @param region The capture region to validate and adjust if necessary.
     */
    void validate_capture_area(CaptureRegion& region);

    /**
     * Check if the target window is currently the foreground window.
     * If no target window is set, this function returns false.
     * @return True if the target window is the foreground window, false otherwise.
     */
    bool is_foreground_window() const;

    /**
     * Get the position of the target window.
     * @return The window region structure containing x1, y1, x2, and y2.
     */
    WindowRegion get_window_position();

    /**
     * Set the capture region for screen capturing.
     * @param region The new capture region to set.
     */
    void set_capture_region(const CaptureRegion& region);

private:
    bool has_frame_ = false;
    cv::Mat frame_buffer_;
    cv::Mat latest_frame_;
    CaptureRegion capture_region_{0, 0, 0, 0};
    HWND target_window_handle_ = nullptr;

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