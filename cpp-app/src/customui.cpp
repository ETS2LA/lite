#include "customui.h"

#define BUTTON_ONE 1
#define BUTTON_TWO 2
void CreateThread(LPCWSTR Name, int X, int Y, int Width, int Height) {

    WNDPROC WindowProc = [](HWND HWND, UINT uMsg, WPARAM wParam, LPARAM lParam) -> LRESULT {
        switch (uMsg) {
            case WM_CLOSE:
                DestroyWindow(HWND);
                return 0;
            case WM_DESTROY:
                PostQuitMessage(0);
                return 0;
            case WM_COMMAND: {
                int wmId = LOWORD(wParam);
                switch (wmId) {

                    case BUTTON_ONE: {
                        MessageBoxW(HWND, L"Button One Clicked", L"Button Event", MB_OK);
                        break;
                    }

                    case BUTTON_TWO: {
                        MessageBoxW(HWND, L"Button Two Clicked", L"Button Event", MB_OK);
                        break;
                    }

                }
                break;
            }
            default:
                return DefWindowProcW(HWND, uMsg, wParam, lParam);
        }
    };

    HINSTANCE hInstance = GetModuleHandle(NULL);

    WNDCLASSW WC = {};
    WC.lpfnWndProc = WindowProc;
    WC.hInstance = hInstance;
    WC.lpszClassName = Name;
    WC.hCursor = LoadCursor(NULL, IDC_ARROW);
    WC.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);

    if (!RegisterClassW(&WC)) {
        DWORD error = GetLastError();
        std::cerr << "Window class registration failed. Error: " << error << std::endl;
        MessageBoxW(NULL, L"Window Class Registration Failed!", L"Error", MB_ICONEXCLAMATION | MB_OK);
        return;
    }

    HWND HWND = CreateWindowExW(
        0,
        Name,
        Name,
        WS_OVERLAPPEDWINDOW,
        X, Y, Width, Height,
        NULL, NULL, hInstance, NULL);

    CreateWindowW(L"BUTTON", L"Button One",
        WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
        50, 100, 150, 50,
        HWND, (HMENU) BUTTON_ONE, hInstance, NULL);

    CreateWindowW(L"BUTTON", L"Button Two",
        WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
        250, 100, 150, 50,
        HWND, (HMENU) BUTTON_TWO, hInstance, NULL);

    ShowWindow(HWND, SW_SHOW);
    UpdateWindow(HWND);

    MSG MSG = {};
    while (GetMessage(&MSG, NULL, 0, 0)) {
        TranslateMessage(&MSG);
        DispatchMessage(&MSG);
    }
}

void CustomUI::Create(LPCWSTR Name, int X, int Y, int Width, int Height) {
    std::thread UI([Name, X, Y, Width, Height]() {CreateThread(Name, X, Y, Width, Height);});
	UI.detach();
}