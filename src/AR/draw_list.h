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
    // MARK: public
    /**
     * Create a draw list for a plugin.
     * @param id Unique identifier for the plugin.
     */
    explicit DrawList(std::string id);

    /**
     * Get the plugin identifier for this draw list.
     * @return The plugin identifier.
     */
    const std::string& id() const;

    /**
     * Remove every queued drawing command.
     */
    void clear();

    /**
     * Publish all queued commands for rendering.
     */
    void publish();

    /**
     * Draw the wheel trajectory.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void draw_wheel_trajectory(const utils::ColorFloat& color);

    // MARK: text
    /**
     * Draw text at pixel coordinates.
     * @param text Text to draw.
     * @param x Horizontal position in pixels.
     * @param y Vertical position in pixels.
     * @param font_size Font size in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void text(
        const std::wstring& text,
        float x,
        float y,
        float font_size,
        const utils::ColorFloat& color
    );
    /**
     * Draw text at a screen coordinate.
     * @param text Text to draw.
     * @param position Screen coordinate.
     * @param font_size Font size in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void text(
        const std::wstring& text,
        const utils::ScreenCoordinates& position,
        float font_size,
        const utils::ColorFloat& color
    );
    /**
     * Draw text at a world coordinate using the latest telemetry camera.
     * @param text Text to draw.
     * @param position World coordinate.
     * @param font_size Font size in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void text(
        const std::wstring& text,
        const utils::Coordinates& position,
        float font_size,
        const utils::ColorFloat& color
    );
    /**
     * Draw text at a world coordinate using a given camera.
     * @param text Text to draw.
     * @param position World coordinate.
     * @param camera_coords Camera position and rotation.
     * @param font_size Font size in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void text(
        const std::wstring& text,
        const utils::Coordinates& position,
        const utils::CameraCoordinates& camera_coords,
        float font_size,
        const utils::ColorFloat& color
    );

    // MARK: line
    /**
     * Draw a line between pixel positions.
     * @param x1 Horizontal position of the first endpoint in pixels.
     * @param y1 Vertical position of the first endpoint in pixels.
     * @param x2 Horizontal position of the second endpoint in pixels.
     * @param y2 Vertical position of the second endpoint in pixels.
     * @param roundness Roundness of the line in pixels.
     * @param thickness Line thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void line(
        const float x1,
        const float y1,
        const float x2,
        const float y2,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a line between screen coordinates.
     * @param start First endpoint.
     * @param end Second endpoint.
     * @param roundness Roundness of the line in pixels.
     * @param thickness Line thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void line(
        const utils::ScreenCoordinates& start,
        const utils::ScreenCoordinates& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a line between world coordinates using the latest telemetry camera.
     * @param start First world endpoint.
     * @param end Second world endpoint.
     * @param roundness Roundness of the line in pixels.
     * @param thickness Line thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void line(
        const utils::Coordinates& start,
        const utils::Coordinates& end,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a line between world coordinates using a given camera.
     * @param start First world endpoint.
     * @param end Second world endpoint.
     * @param camera_coords Camera position and rotation.
     * @param roundness Roundness of the line in pixels.
     * @param thickness Line thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void line(
        const utils::Coordinates& start,
        const utils::Coordinates& end,
        const utils::CameraCoordinates& camera_coords,
        const float roundness,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: circle
    /**
     * Draw a circle at pixel coordinates.
     * @param x Horizontal center position in pixels.
     * @param y Vertical center position in pixels.
     * @param radius Circle radius in pixels.
     * @param thickness Circle outline thickness in pixels, zero or less fills the circle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void circle(
        const float x,
        const float y,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a circle at a screen coordinate.
     * @param center Circle center.
     * @param radius Circle radius in pixels.
     * @param thickness Circle outline thickness in pixels, zero or less fills the circle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void circle(
        const utils::ScreenCoordinates& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a circle at a world coordinate using the latest telemetry camera.
     * @param center World coordinate for the circle center.
     * @param radius Circle radius in pixels.
     * @param thickness Circle outline thickness in pixels, zero or less fills the circle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void circle(
        const utils::Coordinates& center,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a circle at a world coordinate using a given camera.
     * @param center World coordinate for the circle center.
     * @param camera_coords Camera position and rotation.
     * @param radius Circle radius in pixels.
     * @param thickness Circle outline thickness in pixels, zero or less fills the circle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void circle(
        const utils::Coordinates& center,
        const utils::CameraCoordinates& camera_coords,
        const float radius,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: rectangle
    /**
     * Draw a rectangle between pixel positions.
     * @param x1 Horizontal position of the first corner in pixels.
     * @param y1 Vertical position of the first corner in pixels.
     * @param x2 Horizontal position of the second corner in pixels.
     * @param y2 Vertical position of the second corner in pixels.
     * @param radius Corner radius in pixels.
     * @param thickness Rectangle outline thickness in pixels, zero or less fills the rectangle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void rectangle(
        const float x1,
        const float y1,
        const float x2,
        const float y2,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a rectangle between screen coordinates.
     * @param top_left Top left corner.
     * @param bottom_right Bottom right corner.
     * @param radius Corner radius in pixels.
     * @param thickness Rectangle outline thickness in pixels, zero or less fills the rectangle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void rectangle(
        const utils::ScreenCoordinates& top_left,
        const utils::ScreenCoordinates& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a rectangle between world coordinates using the latest telemetry camera.
     * @param top_left Top left world coordinate.
     * @param bottom_right Bottom right world coordinate.
     * @param radius Corner radius in pixels.
     * @param thickness Rectangle outline thickness in pixels, zero or less fills the rectangle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void rectangle(
        const utils::Coordinates& top_left,
        const utils::Coordinates& bottom_right,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a rectangle between world coordinates using a given camera.
     * @param top_left Top left world coordinate.
     * @param bottom_right Bottom right world coordinate.
     * @param camera_coords Camera position and rotation.
     * @param radius Corner radius in pixels.
     * @param thickness Rectangle outline thickness in pixels, zero or less fills the rectangle.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void rectangle(
        const utils::Coordinates& top_left,
        const utils::Coordinates& bottom_right,
        const utils::CameraCoordinates& camera_coords,
        float radius,
        const float thickness,
        const utils::ColorFloat& color
    );

    // MARK: polyline
    /**
     * Draw a polyline from pixel coordinates.
     * @param points Vertex positions in pixels.
     * @param closed Connect the final point back to the first point.
     * @param rounded Draw rounded vertices and joints.
     * @param thickness Polyline thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void polyline(
        const std::vector<std::pair<float, float>>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a polyline from screen coordinates.
     * @param points Vertex screen coordinates.
     * @param closed Connect the final point back to the first point.
     * @param rounded Draw rounded vertices and joints.
     * @param thickness Polyline thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void polyline(
        const std::vector<utils::ScreenCoordinates>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a polyline from world coordinates using the latest telemetry camera.
     * @param points World coordinate vertices.
     * @param closed Connect the final point back to the first point.
     * @param rounded Draw rounded vertices and joints.
     * @param thickness Polyline thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
    void polyline(
        const std::vector<utils::Coordinates>& points,
        const bool closed,
        const bool rounded,
        const float thickness,
        const utils::ColorFloat& color
    );
    /**
     * Draw a polyline from world coordinates using a given camera.
     * @param points World coordinate vertices.
     * @param camera_coords Camera position and rotation.
     * @param closed Connect the final point back to the first point.
     * @param rounded Draw rounded vertices and joints.
     * @param thickness Polyline thickness in pixels.
     * @param color RGBA color with components from 0.0 to 1.0.
     */
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
    using Command = std::function<void(AR&)>;
    void add(Command command);
    std::shared_ptr<const std::vector<Command>> snapshot() const;

    friend class AR;
    std::string id_;
    mutable std::mutex mutex_;
    std::vector<Command> building_commands_;
    std::shared_ptr<const std::vector<Command>> published_commands_;
};