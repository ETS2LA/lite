#include "AR/ar.h"

#define STB_EASY_FONT_IMPLEMENTATION
#include "AR/stb_easy_font.h"

using namespace std;


void AR::text(
	const string& text,
	const float x,
	const float y,
	const float size,
	const utils::ColorFloat& color
) {
	if (window_width_ <= 0 || window_height_ <= 0) return;
	if (text.empty()) return;

	const float base_height = 12.0f;
	const float target_size = (size <= 0.0f) ? base_height : size;
	const float scale = target_size / base_height;

	vector<char> buffer(text.size() * 270 + 1);
	int quad_count = stb_easy_font_print(
		x,
		y,
		const_cast<char*>(text.c_str()),
		nullptr,
		buffer.data(),
		static_cast<int>(buffer.size())
	);
	if (quad_count <= 0) return;

	glColor4f(color.r, color.g, color.b, color.a);
	glBegin(GL_QUADS);

	const float* v = reinterpret_cast<const float*>(buffer.data());
	const int vertex_count = quad_count * 4;
	for (int i = 0; i < vertex_count; ++i) {
		float vx = v[i * 4 + 0];
		float vy = v[i * 4 + 1];

		float sx = (vx - x) * scale + x;
		float sy = (vy - y) * scale + y;

		glVertex2f(
			(sx / static_cast<float>(window_width_)) * 2.0f - 1.0f,
			1.0f - (sy / static_cast<float>(window_height_)) * 2.0f
		);
	}

	glEnd();
}


void AR::text(
	const string& text,
	const utils::ScreenCoordinates& origin,
	const float size,
	const utils::ColorFloat& color
) {
	AR::text(
		text,
		static_cast<float>(origin.x),
		static_cast<float>(origin.y),
		size,
		color
	);
}


void AR::text(
	const string& text,
	const utils::Coordinates& origin,
	const float size,
	const utils::ColorFloat& color
) {
	utils::CameraCoordinates camera_coords = utils::get_6th_camera_coordinate(telemetry_data_);

	utils::ScreenCoordinates screen_coords = utils::convert_to_screen_coordinate(
		origin,
		camera_coords,
		window_width_,
		window_height_
	);

	AR::text(
		text,
		static_cast<float>(screen_coords.x),
		static_cast<float>(screen_coords.y),
		size,
		color
	);
}


void AR::text(
	const string& text,
	const utils::Coordinates& origin,
	const utils::CameraCoordinates& camera_coords,
	const float size,
	const utils::ColorFloat& color
) {
	utils::ScreenCoordinates screen_coords = utils::convert_to_screen_coordinate(
		origin,
		camera_coords,
		window_width_,
		window_height_
	);

	AR::text(
		text,
		static_cast<float>(screen_coords.x),
		static_cast<float>(screen_coords.y),
		size,
		color
	);
}