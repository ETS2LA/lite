#include <chrono>

#include "telemetry.h"


double getCurrentTimeInMilliseconds() {
	return static_cast<double>(
		std::chrono::duration_cast<std::chrono::nanoseconds>(
			std::chrono::high_resolution_clock::now().time_since_epoch()
		).count() * 1e-6
	);
}

int main() {
	SCSTelemetry telemetry;

	float update_rate_ms = 0.0f;
	float prev_speed = 0.0f;
	double last_change = getCurrentTimeInMilliseconds();
	while (true) {
		TelemetryData* data = telemetry.data();
		std::printf("speed: %f, update rate: %f ms\n", data->truck_f.speed, update_rate_ms);
		if (prev_speed != data->truck_f.speed) {
			prev_speed = data->truck_f.speed;
			update_rate_ms = static_cast<float>(getCurrentTimeInMilliseconds() - last_change);
			last_change = getCurrentTimeInMilliseconds();
		}
	}
	return 0;
}