#include "cpp-app.h"

int main() {
	PyTorchExampleTensor();
	PyTorchInitialize("Glas42", "NavigationDetectionAI", true);

	#ifdef BUILD_TYPE_RELEASE
		system("pause");
	#endif
}