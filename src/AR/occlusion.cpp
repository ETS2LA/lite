#include "AR/ar.h"

#include <ets2la_depth/depth_reader.h>

#include <algorithm>
#include <atomic>
#include <cstdio>
#include <memory>
#include <thread>
#include <mutex>

using namespace std;


namespace {

constexpr unsigned int kGlFragmentShader = 0x8B30;
constexpr unsigned int kGlVertexShader = 0x8B31;
constexpr unsigned int kGlCompileStatus = 0x8B81;
constexpr unsigned int kGlLinkStatus = 0x8B82;
constexpr unsigned int kGlInfoLogLength = 0x8B84;
constexpr unsigned int kGlTexture0 = 0x84C0;
constexpr unsigned int kGlTexture1 = 0x84C1;
constexpr unsigned int kGlR16F = 0x822D;
constexpr unsigned int kGlHalfFloat = 0x140B;
constexpr unsigned int kGlClampToEdge = 0x812F;

using GlCreateShader = unsigned int (APIENTRY*)(unsigned int type);
using GlShaderSource = void (APIENTRY*)(unsigned int shader, int count, const char* const* strings, const int* lengths);
using GlCompileShader = void (APIENTRY*)(unsigned int shader);
using GlGetShaderiv = void (APIENTRY*)(unsigned int shader, unsigned int parameter, int* values);
using GlGetShaderInfoLog = void (APIENTRY*)(unsigned int shader, int buffer_size, int* length, char* log);
using GlDeleteShader = void (APIENTRY*)(unsigned int shader);
using GlCreateProgram = unsigned int (APIENTRY*)();
using GlAttachShader = void (APIENTRY*)(unsigned int program, unsigned int shader);
using GlLinkProgram = void (APIENTRY*)(unsigned int program);
using GlGetProgramiv = void (APIENTRY*)(unsigned int program, unsigned int parameter, int* values);
using GlGetProgramInfoLog = void (APIENTRY*)(unsigned int program, int buffer_size, int* length, char* log);
using GlDeleteProgram = void (APIENTRY*)(unsigned int program);
using GlUseProgram = void (APIENTRY*)(unsigned int program);
using GlGetUniformLocation = int (APIENTRY*)(unsigned int program, const char* name);
using GlUniform1i = void (APIENTRY*)(int location, int value);
using GlUniform1f = void (APIENTRY*)(int location, float value);
using GlUniform2f = void (APIENTRY*)(int location, float value_x, float value_y);
using GlActiveTexture = void (APIENTRY*)(unsigned int texture);

const char* const kVertexShaderSource = R"(#version 120
void main() {
    gl_Position = ftransform();
    gl_FrontColor = gl_Color;
    gl_TexCoord[0] = gl_MultiTexCoord0;
})";

const char* const kFragmentShaderSource = R"(#version 120
uniform sampler2D u_glyph;
uniform sampler2D u_depth_map;
uniform int u_mode;
uniform bool u_use_glyph;
uniform float u_inverse_depth_a;
uniform float u_inverse_depth_b;
uniform vec2 u_point_a;
uniform vec2 u_point_b;
uniform vec2 u_window_size;
uniform vec2 u_framebuffer_size;

void main() {
    vec2 uv = vec2(gl_FragCoord.x / u_framebuffer_size.x, 1.0 - gl_FragCoord.y / u_framebuffer_size.y);

    float inverse_depth;
    if (u_mode == 1) {
        vec2 axis = u_point_b - u_point_a;
        float axis_length_squared = dot(axis, axis);
        float t = 0.0;
        if (axis_length_squared > 0.000001) {
            t = clamp(dot(uv * u_window_size - u_point_a, axis) / axis_length_squared, 0.0, 1.0);
        }
        inverse_depth = mix(u_inverse_depth_a, u_inverse_depth_b, t);
    } else if (u_mode == 2) {
        inverse_depth = gl_TexCoord[0].x;
    } else {
        inverse_depth = u_inverse_depth_a;
    }

    float game_depth_raw = texture2D(u_depth_map, uv).r;
    if (game_depth_raw < -0.001 && inverse_depth > 0.000001) {
        float game_depth = -game_depth_raw;
        float drawing_depth = 1.0 / inverse_depth;
        if (game_depth < drawing_depth) {
            discard;
        }
    }

    vec4 color = gl_Color;
    if (u_use_glyph) {
        color.a *= texture2D(u_glyph, gl_TexCoord[0].st).a;
    }
    gl_FragColor = color;
})";

}


struct AR::OcclusionState {
    bool failed = false;

    GlCreateShader create_shader = nullptr;
    GlShaderSource shader_source = nullptr;
    GlCompileShader compile_shader = nullptr;
    GlGetShaderiv get_shaderiv = nullptr;
    GlGetShaderInfoLog get_shader_info_log = nullptr;
    GlDeleteShader delete_shader = nullptr;
    GlCreateProgram create_program = nullptr;
    GlAttachShader attach_shader = nullptr;
    GlLinkProgram link_program = nullptr;
    GlGetProgramiv get_programiv = nullptr;
    GlGetProgramInfoLog get_program_info_log = nullptr;
    GlDeleteProgram delete_program = nullptr;
    GlUseProgram use_program = nullptr;
    GlGetUniformLocation get_uniform_location = nullptr;
    GlUniform1i uniform_1i = nullptr;
    GlUniform1f uniform_1f = nullptr;
    GlUniform2f uniform_2f = nullptr;
    GlActiveTexture active_texture = nullptr;

    unsigned int program = 0;
    unsigned int depth_texture = 0;
    int depth_texture_width = 0;
    int depth_texture_height = 0;

    int mode_location = -1;
    int use_glyph_location = -1;
    int inverse_depth_a_location = -1;
    int inverse_depth_b_location = -1;
    int point_a_location = -1;
    int point_b_location = -1;
    int window_size_location = -1;
    int framebuffer_size_location = -1;
    int depth_map_location = -1;
    int glyph_location = -1;

    thread reader_thread;
    atomic<bool> reader_running{false};
    atomic<bool> reader_stop{false};
    atomic<uint64_t> last_use_milliseconds{0};
    mutex latest_view_mutex;
    ets2la_depth::DepthView latest_view;
    bool has_latest_view = false;
    uint64_t qpc_frequency = 0;

    uint64_t uploaded_frame_index = 0;
    bool depth_available = false;
    bool depth_prepared_this_frame = false;
    bool frame_uniforms_set = false;
    bool shader_active = false;
};


AR::OcclusionScope::OcclusionScope(AR& ar, const OcclusionDepth* depth, const bool uses_glyph_texture):
active(false),
ar_(ar) {
    active = ar_.begin_occlusion(depth, uses_glyph_texture);
}


AR::OcclusionScope::~OcclusionScope() {
    if (active) {
        ar_.end_occlusion();
    }
}


float AR::inverse_depth(const utils::ScreenProjection& projection) {
    return 1.0f / max(static_cast<float>(projection.view_depth), 0.01f);
}


AR::OcclusionDepth AR::constant_depth(const utils::ScreenProjection& projection) {
    OcclusionDepth depth;
    depth.mode = OcclusionDepth::Mode::Constant;
    depth.inverse_depth_a = inverse_depth(projection);
    return depth;
}


AR::OcclusionDepth AR::segment_depth(const utils::ScreenProjection& start, const utils::ScreenProjection& end) {
    OcclusionDepth depth;
    depth.mode = OcclusionDepth::Mode::Segment;
    depth.inverse_depth_a = inverse_depth(start);
    depth.inverse_depth_b = inverse_depth(end);
    depth.point_ax = static_cast<float>(start.coordinates.x);
    depth.point_ay = static_cast<float>(start.coordinates.y);
    depth.point_bx = static_cast<float>(end.coordinates.x);
    depth.point_by = static_cast<float>(end.coordinates.y);
    return depth;
}


void AR::initialize_occlusion() {
    occlusion_state_ = new OcclusionState();
    OcclusionState& state = *occlusion_state_;

    auto load = [](const char* name) {
        return reinterpret_cast<void*>(glfwGetProcAddress(name));
    };
    state.create_shader = reinterpret_cast<GlCreateShader>(load("glCreateShader"));
    state.shader_source = reinterpret_cast<GlShaderSource>(load("glShaderSource"));
    state.compile_shader = reinterpret_cast<GlCompileShader>(load("glCompileShader"));
    state.get_shaderiv = reinterpret_cast<GlGetShaderiv>(load("glGetShaderiv"));
    state.get_shader_info_log = reinterpret_cast<GlGetShaderInfoLog>(load("glGetShaderInfoLog"));
    state.delete_shader = reinterpret_cast<GlDeleteShader>(load("glDeleteShader"));
    state.create_program = reinterpret_cast<GlCreateProgram>(load("glCreateProgram"));
    state.attach_shader = reinterpret_cast<GlAttachShader>(load("glAttachShader"));
    state.link_program = reinterpret_cast<GlLinkProgram>(load("glLinkProgram"));
    state.get_programiv = reinterpret_cast<GlGetProgramiv>(load("glGetProgramiv"));
    state.get_program_info_log = reinterpret_cast<GlGetProgramInfoLog>(load("glGetProgramInfoLog"));
    state.delete_program = reinterpret_cast<GlDeleteProgram>(load("glDeleteProgram"));
    state.use_program = reinterpret_cast<GlUseProgram>(load("glUseProgram"));
    state.get_uniform_location = reinterpret_cast<GlGetUniformLocation>(load("glGetUniformLocation"));
    state.uniform_1i = reinterpret_cast<GlUniform1i>(load("glUniform1i"));
    state.uniform_1f = reinterpret_cast<GlUniform1f>(load("glUniform1f"));
    state.uniform_2f = reinterpret_cast<GlUniform2f>(load("glUniform2f"));
    state.active_texture = reinterpret_cast<GlActiveTexture>(load("glActiveTexture"));

    if (!state.create_shader || !state.shader_source || !state.compile_shader || !state.get_shaderiv ||
        !state.get_shader_info_log || !state.delete_shader || !state.create_program || !state.attach_shader ||
        !state.link_program || !state.get_programiv || !state.get_program_info_log || !state.delete_program ||
        !state.use_program || !state.get_uniform_location || !state.uniform_1i || !state.uniform_1f ||
        !state.uniform_2f || !state.active_texture
    ) {
        fprintf(stderr, "AR occlusion disabled: OpenGL shaders are not available.\n");
        state.failed = true;
        return;
    }

    auto compile = [&state](const unsigned int type, const char* source) -> unsigned int {
        const unsigned int shader = state.create_shader(type);
        state.shader_source(shader, 1, &source, nullptr);
        state.compile_shader(shader);

        int compiled = 0;
        state.get_shaderiv(shader, kGlCompileStatus, &compiled);
        if (!compiled) {
            int log_length = 0;
            state.get_shaderiv(shader, kGlInfoLogLength, &log_length);
            string log(static_cast<size_t>(max(log_length, 1)), '\0');
            state.get_shader_info_log(shader, log_length, nullptr, log.data());
            fprintf(stderr, "AR occlusion shader failed to compile: %s\n", log.c_str());
            state.delete_shader(shader);
            return 0;
        }
        return shader;
    };

    const unsigned int vertex_shader = compile(kGlVertexShader, kVertexShaderSource);
    const unsigned int fragment_shader = compile(kGlFragmentShader, kFragmentShaderSource);
    if (vertex_shader == 0 || fragment_shader == 0) {
        if (vertex_shader != 0) state.delete_shader(vertex_shader);
        if (fragment_shader != 0) state.delete_shader(fragment_shader);
        state.failed = true;
        return;
    }

    state.program = state.create_program();
    state.attach_shader(state.program, vertex_shader);
    state.attach_shader(state.program, fragment_shader);
    state.link_program(state.program);
    state.delete_shader(vertex_shader);
    state.delete_shader(fragment_shader);

    int linked = 0;
    state.get_programiv(state.program, kGlLinkStatus, &linked);
    if (!linked) {
        int log_length = 0;
        state.get_programiv(state.program, kGlInfoLogLength, &log_length);
        string log(static_cast<size_t>(max(log_length, 1)), '\0');
        state.get_program_info_log(state.program, log_length, nullptr, log.data());
        fprintf(stderr, "AR occlusion shader failed to link: %s\n", log.c_str());
        state.delete_program(state.program);
        state.program = 0;
        state.failed = true;
        return;
    }

    auto uniform = [&state](const char* name) {
        return state.get_uniform_location(state.program, name);
    };
    state.mode_location = uniform("u_mode");
    state.use_glyph_location = uniform("u_use_glyph");
    state.inverse_depth_a_location = uniform("u_inverse_depth_a");
    state.inverse_depth_b_location = uniform("u_inverse_depth_b");
    state.point_a_location = uniform("u_point_a");
    state.point_b_location = uniform("u_point_b");
    state.window_size_location = uniform("u_window_size");
    state.framebuffer_size_location = uniform("u_framebuffer_size");
    state.depth_map_location = uniform("u_depth_map");
    state.glyph_location = uniform("u_glyph");

    glGenTextures(1, &state.depth_texture);
    state.active_texture(kGlTexture1);
    glBindTexture(GL_TEXTURE_2D, state.depth_texture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, kGlClampToEdge);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, kGlClampToEdge);
    state.active_texture(kGlTexture0);
}


void AR::cleanup_occlusion() {
    if (!occlusion_state_) {
        return;
    }
    OcclusionState& state = *occlusion_state_;

    state.reader_stop.store(true, memory_order_relaxed);
    if (state.reader_thread.joinable()) {
        state.reader_thread.join();
    }

    if (state.depth_texture != 0) {
        glDeleteTextures(1, &state.depth_texture);
    }
    if (state.program != 0 && state.delete_program) {
        state.delete_program(state.program);
    }

    delete occlusion_state_;
    occlusion_state_ = nullptr;
}


void AR::begin_occlusion_frame() {
    if (!occlusion_state_) {
        return;
    }
    occlusion_state_->depth_prepared_this_frame = false;
    occlusion_state_->frame_uniforms_set = false;
}


bool AR::update_depth_map() {
    OcclusionState& state = *occlusion_state_;
    if (state.depth_prepared_this_frame) {
        return state.depth_available;
    }
    state.depth_prepared_this_frame = true;

    state.last_use_milliseconds.store(GetTickCount64(), memory_order_relaxed);
    if (!state.reader_running.load(memory_order_acquire)) {
        if (state.reader_thread.joinable()) {
            state.reader_thread.join();
        }
        LARGE_INTEGER frequency;
        QueryPerformanceFrequency(&frequency);
        state.qpc_frequency = static_cast<uint64_t>(frequency.QuadPart);
        state.reader_stop.store(false, memory_order_relaxed);
        state.reader_running.store(true, memory_order_release);

        state.reader_thread = thread([&state]() {
            ets2la_depth::DepthReader reader;

            while (
                !state.reader_stop.load(memory_order_relaxed) &&
                GetTickCount64() - state.last_use_milliseconds.load(memory_order_relaxed) < 3000
            ) {
                ets2la_depth::DepthView received_view;
                if (reader.get_frame_view(received_view, 100)) {
                    lock_guard lock(state.latest_view_mutex);
                    state.latest_view = move(received_view);
                    state.has_latest_view = true;
                }
            }

            state.reader_running.store(false, memory_order_release);
        });
    }

    ets2la_depth::DepthView view;
    {
        lock_guard lock(state.latest_view_mutex);
        if (!state.has_latest_view) {
            state.depth_available = false;
            return false;
        }
        view = state.latest_view;
    }

    if (view.layout() != ets2la_depth::DepthLayout::Float16 ||
        view.width == 0 ||
        view.height == 0 ||
        view.stride != view.width * 2
    ) {
        state.depth_available = false;
        return false;
    }

    if (view.frame_index != state.uploaded_frame_index || !state.depth_available) {
        GLint previous_unpack_alignment = 4;
        glGetIntegerv(GL_UNPACK_ALIGNMENT, &previous_unpack_alignment);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);

        state.active_texture(kGlTexture1);
        glBindTexture(GL_TEXTURE_2D, state.depth_texture);

        const int width = static_cast<int>(view.width);
        const int height = static_cast<int>(view.height);
        if (width != state.depth_texture_width || height != state.depth_texture_height) {
            glTexImage2D(GL_TEXTURE_2D, 0, kGlR16F, width, height, 0, GL_RED, kGlHalfFloat, view.data);
            state.depth_texture_width = width;
            state.depth_texture_height = height;
        } else {
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RED, kGlHalfFloat, view.data);
        }

        state.active_texture(kGlTexture0);
        glPixelStorei(GL_UNPACK_ALIGNMENT, previous_unpack_alignment);

        if (!view.valid()) {
            state.depth_available = false;
            return false;
        }
        state.uploaded_frame_index = view.frame_index;
    }

    state.depth_available = true;
    return true;
}


bool AR::begin_occlusion(const OcclusionDepth* depth, const bool uses_glyph_texture) {
    if (!depth || !occlusion_state_ || occlusion_state_->failed) {
        return false;
    }
    OcclusionState& state = *occlusion_state_;

    if (!update_depth_map()) {
        return false;
    }

    state.use_program(state.program);
    state.shader_active = true;

    if (!state.frame_uniforms_set) {
        int framebuffer_width = 0;
        int framebuffer_height = 0;
        glfwGetFramebufferSize(window_, &framebuffer_width, &framebuffer_height);

        state.uniform_1i(state.glyph_location, 0);
        state.uniform_1i(state.depth_map_location, 1);
        state.uniform_2f(state.window_size_location, static_cast<float>(window_width_), static_cast<float>(window_height_));
        state.uniform_2f(state.framebuffer_size_location, static_cast<float>(max(framebuffer_width, 1)), static_cast<float>(max(framebuffer_height, 1)));
        state.frame_uniforms_set = true;
    }

    state.uniform_1i(state.use_glyph_location, uses_glyph_texture ? 1 : 0);
    switch (depth->mode) {
        case OcclusionDepth::Mode::Constant:
            state.uniform_1i(state.mode_location, 0);
            state.uniform_1f(state.inverse_depth_a_location, depth->inverse_depth_a);
            break;
        case OcclusionDepth::Mode::Segment:
            state.uniform_1i(state.mode_location, 1);
            state.uniform_1f(state.inverse_depth_a_location, depth->inverse_depth_a);
            state.uniform_1f(state.inverse_depth_b_location, depth->inverse_depth_b);
            state.uniform_2f(state.point_a_location, depth->point_ax, depth->point_ay);
            state.uniform_2f(state.point_b_location, depth->point_bx, depth->point_by);
            break;
        case OcclusionDepth::Mode::Vertices:
            state.uniform_1i(state.mode_location, 2);
            break;
    }

    return true;
}


void AR::end_occlusion() {
    if (!occlusion_state_ || !occlusion_state_->shader_active) {
        return;
    }
    occlusion_state_->use_program(0);
    occlusion_state_->shader_active = false;
}