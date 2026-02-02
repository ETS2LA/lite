#pragma once

#include <opencv2/opencv.hpp>

#include "controller.h"
#include "telemetry.h"
#include "capture.h"
#include "input.h"
#include "utils.h"


namespace navigation_detection {

void initialize(ScreenCapture* capture);
void run();

}