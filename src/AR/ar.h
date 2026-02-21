#pragma once

#include "telemetry.h"
#include "camera.h"

#include <GLFW/glfw3.h>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <unordered_map>
#include <windows.h>
#include <thread>

#include <ft2build.h>
#include FT_FREETYPE_H


class AR {
public:
    // MARK: public
    AR(const std::function<HWND()> target_window_handle_function, const bool hide_from_capture = true, const int msaa_samples = 8);
    ~AR();
    void draw_wheel_trajectory(const utils::ColorFloat& color);
    void run();

    // MARK: text
    void text(
        const std::wstring& text,
        float x,
        float y,
        float font_size,
        const utils::ColorFloat& color
    );
    void text(
        const std::wstring& text,
        const utils::ScreenCoordinates& position,
        float font_size,
        const utils::ColorFloat& color
    );
    void text(
        const std::wstring& text,
        const utils::Coordinates& position,
        float font_size,
        const utils::ColorFloat& color
    );
    void text(
        const std::wstring& text,
        const utils::Coordinates& position,
        const utils::CameraCoordinates& camera_coords,
        float font_size,
        const utils::ColorFloat& color
    );

    // MARK: line
    void line(
        const float x1,
        const float y1,
        const float x2,
        const float y2,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::ScreenCoordinates& start,
        const utils::ScreenCoordinates& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::Coordinates& start,
        const utils::Coordinates& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    void line(
        const utils::Coordinates& start,
        const utils::Coordinates& end,
        const utils::CameraCoordinates& camera_coords,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: circle
    void circle(
        const float x,
        const float y,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::ScreenCoordinates& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::Coordinates& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void circle(
        const utils::Coordinates& center,
        const utils::CameraCoordinates& camera_coords,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: rectangle
    void rectangle(
        const float x1,
        const float y1,
        const float x2,
        const float y2,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::ScreenCoordinates& top_left,
        const utils::ScreenCoordinates& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::Coordinates& top_left,
        const utils::Coordinates& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    void rectangle(
        const utils::Coordinates& top_left,
        const utils::Coordinates& bottom_right,
        const utils::CameraCoordinates& camera_coords,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: polyline
    void polyline(
        const std::vector<std::pair<float, float>>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::ScreenCoordinates>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::Coordinates>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    void polyline(
        const std::vector<utils::Coordinates>& points,
        const utils::CameraCoordinates& camera_coords,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );

private:
    // MARK: private
    void window_state_update_thread();
    bool initialize_text_renderer();
    void cleanup_text_renderer();
    bool load_glyph(std::uint32_t codepoint);
    std::uint32_t read_codepoint(const std::wstring& text, std::size_t& index) const;

    struct Glyph {
        unsigned int texture_id;
        int width;
        int height;
        int bearing_x;
        int bearing_y;
        unsigned int advance;
    };

    GLFWwindow* window_;
    std::function<HWND()> target_window_handle_function_;
    std::thread position_thread_;

    SCSTelemetry telemetry_;
    TelemetryData* telemetry_data_;

    int window_width_;
    int window_height_;

    FT_Library freetype_library_;
    FT_Face freetype_face_;
    std::unordered_map<std::uint32_t, Glyph> glyphs_;
    int text_font_pixel_size_;
    bool text_ready_;
};