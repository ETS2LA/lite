#include "draw_list.h"
#include "ar.h"

#include <atomic>

using namespace std;


DrawList::DrawList(string id): id_(move(id)), published_commands_(make_shared<const vector<Command>>()) {}

const string& DrawList::id() const { return id_; }

void DrawList::add(Command command) {
    lock_guard lock(mutex_);
    building_commands_.push_back(move(command));
}

void DrawList::clear() {
    lock_guard lock(mutex_);
    building_commands_.clear();
}

void DrawList::publish() {
    shared_ptr<const vector<Command>> next;
    {
        lock_guard lock(mutex_);
        next = make_shared<const vector<Command>>(move(building_commands_));
        building_commands_.clear();
    }
    atomic_store_explicit(&published_commands_, move(next), memory_order_release);
}

shared_ptr<const vector<DrawList::Command>> DrawList::snapshot() const {
    return atomic_load_explicit(&published_commands_, memory_order_acquire);
}

void DrawList::text(const wstring& text, float x, float y, float font_size, const utils::ColorFloat& color) {
    add([text, x, y, font_size, color](AR& ar) { ar.text(text, x, y, font_size, color); });
}
void DrawList::text(const wstring& text, const utils::ScreenCoordinates& position, float font_size, const utils::ColorFloat& color) {
    add([text, position, font_size, color](AR& ar) { ar.text(text, position, font_size, color); });
}
void DrawList::text(const wstring& text, const utils::Coordinates& position, float font_size, const utils::ColorFloat& color, const bool occlusion) {
    add([text, position, font_size, color, occlusion](AR& ar) { ar.text(text, position, font_size, color, occlusion); });
}
void DrawList::text(const wstring& text, const utils::Coordinates& position, const utils::CameraCoordinates& camera_coords, float font_size, const utils::ColorFloat& color, const bool occlusion) {
    add([text, position, camera_coords, font_size, color, occlusion](AR& ar) { ar.text(text, position, camera_coords, font_size, color, occlusion); });
}

void DrawList::line(float x1, float y1, float x2, float y2, float roundness, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.line(x1, y1, x2, y2, roundness, thickness, color); });
}
void DrawList::line(const utils::ScreenCoordinates& start, const utils::ScreenCoordinates& end, float roundness, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.line(start, end, roundness, thickness, color); });
}
void DrawList::line(const utils::Coordinates& start, const utils::Coordinates& end, float roundness, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.line(start, end, roundness, thickness, color, occlusion); });
}
void DrawList::line(const utils::Coordinates& start, const utils::Coordinates& end, const utils::CameraCoordinates& camera_coords, float roundness, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.line(start, end, camera_coords, roundness, thickness, color, occlusion); });
}

void DrawList::circle(float x, float y, float radius, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.circle(x, y, radius, thickness, color); });
}
void DrawList::circle(const utils::ScreenCoordinates& center, float radius, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.circle(center, radius, thickness, color); });
}
void DrawList::circle(const utils::Coordinates& center, float radius, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.circle(center, radius, thickness, color, occlusion); });
}
void DrawList::circle(const utils::Coordinates& center, const utils::CameraCoordinates& camera_coords, float radius, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.circle(center, camera_coords, radius, thickness, color, occlusion); });
}

void DrawList::rectangle(float x1, float y1, float x2, float y2, float radius, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.rectangle(x1, y1, x2, y2, radius, thickness, color); });
}
void DrawList::rectangle(const utils::ScreenCoordinates& top_left, const utils::ScreenCoordinates& bottom_right, float radius, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.rectangle(top_left, bottom_right, radius, thickness, color); });
}
void DrawList::rectangle(const utils::Coordinates& top_left, const utils::Coordinates& bottom_right, float radius, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.rectangle(top_left, bottom_right, radius, thickness, color, occlusion); });
}
void DrawList::rectangle(const utils::Coordinates& top_left, const utils::Coordinates& bottom_right, const utils::CameraCoordinates& camera_coords, float radius, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.rectangle(top_left, bottom_right, camera_coords, radius, thickness, color, occlusion); });
}

void DrawList::polyline(const vector<pair<float, float>>& points, bool closed, bool rounded, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.polyline(points, closed, rounded, thickness, color); });
}
void DrawList::polyline(const vector<utils::ScreenCoordinates>& points, bool closed, bool rounded, float thickness, const utils::ColorFloat& color) {
    add([=](AR& ar) { ar.polyline(points, closed, rounded, thickness, color); });
}
void DrawList::polyline(const vector<utils::Coordinates>& points, bool closed, bool rounded, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.polyline(points, closed, rounded, thickness, color, occlusion); });
}
void DrawList::polyline(const vector<utils::Coordinates>& points, const utils::CameraCoordinates& camera_coords, bool closed, bool rounded, float thickness, const utils::ColorFloat& color, const bool occlusion) {
    add([=](AR& ar) { ar.polyline(points, camera_coords, closed, rounded, thickness, color, occlusion); });
}