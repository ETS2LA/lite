#include "pytorch.h"

void PyTorch::ExampleTensor() {
    torch::Tensor Tensor = torch::rand({3, 3});
    std::cout << "Example of a random tensor:\n" << Tensor << std::endl;
}

const std::string RED = "\033[91m";
const std::string GREEN = "\033[92m";
const std::string GRAY = "\033[90m";
const std::string NORMAL = "\033[0m";

std::map<std::string, std::map<std::string, std::string>> MODELS;

void PyTorch::Initialize(std::string Owner, std::string Model, bool Threaded) {
    if (torch::cuda::is_available()) {
        MODELS[Model]["Device"] = "cuda";
    } else {
        MODELS[Model]["Device"] = "cpu";
    }
    MODELS[Model]["Path"] = PATH + "cache/" + Model;
    MODELS[Model]["Threaded"] = Threaded;
    MODELS[Model]["ModelOwner"] = Owner;
};

//bool PyTorch::Loaded(std::any Model = "All") {
//    if (Model == "All") {
//        for (auto& [key, value] : MODELS) {
//            if (value["Threaded"] == true) {
//                if (value["UpdateThread"].joinable() || value["LoadThread"].joinable()) {
//                    return false;
//                }
//            }
//        }
//    } else {
//        if (MODELS[Model]["Threaded"] == true) {
//            if (MODELS[Model]["UpdateThread"].joinable() || MODELS[Model]["LoadThread"].joinable()) {
//                return false;
//            }
//        }
//    }
//    return true;
//};
//
//void LoadFunction(std::any Model) {
//    PyTorch::CheckForUpdates(Model);
//    if (MODELS[Model].count("UpdateThread")) {
//        while (MODELS[Model]["UpdateThread"].type() == typeid(std::thread) && static_cast<std::thread&>(MODELS[Model]["UpdateThread"]).joinable()) {
//            std::this_thread::sleep_for(std::chrono::milliseconds(100));
//        }
//    }
//
//    if (PyTorch::GetName(Model) == nullptr) {
//        return;
//    }
//
//    bool ModelFileBroken = false;
//
//    try {
//        MODELS[Model]["Metadata"] = {{"data", std::vector<std::string>()}};
//        MODELS[Model]["Model"] = torch::jit::load(MODELS[Model]["Path"] + PyTorch::GetName(Model), MODELS[Model]["Metadata"]["data"], MODELS[Model]["Device"]);
//        MODELS[Model]["Model"].eval();
//        MODELS[Model]["Metadata"]["data"] = std::any_cast<std::vector<std::string>>(MODELS[Model]["Metadata"]["data"]);
//        for (const auto& Item : MODELS[Model]["Metadata"]["data"]) {
//            std::string Item_ = Item;
//            if (Item_.find("image_width") != std::string::npos) {
//                MODELS[Model]["IMG_WIDTH"] = std::stoi(Item_.substr(Item_.find("#") + 1));
//            } else if (Item_.find("image_height") != std::string::npos) {
//                MODELS[Model]["IMG_HEIGHT"] = std::stoi(Item_.substr(Item_.find("#") + 1));
//            } else if (Item_.find("image_channels") != std::string::npos) {
//                MODELS[Model]["IMG_CHANNELS"] = Item_.substr(Item_.find("#") + 1);
//            } else if (Item_.find("outputs") != std::string::npos) {
//                MODELS[Model]["OUTPUTS"] = std::stoi(Item_.substr(Item_.find("#") + 1));
//            } else if (Item_.find("epochs") != std::string::npos) {
//                MODELS[Model]["EPOCHS"] = std::stoi(Item_.substr(Item_.find("#") + 1));
//            } else if (Item_.find("batch") != std::string::npos) {
//                MODELS[Model]["BATCH_SIZE"] = std::stoi(Item_.substr(Item_.find("#") + 1));
//            } else if (Item_.find("image_count") != std::string::npos) {
//                MODELS[Model]["IMAGE_COUNT"] = std::stoi(Item_.substr(Item_.find("#") + 1));
//            } else if (Item_.find("training_time") != std::string::npos) {
//                MODELS[Model]["TRAINING_TIME"] = Item_.substr(Item_.find("#") + 1);
//            } else if (Item_.find("training_date") != std::string::npos) {
//                MODELS[Model]["TRAINING_DATE"] = Item_.substr(Item_.find("#") + 1);
//            }
//        }
//    } catch (...) {
//        ModelFileBroken = true;
//    }
//
//    if (ModelFileBroken == false) {
//        MODELS[Model]["ModelLoaded"] = true;
//    } else {
//        MODELS[Model]["ModelLoaded"] = false;
//        HandleBroken(Model);
//    }
//        
//};
//
//void PyTorch::Load(std::any Model) {
//    if (MODELS[Model]["Threaded"] == true) {
//        MODELS[Model]["LoadThread"] = std::thread(LoadFunction, Model);
//        MODELS[Model]["LoadThread"].detach();
//    } else {
//        LoadFunction(Model);
//    }
//};
//
//void CheckForUpdatesFunction(std::any Model) {
//    std::cout << "yeah there is not update checking yet..." << std::endl;
//}
//
//void PyTorch::CheckForUpdates(std::any Model) {
//    if (MODELS[Model]["Threaded"] == true) {
//        MODELS[Model]["UpdateThread"] = std::thread(CheckForUpdatesFunction, Model);
//        MODELS[Model]["UpdateThread"].detach();
//    } else {
//        CheckForUpdatesFunction(Model);
//    }
//};
//
//void FolderExists(std::any Model) {
//    if (std::filesystem::exists(MODELS[Model]["Path"]) == false) {
//        try {
//            std::filesystem::create_directory(MODELS[Model]["Path"]);
//        } catch (const std::exception& e) {
//            
//        }
//    }
//};
//
//std::any PyTorch::GetName(std::any Model) {
//    FolderExists(Model);
//    for (const auto& entry : std::filesystem::directory_iterator(MODELS[Model]["Path"])) {
//        if (entry.path().extension() == ".pt") {
//            return entry.path().filename().string();
//        }
//    }
//    return nullptr;
//};
//
//void Delete(std::any Model) {
//    FolderExists(Model);
//    try {
//        for (const auto& entry : std::filesystem::directory_iterator(MODELS[Model]["Path"])) {
//            if (entry.path().extension() == ".pt") {
//                std::filesystem::remove(entry.path());
//            }
//        }
//    } catch (const std::exception& e) {
//        
//    }
//};
//
//void HandleBroken(std::any Model) {
//    PyTorch::Delete(Model);
//    PyTorch::CheckForUpdates(Model);
//    if (MODELS[Model]["UpdateThread"].type() == typeid(std::thread) && static_cast<std::thread&>(MODELS[Model]["UpdateThread"]).joinable()) {
//        while (MODELS[Model]["UpdateThread"].type() == typeid(std::thread) && static_cast<std::thread&>(MODELS[Model]["UpdateThread"]).joinable()) {
//            std::this_thread::sleep_for(std::chrono::milliseconds(100));
//        }
//    }
//    std::this_thread::sleep_for(std::chrono::milliseconds(500));
//    PyTorch::Load(Model);
//};