#pragma once

#include "ObjectDetection/object_detection.h"
#include "tracker.h"
#include "utils.h"

#include <unordered_map>
#include <utility>
#include <memory>
#include <string>
#include <mutex>
#include <any>


struct PositionedObject {
    Tracker::Object tracking;
    utils::Coordinates position{};
    bool position_valid = false;
};

struct PositionSnapshot {
    std::vector<PositionedObject> objects;
};


class SharedData {
public:
    template <typename T>
    void set(const std::string& name, T value) {
        auto snapshot = std::make_shared<const T>(std::move(value));
        std::lock_guard lock(mutex_);
        values_[name] = std::move(snapshot);
    }

    template <typename T>
    std::shared_ptr<const T> get(const std::string& name) const {
        std::lock_guard lock(mutex_);
        const auto value = values_.find(name);
        if (value == values_.end()) {
            return nullptr;
        }

        return std::any_cast<std::shared_ptr<const T>>(value->second);
    }

private:
    mutable std::mutex mutex_;
    std::unordered_map<std::string, std::any> values_;
};