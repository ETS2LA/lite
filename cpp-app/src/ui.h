#ifndef UI_H
#define UI_H

#include <windows.h>
#include <string>

class UI {
public:
    static void Initialize();
    static void CreateMainWindow(HINSTANCE hInstance, int nCmdShow);

private:
    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam);
};

#endif
