#include "telemetry.h"
#include "controller.h"

#include <chrono>
#include <thread>


double getCurrentTimeInMilliseconds() {
	return static_cast<double>(
		std::chrono::duration_cast<std::chrono::nanoseconds>(
			std::chrono::high_resolution_clock::now().time_since_epoch()
		).count() * 1e-6
	);
}

int main() {
	SCSController controller;

	while (true) {
		controller.steering = static_cast<float>(sin(getCurrentTimeInMilliseconds() * 0.001));
		controller.update();
		std::this_thread::sleep_for(std::chrono::milliseconds(10));
	}
	return 0;
}