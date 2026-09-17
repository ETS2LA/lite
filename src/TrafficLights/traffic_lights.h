#pragma once

#include <opencv2/opencv.hpp>

#include "capture.h"
#include "utils.h"

namespace traffic_lights {

#define TRAFFIC_LIGHT_NONE 0
#define TRAFFIC_LIGHT_RED 1
#define TRAFFIC_LIGHT_YELLOW 2
#define TRAFFIC_LIGHT_GREEN 3

void initialize(ScreenCapture* capture);
void run();

}