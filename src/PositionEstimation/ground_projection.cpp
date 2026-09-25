#include "PositionEstimation/ground_projection.h"

#include <algorithm>
#include <cmath>

using namespace std;


void GroundProjection::update(TelemetryData* telemetry_data) {
    const utils::Rotations truck_rotation{
        static_cast<float>(telemetry_data->truck_dp.rotationY * 360.0),
        static_cast<float>(telemetry_data->truck_dp.rotationX * 360.0),
        static_cast<float>(telemetry_data->truck_dp.rotationZ * 360.0)
    };

    plane_.point = utils::Coordinates{
        telemetry_data->truck_dp.coordinateX,
        telemetry_data->truck_dp.coordinateY,
        telemetry_data->truck_dp.coordinateZ
    };
    plane_.normal = utils::rotate_vector(utils::Coordinates{0.0, 1.0, 0.0}, truck_rotation);
    plane_.pitch_degrees = truck_rotation.pitch;
    plane_.roll_degrees = truck_rotation.roll;
    plane_.valid = true;
}


utils::Coordinates GroundProjection::project_to_ground(
    const utils::Angles& angles,
    const utils::CameraCoordinates& camera_coords,
    bool& ok
) const {
    ok = false;
    const utils::Coordinates origin{camera_coords.x, camera_coords.y, camera_coords.z};

    if (!plane_.valid) {
        return origin;
    }

    const utils::Coordinates direction = utils::camera_ray_direction(angles, camera_coords);

    const double denom = utils::dot_product(direction, plane_.normal);
    if (std::abs(denom) < 1e-6) {
        return origin;
    }

    const utils::Coordinates to_plane_point{
        plane_.point.x - origin.x,
        plane_.point.y - origin.y,
        plane_.point.z - origin.z
    };
    const double t = utils::dot_product(to_plane_point, plane_.normal) / denom;

    if (t <= 0.0) {
        return origin;
    }

    ok = true;
    return utils::Coordinates{
        origin.x + direction.x * t,
        origin.y + direction.y * t,
        origin.z + direction.z * t
    };
}