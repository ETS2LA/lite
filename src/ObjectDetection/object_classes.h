#pragma once

#include <opencv2/opencv.hpp>
#include <string>
#include <array>


namespace object_classes {

/**
 * Class IDs.
 * The order of the classes must match the output of the model.
 */
enum Id : int {
    Car,
    Bus,
    Truck,
    Stoplight,
    Streetlamp,
    Sign,
    ShortPost,
    LongPole,
    CurvedPole,
    LaneLine,
    TreeTrunk,
    BridgePier,
    TrafficCone,
    TrafficDelineator,
    Count
};

/**
 * General group of object classes.
 * For example, Car, Bus and Truck are all in the Vehicle group.
 */
enum class Group {
    Vehicle,
    Pole,
    Stoplight,
    Streetlamp,
    Sign,
    LaneLine,
    TreeTrunk,
    BridgePier,
    TrafficCone,
    TrafficDelineator
};

/**
 * Information about a class.
 * @param name The name of the class.
 * @param color The display color of the class.
 * @param group The general group of the class.
 */
struct Info {
    const char* name;
    cv::Scalar color;
    Group group;
};

/**
 * Get the table of class information.
 * @return The table of class information.
 */
inline const std::array<Info, Count>& table() {
    static const std::array<Info, Count> classes = {{
        {"car", cv::Scalar{0, 255, 0}, Group::Vehicle},
        {"bus", cv::Scalar{255, 255, 0}, Group::Vehicle},
        {"truck", cv::Scalar{0, 0, 255}, Group::Vehicle},
        {"stoplight", cv::Scalar{0, 255, 255}, Group::Stoplight},
        {"streetlamp", cv::Scalar{128, 128, 128}, Group::Streetlamp},
        {"sign", cv::Scalar{255, 75, 75}, Group::Sign},
        {"short post", cv::Scalar{128, 128, 128}, Group::Pole},
        {"long pole", cv::Scalar{128, 128, 128}, Group::Pole},
        {"curved pole", cv::Scalar{128, 128, 128}, Group::Pole},
        {"lane line", cv::Scalar{255, 255, 255}, Group::LaneLine},
        {"tree trunk", cv::Scalar{0, 25, 50}, Group::TreeTrunk},
        {"bridge pier", cv::Scalar{128, 128, 128}, Group::BridgePier},
        {"traffic cone", cv::Scalar{0, 75, 255}, Group::TrafficCone},
        {"traffic delineator", cv::Scalar{0, 75, 255}, Group::TrafficDelineator}
    }};
    return classes;
}

/**
 * Check if a class ID is valid.
 * @param class_id The class ID to check.
 * @return True if the class ID is valid, false otherwise.
 */
inline bool is_valid(const int class_id) {
    return class_id >= 0 && class_id < Count;
}

/**
 * Get the name of a class.
 * @param class_id The class ID to get the name for.
 * @return The name of the class, or "unknown" if the class ID is invalid.
 */
inline std::string name(const int class_id) {
    return is_valid(class_id) ? table()[class_id].name : "unknown";
}

/**
 * Get the display color of a class.
 * @param class_id The class ID to get the color for.
 * @return The display color of the class, or white if the class ID is invalid.
 */
inline cv::Scalar color(const int class_id) {
    return is_valid(class_id) ? table()[class_id].color : cv::Scalar{255, 255, 255};
}

/**
 * General group of a class.
 * @param class_id The class ID to check.
 * @return The general group of the class, or Group::Vehicle if the class ID is invalid.
 */
inline Group group(const int class_id) {
    return is_valid(class_id) ? table()[class_id].group : Group::Vehicle;
}

/**
 * Check if a class is ground projected.
 * @param class_id The class ID to check.
 * @return True if the class is ground projected, false otherwise.
 */
inline bool is_ground_projected(const int class_id) {
    return group(class_id) == Group::Vehicle || class_id == ShortPost || class_id == LaneLine;
}

/**
 * Check if a class is triangulated.
 * @param class_id The class ID to check.
 * @return True if the class is ground projected, false otherwise.
 */
inline bool is_triangulated(const int class_id) {
    return !is_ground_projected(class_id);
}

/**
 * Check if the class is a vehicle.
 * @param class_id The class ID to check.
 * @return True if the class is a vehicle, false otherwise.
 */
inline bool is_vehicle(const int class_id) {
    return group(class_id) == Group::Vehicle;
}

}