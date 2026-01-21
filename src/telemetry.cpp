#include "telemetry.h"

#include <algorithm>
#include <utility>

using namespace std;


SCSTelemetry::SCSTelemetry()
    : mapHandle_(nullptr), view_(&fallback_), size_(sizeof(TelemetryData)), hooked_(false),
      mapName_(L"Local\\SCSTelemetry"), mapSize_(sizeof(TelemetryData)) {
    open(mapName_, mapSize_);
}

SCSTelemetry::SCSTelemetry(const wstring &mapName, size_t mapSize)
    : mapHandle_(nullptr), view_(&fallback_), size_(sizeof(TelemetryData)), hooked_(false),
      mapName_(mapName), mapSize_(mapSize ? mapSize : sizeof(TelemetryData)) {
    open(mapName_, mapSize_);
}

SCSTelemetry::SCSTelemetry(SCSTelemetry &&other) noexcept
    : mapHandle_(other.mapHandle_), view_(other.view_), size_(other.size_), hooked_(other.hooked_) {
    other.mapHandle_ = nullptr;
    other.view_ = nullptr;
    other.size_ = 0U;
    other.hooked_ = false;
}

SCSTelemetry &SCSTelemetry::operator=(SCSTelemetry &&other) noexcept {
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

SCSTelemetry::~SCSTelemetry() {
    close();
}

bool SCSTelemetry::open(const wstring &mapName, size_t mapSize) {
    close();

    mapName_ = mapName;
    mapSize_ = mapSize ? mapSize : sizeof(TelemetryData);

    mapHandle_ = OpenFileMappingW(FILE_MAP_READ, FALSE, mapName_.c_str());
    if (!mapHandle_) {
        view_ = &fallback_;
        size_ = sizeof(TelemetryData);
        hooked_ = false;
        return true;
    }

    view_ = MapViewOfFile(mapHandle_, FILE_MAP_READ, 0, 0, mapSize_);
    if (!view_) {
        CloseHandle(mapHandle_);
        mapHandle_ = nullptr;
        view_ = &fallback_;
        size_ = sizeof(TelemetryData);
        hooked_ = false;
        return true;
    }

    size_ = mapSize_;
    hooked_ = true;
    return true;
}

void SCSTelemetry::close() {
    if (view_ && view_ != &fallback_) {
        UnmapViewOfFile(view_);
    }
    view_ = &fallback_;

    if (mapHandle_) {
        CloseHandle(mapHandle_);
        mapHandle_ = nullptr;
    }

    size_ = sizeof(TelemetryData);
    hooked_ = false;
}

bool SCSTelemetry::ensure_open() const {
    if (hooked_) return true;
    return const_cast<SCSTelemetry*>(this)->open(mapName_, mapSize_) && hooked_;
}

TelemetryData *SCSTelemetry::data() {
    ensure_open();
    return static_cast<TelemetryData *>(view_);
}

const TelemetryData *SCSTelemetry::data() const {
    ensure_open();
    return static_cast<const TelemetryData *>(view_);
}