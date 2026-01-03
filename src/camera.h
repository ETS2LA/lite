#pragma once

#include <array>
#include <cstddef>
#include <string>

#include "utils.h"


/**
 * CameraData structure.
 * @param fov Field of view in degrees.
 * @param position Camera position and rotation (pitch, yaw, roll).
 */
struct CameraData {
    float fov;
    utils::CameraCoordinate position;
};


class SCSCamera {
public:
    SCSCamera();
    explicit SCSCamera(const std::wstring& mapName, std::size_t mapSize = 36U);
    SCSCamera(const SCSCamera&) = delete;
    SCSCamera& operator=(const SCSCamera&) = delete;
    SCSCamera(SCSCamera&& other) noexcept;
    SCSCamera& operator=(SCSCamera&& other) noexcept;
    ~SCSCamera();

    bool open(const std::wstring& mapName = L"Local\\ETS2LACameraProps", std::size_t mapSize = 36U);
    void close();

    bool hooked() const { return hooked_; }
    std::size_t size() const { return size_; }

    CameraData* data();
    const CameraData* data() const;

private:
    bool ensure_open() const;

    HANDLE mapHandle_;
    void* view_;
    std::size_t size_;
    bool hooked_;
    std::wstring mapName_;
    std::size_t mapSize_;
    CameraData fallback_{};
};