#ifndef PYTORCH_H
#define PYTORCH_H

#include "variables.h"

#include <torch/script.h>
#include <torch/torch.h>
#include <unordered_map>
#include <exception>
#include <iostream>
#include <sstream>
#include <utility>
#include <chrono>
#include <string>
#include <thread>
#include <vector>
#include <cmath>
#include <map>
#include <any>

class PyTorch {
    public:
    static void ExampleTensor();
    static void Initialize(std::string Owner = "", std::string Model = "", bool Threaded = true);
    static bool Loaded(std::string Model = "All");
    //static void Load(std::any Model = "All");
    //static void CheckForUpdates(std::any Model = "All");
    //static std::any GetName(std::any Model = "All");
    //static void Delete(std::any Model = "All");
};

#endif