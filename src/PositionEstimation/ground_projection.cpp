#include "PositionEstimation/ground_projection.h"

#include <algorithm>
#include <cmath>

using namespace std;


// Fits the road under the truck as a plane through the contact points of its wheels in vehicle space
// height = slope_x * x + slope_z * z + offset
// Returns false if fewer than three wheels touch the ground or they lie on one line
bool fit_wheel_contact_plane(
    const ets2la_telemetry::Telemetry& telemetry,
    double& slope_x,
    double& slope_z,
    double& offset
) {
    double count = 0.0;
    double sum_x = 0.0;
    double sum_z = 0.0;
    double sum_y = 0.0;
    double sum_xx = 0.0;
    double sum_xz = 0.0;
    double sum_zz = 0.0;
    double sum_xy = 0.0;
    double sum_zy = 0.0;

    for (uint32_t i = 0; i < telemetry.truck.wheel_count; ++i) {
        const auto& wheel = telemetry.truck.wheels[i];
        if (!wheel.simulated || !wheel.on_ground || wheel.lift > 0.01f) {
            continue;
        }

        const double x = wheel.position.x;
        const double z = wheel.position.z;
        const double y = wheel.position.y + wheel.suspension_deflection - wheel.radius;

        count += 1.0;
        sum_x += x;
        sum_z += z;
        sum_y += y;
        sum_xx += x * x;
        sum_xz += x * z;
        sum_zz += z * z;
        sum_xy += x * y;
        sum_zy += z * y;
    }

    if (count < 3.0) {
        return false;
    }

    const double a11 = sum_xx;
    const double a12 = sum_xz;
    const double a13 = sum_x;
    const double a22 = sum_zz;
    const double a23 = sum_z;
    const double a33 = count;
    const double determinant =
        a11 * (a22 * a33 - a23 * a23) -
        a12 * (a12 * a33 - a23 * a13) +
        a13 * (a12 * a23 - a22 * a13);

    if (abs(determinant) < 1e-3) {
        return false;
    }

    const double b1 = sum_xy, b2 = sum_zy, b3 = sum_y;
    slope_x = (
        b1 * (a22 * a33 - a23 * a23) -
        a12 * (b2 * a33 - a23 * b3) +
        a13 * (b2 * a23 - a22 * b3)
    ) / determinant;
    slope_z = (
        a11 * (b2 * a33 - a23 * b3) -
        b1 * (a12 * a33 - a23 * a13) +
        a13 * (a12 * b3 - b2 * a13)
    ) / determinant;
    offset = (
        a11 * (a22 * b3 - b2 * a23) -
        a12 * (a12 * b3 - b2 * a13) +
        b1 * (a12 * a23 - a22 * a13)
    ) / determinant;
    return true;
}


void GroundProjection::update(const ets2la_telemetry::Telemetry& telemetry) {
    const utils::Rotations truck_rotation{
        telemetry.truck.world.orientation.pitch * 360.0f,
        telemetry.truck.world.orientation.heading * 360.0f,
        telemetry.truck.world.orientation.roll * 360.0f
    };

    double slope_x = 0.0;
    double slope_z = 0.0;
    double offset = 0.0;
    const bool fitted = fit_wheel_contact_plane(telemetry, slope_x, slope_z, offset);

    const utils::Coordinates local_point{0.0, fitted ? offset : 0.0, 0.0};
    utils::Coordinates local_normal{0.0, 1.0, 0.0};
    if (fitted) {
        const double length = sqrt(slope_x * slope_x + 1.0 + slope_z * slope_z);
        local_normal = utils::Coordinates{-slope_x / length, 1.0 / length, -slope_z / length};
    }

    const utils::Coordinates rotated_point = utils::rotate_vector(local_point, truck_rotation);
    plane_.point = utils::Coordinates{
        telemetry.truck.world.position.x + rotated_point.x,
        telemetry.truck.world.position.y + rotated_point.y,
        telemetry.truck.world.position.z + rotated_point.z
    };
    plane_.normal = utils::rotate_vector(local_normal, truck_rotation);
    plane_.pitch_degrees = fitted ? static_cast<float>(utils::radians_to_degrees(atan(slope_z))) : 0.0f;
    plane_.roll_degrees = fitted ? static_cast<float>(utils::radians_to_degrees(atan(slope_x))) : 0.0f;
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
    if (abs(denom) < 1e-6) {
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