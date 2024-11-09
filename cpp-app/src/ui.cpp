#include <windows.h>
#include <string>
#include <iostream>
#include <opencv2/opencv.hpp>
#include <dwmapi.h>

#define BUTTON_ONE 1
#define BUTTON_TWO 2
class UI {
public:
    static void Initialize();
    static void CreateMainWindow(HINSTANCE hInstance, int nCmdShow);
private:
    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam);
};

void UI::Initialize() {
    std::wcout << L"UI Initialized." << std::endl;
}

LRESULT CALLBACK UI::WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
        case WM_COMMAND: {
            int wmId = LOWORD(wParam);
            switch (wmId) {
                case BUTTON_ONE: {
                    HWND hwndDesktop = GetDesktopWindow();

                    HDC hDC = GetDC(hwndDesktop);
                    HDC hMemDC = CreateCompatibleDC(hDC);

                    int width = GetSystemMetrics(SM_CXSCREEN);
                    int height = GetSystemMetrics(SM_CYSCREEN);

                    HBITMAP hBitmap = CreateCompatibleBitmap(hDC, width, height);
                    SelectObject(hMemDC, hBitmap);

                    BitBlt(hMemDC, 0, 0, width, height, hDC, 0, 0, SRCCOPY);

                    BITMAPINFO bi = { sizeof(BITMAPINFOHEADER) };
                    bi.bmiHeader.biWidth = width;
                    bi.bmiHeader.biHeight = -height;
                    bi.bmiHeader.biPlanes = 1;
                    bi.bmiHeader.biBitCount = 32;
                    bi.bmiHeader.biCompression = BI_RGB;

                    cv::Mat screen(height, width, CV_8UC4);
                    GetDIBits(hMemDC, hBitmap, 0, height, screen.data, &bi, DIB_RGB_COLORS);

                    DeleteObject(hBitmap);
                    DeleteDC(hMemDC);
                    ReleaseDC(hwndDesktop, hDC);

                    cv::imshow("Screen Capture", screen);
                    cv::waitKey(0);

                    break;
                }
                case BUTTON_TWO:
                    MessageBoxW(hwnd, L"Button Two Clicked", L"Button Event", MB_OK);
                    break;
            }
            break;
        }
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(hwnd, uMsg, wParam, lParam);
}

void UI::CreateMainWindow(HINSTANCE hInstance, int nCmdShow) {
    std::cout << "Creating window..." << std::endl;
    const std::wstring CLASS_NAME = L"Sample Window Class";

    WNDCLASSW wc = {};
    wc.lpfnWndProc = UI::WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME.c_str();
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);

    if (!RegisterClassW(&wc)) {
        DWORD error = GetLastError();
        std::cerr << "Window class registration failed. Error: " << error << std::endl;
        MessageBoxW(NULL, L"Window Class Registration Failed!", L"Error", MB_ICONEXCLAMATION | MB_OK);
        return;
    }

    HWND hwnd = CreateWindowExW(
        0,
        CLASS_NAME.c_str(),
        L"Simple UI Window",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT,
        500, 400,
        NULL, NULL, hInstance, NULL
    );

    if (hwnd == NULL) {
        DWORD error = GetLastError();
        std::cerr << "Window creation failed. Error: " << error << std::endl;
        MessageBoxW(NULL, L"Window Creation Failed!", L"Error", MB_ICONEXCLAMATION | MB_OK);
        return;
    }

    CreateWindowW(
        L"BUTTON", L"Test OpenCV",
        WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
        50, 100, 150, 50,
        hwnd, (HMENU)BUTTON_ONE, hInstance, NULL
    );

    CreateWindowW(
        L"BUTTON", L"Button Two",
        WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
        250, 100, 150, 50,
        hwnd, (HMENU)BUTTON_TWO, hInstance, NULL
    );

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    MSG msg = {};
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow) {

    AllocConsole();
    freopen("CONOUT$", "w", stdout);

    UI::Initialize();
    UI::CreateMainWindow(hInstance, nCmdShow);

    FreeConsole();
    return 0;

}
