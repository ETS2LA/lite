#include "PositionEstimation/triangulation.h"

#include <algorithm>
#include <cmath>

using namespace std;


utils::Coordinates triangulate_position(
    const utils::CameraCoordinates& camera_coords,
    Tracker::Object& object,
    const int window_width,
    const int window_height
) {
    const utils::CameraCoordinates& cam0 = object.first_camera_coords;
    const utils::Angles& ang0 = object.angles;
    const utils::Angles ang1 = utils::convert_to_angles(
        {object.ground_anchor_x(), object.ground_anchor_y(), 0.0f},
        window_width,
        window_height
    );

    const utils::Coordinates p0{cam0.x, cam0.y, cam0.z};
    const utils::Coordinates p1{camera_coords.x, camera_coords.y, camera_coords.z};
    const utils::Coordinates d0 = utils::camera_ray_direction(ang0, cam0);
    const utils::Coordinates d1 = utils::camera_ray_direction(ang1, camera_coords);

    const utils::Coordinates r{p0.x - p1.x, p0.y - p1.y, p0.z - p1.z};
    const double a = utils::dot_product(d0, d0);
    const double b = utils::dot_product(d0, d1);
    const double c = utils::dot_product(d1, d1);
    const double d = utils::dot_product(d0, r);
    const double e = utils::dot_product(d1, r);
    const double denom = a * c - b * b;

    double t = 0.0;
    double s = 0.0;
    if (std::abs(denom) > 1e-6) {
        t = (b * e - c * d) / denom;
        s = (a * e - b * d) / denom;
    } else if (std::abs(b) > 1e-6) {
        t = 0.0;
        s = d / b;
    }

    if (s < 1e-6) {
        s = 1e-6;
    }
    if (t < 0.0) {
        t = 0.0;
    }

    const utils::Coordinates c0{p0.x + d0.x * t, p0.y + d0.y * t, p0.z + d0.z * t};
    const utils::Coordinates c1{p1.x + d1.x * s, p1.y + d1.y * s, p1.z + d1.z * s};

    const double baseline = std::sqrt(r.x * r.x + r.y * r.y + r.z * r.z);
    const double sin_angle = std::sqrt(std::max(0.0, 1.0 - b * b));
    object.accuracy = baseline * sin_angle;

    const utils::Coordinates mid{
        (c0.x + c1.x) * 0.5,
        (c0.y + c1.y) * 0.5,
        (c0.z + c1.z) * 0.5
    };

    const utils::Coordinates v1{mid.x - p1.x, mid.y - p1.y, mid.z - p1.z};
    if (utils::dot_product(d1, v1) < 0.0) {
        object.accuracy = 0.0f;
    }

    return mid;
}