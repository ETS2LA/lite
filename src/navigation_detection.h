#pragma once

#include <ets2la_telemetry/telemetry_reader.h>
#include <opencv2/opencv.hpp>

#include "controller.h"
#include "input.h"
#include "utils.h"


namespace navigation_detection {

void initialize();
void run();

}