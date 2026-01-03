#include "camera.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <numbers>
#include <utility>

using namespace std;


struct RawCameraData {
    float fov;
    float x;
    float y;
    float z;
    int16_t cx;
    int16_t cz;
    float qw;
    float qx;
    float qy;
    float qz;
};

void quaternion_to_euler(const RawCameraData& raw, float& pitch, float& yaw, float& roll) {
	const float w = raw.qw;
	const float x = raw.qy;
	const float y = raw.qx;
	const float z = raw.qz;

    yaw = -utils::radians_to_degrees(atan2(2.0 * (y * z + w * x), w * w - x * x - y * y + z * z));
    pitch = -utils::radians_to_degrees(asin(-2.0 * (x * z - w * y)));
    roll = -utils::radians_to_degrees(atan2(2.0 * (x * y + w * z), w * w + x * x - y * y - z * z));
}

CameraData convert_data(const RawCameraData& raw) {
	CameraData out;
	out.fov = raw.fov;
	out.position.x = static_cast<double>(raw.x + raw.cx * 512);
	out.position.y = static_cast<double>(raw.y);
	out.position.z = static_cast<double>(raw.z + raw.cz * 512);
	quaternion_to_euler(raw, out.position.pitch, out.position.yaw, out.position.roll);
	return out;
}


SCSCamera::SCSCamera()
	: mapHandle_(nullptr), view_(&fallback_), size_(36U), hooked_(false),
	  mapName_(L"Local\\ETS2LACameraProps"), mapSize_(36U) {
	open(mapName_, mapSize_);
}

SCSCamera::SCSCamera(const wstring& mapName, size_t mapSize)
	: mapHandle_(nullptr), view_(&fallback_), size_(36U), hooked_(false),
	  mapName_(mapName), mapSize_(mapSize ? mapSize : 36U) {
	open(mapName_, mapSize_);
}

SCSCamera::SCSCamera(SCSCamera&& other) noexcept
	: mapHandle_(other.mapHandle_), view_(other.view_), size_(other.size_), hooked_(other.hooked_) {
    other.mapHandle_ = nullptr;
    other.view_ = nullptr;
    other.size_ = 0U;
    other.hooked_ = false;
}

SCSCamera& SCSCamera::operator=(SCSCamera&& other) noexcept {
	if (this != &other) {
        close();
        mapHandle_ = other.mapHandle_;
        view_ = other.view_;
        size_ = other.size_;
        hooked_ = other.hooked_;

        other.mapHandle_ = nullptr;
        other.view_ = nullptr;
        other.size_ = 0U;
        other.hooked_ = false;
    }
    return *this;
}

SCSCamera::~SCSCamera() {
	close();
}

bool SCSCamera::open(const wstring& mapName, size_t mapSize) {
	close();

	mapName_ = mapName;
	mapSize_ = mapSize ? mapSize : 36U;

	mapHandle_ = OpenFileMappingW(FILE_MAP_READ, FALSE, mapName_.c_str());
	if (!mapHandle_) {
		view_ = &fallback_;
		size_ = 36U;
		hooked_ = false;
		return true;
	}

	view_ = MapViewOfFile(mapHandle_, FILE_MAP_READ, 0, 0, mapSize_);
	if (!view_) {
		CloseHandle(mapHandle_);
		mapHandle_ = nullptr;
		view_ = &fallback_;
		size_ = 36U;
		hooked_ = false;
		return true;
	}

	size_ = mapSize_;
	hooked_ = true;
	return true;
}

void SCSCamera::close() {
	if (view_ && view_ != &fallback_) {
		UnmapViewOfFile(view_);
	}
	view_ = &fallback_;

	if (mapHandle_) {
		CloseHandle(mapHandle_);
		mapHandle_ = nullptr;
	}

	size_ = 36U;
	hooked_ = false;
}

bool SCSCamera::ensure_open() const {
	if (hooked_) return true;
	return const_cast<SCSCamera*>(this)->open(mapName_, mapSize_) && hooked_;
}

CameraData* SCSCamera::data() {
	ensure_open();

	RawCameraData raw{};
	memcpy(&raw, view_, size_ ? size_ : 36U);
	fallback_ = convert_data(raw);
    return &fallback_;
}