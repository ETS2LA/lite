#include "AR/ar.h"

#include <cstdio>
#include <filesystem>
#include <vector>
#include <cstdint>

using namespace std;


bool AR::initialize_text_renderer() {
    glyphs_.clear();
    text_ready_ = false;
    freetype_library_ = nullptr;
    freetype_face_ = nullptr;

    if (FT_Init_FreeType(&freetype_library_) != 0) {
        fprintf(stderr, "Failed to initialize FreeType library.\n");
        return false;
    }

    vector<string> font_candidates = {
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf"
    };

    string font_path;
    for (const auto& candidate : font_candidates) {
        if (filesystem::exists(candidate)) {
            font_path = candidate;
            break;
        }
    }

    if (font_path.empty()) {
        fprintf(stderr, "No usable font file found for AR text rendering.\n");
        FT_Done_FreeType(freetype_library_);
        freetype_library_ = nullptr;
        return false;
    }

    if (FT_New_Face(freetype_library_, font_path.c_str(), 0, &freetype_face_) != 0) {
        fprintf(stderr, "Failed to load font file: %s\n", font_path.c_str());
        FT_Done_FreeType(freetype_library_);
        freetype_library_ = nullptr;
        return false;
    }

    FT_Set_Pixel_Sizes(freetype_face_, 0, static_cast<unsigned int>(text_font_pixel_size_));
    FT_Select_Charmap(freetype_face_, FT_ENCODING_UNICODE);

    GLint old_unpack_alignment = 4;
    glGetIntegerv(GL_UNPACK_ALIGNMENT, &old_unpack_alignment);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);

    for (std::uint32_t c = 32; c < 127; ++c) {
        load_glyph(c);
    }

    glBindTexture(GL_TEXTURE_2D, 0);
    glPixelStorei(GL_UNPACK_ALIGNMENT, old_unpack_alignment);

    text_ready_ = !glyphs_.empty();
    return text_ready_;
}


void AR::cleanup_text_renderer() {
    for (const auto& [_, glyph] : glyphs_) {
        if (glyph.texture_id != 0) {
            glDeleteTextures(1, &glyph.texture_id);
        }
    }

    glyphs_.clear();
    if (freetype_face_) {
        FT_Done_Face(freetype_face_);
        freetype_face_ = nullptr;
    }
    if (freetype_library_) {
        FT_Done_FreeType(freetype_library_);
        freetype_library_ = nullptr;
    }
    text_ready_ = false;
}


bool AR::load_glyph(std::uint32_t codepoint) {
    if (!freetype_face_ || glyphs_.find(codepoint) != glyphs_.end()) {
        return glyphs_.find(codepoint) != glyphs_.end();
    }

    if (FT_Load_Char(freetype_face_, static_cast<FT_ULong>(codepoint), FT_LOAD_RENDER) != 0) {
        return false;
    }

    Glyph glyph = {
        0,
        static_cast<int>(freetype_face_->glyph->bitmap.width),
        static_cast<int>(freetype_face_->glyph->bitmap.rows),
        static_cast<int>(freetype_face_->glyph->bitmap_left),
        static_cast<int>(freetype_face_->glyph->bitmap_top),
        static_cast<unsigned int>(freetype_face_->glyph->advance.x)
    };

    if (glyph.width > 0 && glyph.height > 0 && freetype_face_->glyph->bitmap.buffer != nullptr) {
        GLint old_unpack_alignment = 4;
        glGetIntegerv(GL_UNPACK_ALIGNMENT, &old_unpack_alignment);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);

        unsigned int texture_id = 0;
        glGenTextures(1, &texture_id);
        glBindTexture(GL_TEXTURE_2D, texture_id);
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_ALPHA,
            glyph.width,
            glyph.height,
            0,
            GL_ALPHA,
            GL_UNSIGNED_BYTE,
            freetype_face_->glyph->bitmap.buffer
        );

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

        glPixelStorei(GL_UNPACK_ALIGNMENT, old_unpack_alignment);

        glyph.texture_id = texture_id;
    }

    glyphs_.insert({ codepoint, glyph });
    return true;
}


std::uint32_t AR::read_codepoint(const std::wstring& text, std::size_t& index) const {
    const wchar_t first = text[index++];

    if (sizeof(wchar_t) == 2) {
        const std::uint32_t first_value = static_cast<std::uint32_t>(first);
        if (first_value >= 0xD800 && first_value <= 0xDBFF && index < text.size()) {
            const std::uint32_t second_value = static_cast<std::uint32_t>(text[index]);
            if (second_value >= 0xDC00 && second_value <= 0xDFFF) {
                ++index;
                return ((first_value - 0xD800) << 10) + (second_value - 0xDC00) + 0x10000;
            }
        }
    }

    return static_cast<std::uint32_t>(first);
}


void AR::text(
    const wstring& text,
    float x,
    float y,
    float font_size,
    const utils::ColorFloat& color
) {
    if (!text_ready_ || window_width_ <= 0 || window_height_ <= 0 || font_size <= 0.0f || text_font_pixel_size_ <= 0) {
        return;
    }

    const float scale = font_size / static_cast<float>(text_font_pixel_size_);

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_TEXTURE_2D);
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    glColor4f(color.r, color.g, color.b, color.a);

    const float origin_x = x;
    float cursor_x = x;
    float baseline_y = y;
    const float line_height = font_size * 1.1f;

    for (size_t i = 0; i < text.size();) {
        const std::uint32_t codepoint = read_codepoint(text, i);

        if (codepoint == L'\r') {
            continue;
        }

        if (codepoint == L'\n') {
            cursor_x = origin_x;
            baseline_y += line_height;
            continue;
        }

        if (!load_glyph(codepoint)) {
            cursor_x += font_size * 0.5f;
            continue;
        }

        auto glyph_it = glyphs_.find(codepoint);
        if (glyph_it == glyphs_.end()) {
            glyph_it = glyphs_.find(static_cast<std::uint32_t>(L'?'));
            if (glyph_it == glyphs_.end()) {
                cursor_x += font_size * 0.5f;
                continue;
            }
        }

        const Glyph& glyph = glyph_it->second;

        if (glyph.texture_id != 0 && glyph.width > 0 && glyph.height > 0) {
            const float xpos = cursor_x + static_cast<float>(glyph.bearing_x) * scale;
            const float ypos = baseline_y - static_cast<float>(glyph.bearing_y) * scale;

            const float width = static_cast<float>(glyph.width) * scale;
            const float height = static_cast<float>(glyph.height) * scale;

            const float left = (xpos / static_cast<float>(window_width_)) * 2.0f - 1.0f;
            const float right = ((xpos + width) / static_cast<float>(window_width_)) * 2.0f - 1.0f;
            const float top = 1.0f - (ypos / static_cast<float>(window_height_)) * 2.0f;
            const float bottom = 1.0f - ((ypos + height) / static_cast<float>(window_height_)) * 2.0f;

            glBindTexture(GL_TEXTURE_2D, glyph.texture_id);
            glBegin(GL_TRIANGLES);
            glTexCoord2f(0.0f, 0.0f);
            glVertex2f(left, top);
            glTexCoord2f(0.0f, 1.0f);
            glVertex2f(left, bottom);
            glTexCoord2f(1.0f, 1.0f);
            glVertex2f(right, bottom);

            glTexCoord2f(0.0f, 0.0f);
            glVertex2f(left, top);
            glTexCoord2f(1.0f, 1.0f);
            glVertex2f(right, bottom);
            glTexCoord2f(1.0f, 0.0f);
            glVertex2f(right, top);
            glEnd();
        }

        cursor_x += static_cast<float>(glyph.advance >> 6) * scale;
    }

    glBindTexture(GL_TEXTURE_2D, 0);
    glDisable(GL_TEXTURE_2D);
}


void AR::text(
    const wstring& text,
    const utils::ScreenCoordinates& position,
    float font_size,
    const utils::ColorFloat& color
) {
    AR::text(
        text,
        position.x,
        position.y,
        font_size,
        color
    );
}


void AR::text(
    const wstring& text,
    const utils::Coordinates& position,
    float font_size,
    const utils::ColorFloat& color
) {
    utils::CameraCoordinates camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

    utils::ScreenCoordinates screen_position = utils::convert_to_screen_coordinate(
        position,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::text(
        text,
        screen_position.x,
        screen_position.y,
        font_size,
        color
    );
}


void AR::text(
    const wstring& text,
    const utils::Coordinates& position,
    const utils::CameraCoordinates& camera_coords,
    float font_size,
    const utils::ColorFloat& color
) {
    utils::ScreenCoordinates screen_position = utils::convert_to_screen_coordinate(
        position,
        camera_coords,
        window_width_,
        window_height_
    );

    AR::text(
        text,
        screen_position.x,
        screen_position.y,
        font_size,
        color
    );
}