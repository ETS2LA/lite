#pragma once

#include "utils.h"

#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

class AR;

class DrawList {
public:
    explicit DrawList(std::string id);

    const std::string& id() const;
    void clear();
    void publish();

    void draw_wheel_trajectory(const utils::ColorFloat& color);
    void text(const std::wstring&, float, float, float, const utils::ColorFloat&);
    void text(const std::wstring&, const utils::ScreenCoordinates&, float, const utils::ColorFloat&);
    void text(const std::wstring&, const utils::Coordinates&, float, const utils::ColorFloat&);
    void text(const std::wstring&, const utils::Coordinates&, const utils::CameraCoordinates&, float, const utils::ColorFloat&);
    void line(float, float, float, float, float, float, const utils::ColorFloat&);
    void line(const utils::ScreenCoordinates&, const utils::ScreenCoordinates&, float, float, const utils::ColorFloat&);
    void line(const utils::Coordinates&, const utils::Coordinates&, float, float, const utils::ColorFloat&);
    void line(const utils::Coordinates&, const utils::Coordinates&, const utils::CameraCoordinates&, float, float, const utils::ColorFloat&);
    void circle(float, float, float, float, const utils::ColorFloat&);
    void circle(const utils::ScreenCoordinates&, float, float, const utils::ColorFloat&);
    void circle(const utils::Coordinates&, float, float, const utils::ColorFloat&);
    void circle(const utils::Coordinates&, const utils::CameraCoordinates&, float, float, const utils::ColorFloat&);
    void rectangle(float, float, float, float, float, float, const utils::ColorFloat&);
    void rectangle(const utils::ScreenCoordinates&, const utils::ScreenCoordinates&, float, float, const utils::ColorFloat&);
    void rectangle(const utils::Coordinates&, const utils::Coordinates&, float, float, const utils::ColorFloat&);
    void rectangle(const utils::Coordinates&, const utils::Coordinates&, const utils::CameraCoordinates&, float, float, const utils::ColorFloat&);
    void polyline(const std::vector<std::pair<float, float>>&, bool, bool, float, const utils::ColorFloat&);
    void polyline(const std::vector<utils::ScreenCoordinates>&, bool, bool, float, const utils::ColorFloat&);
    void polyline(const std::vector<utils::Coordinates>&, bool, bool, float, const utils::ColorFloat&);
    void polyline(const std::vector<utils::Coordinates>&, const utils::CameraCoordinates&, bool, bool, float, const utils::ColorFloat&);

private:
    using Command = std::function<void(AR&)>;
    void add(Command command);
    std::shared_ptr<const std::vector<Command>> snapshot() const;

    friend class AR;
    std::string id_;
    mutable std::mutex mutex_;
    std::vector<Command> building_commands_;
    std::shared_ptr<const std::vector<Command>> published_commands_;
};