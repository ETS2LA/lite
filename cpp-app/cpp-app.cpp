#include "cpp-app.h"

int main(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow) {
    UI::CreateMainWindow(hInstance, nCmdShow);

    if (BUILD_TYPE == "Release") {
        system("pause");
    }

    return 0;
}
