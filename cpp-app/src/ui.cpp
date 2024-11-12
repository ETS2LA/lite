#include "ui.h"

//#define BUTTON_ONE 1
//#define BUTTON_TWO 2
//
//LRESULT CALLBACK UI::WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
//    switch (uMsg) {
//        case WM_COMMAND: {
//            int wmId = LOWORD(wParam);
//            switch (wmId) {
//
//                case BUTTON_ONE: {
//                    HWND hwndDesktop = GetDesktopWindow();
//
//                    HDC hDC = GetDC(hwndDesktop);
//                    HDC hMemDC = CreateCompatibleDC(hDC);
//
//                    int Width = GetSystemMetrics(SM_CXSCREEN);
//                    int Height = GetSystemMetrics(SM_CYSCREEN);
//
//                    HBITMAP hBitmap = CreateCompatibleBitmap(hDC, Width, Height);
//                    SelectObject(hMemDC, hBitmap);
//
//                    BitBlt(hMemDC, 0, 0, Width, Height, hDC, 0, 0, SRCCOPY);
//
//                    BITMAPINFO bi = { sizeof(BITMAPINFOHEADER) };
//                    bi.bmiHeader.biWidth = Width;
//                    bi.bmiHeader.biHeight = -Height;
//                    bi.bmiHeader.biPlanes = 1;
//                    bi.bmiHeader.biBitCount = 32;
//                    bi.bmiHeader.biCompression = BI_RGB;
//
//                    cv::Mat Image(Height, Width, CV_8UC4);
//                    GetDIBits(hMemDC, hBitmap, 0, Height, Image.data, &bi, DIB_RGB_COLORS);
//
//                    DeleteObject(hBitmap);
//                    DeleteDC(hMemDC);
//                    ReleaseDC(hwndDesktop, hDC);
//
//					OpenCV::ShowImage("Screen Capture", Image, true);
//
//                    break;
//                }
//
//                case BUTTON_TWO: {
//                    MessageBoxW(hwnd, L"Button Two Clicked", L"Button Event", MB_OK);
//                    break;
//				}
//
//            }
//            break;
//        }
//        case WM_DESTROY:
//            PostQuitMessage(0);
//            return 0;
//    }
//    return DefWindowProcW(hwnd, uMsg, wParam, lParam);
//}
//
//void UI::CreateMainWindow(HINSTANCE hInstance, int nCmdShow) {
//    const std::wstring CLASS_NAME = L"Sample Window Class";
//
//    WNDCLASSW wc = {};
//    wc.lpfnWndProc = UI::WindowProc;
//    wc.hInstance = hInstance;
//    wc.lpszClassName = CLASS_NAME.c_str();
//    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
//    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
//
//    if (!RegisterClassW(&wc)) {
//        DWORD error = GetLastError();
//        std::cerr << "Window class registration failed. Error: " << error << std::endl;
//        MessageBoxW(NULL, L"Window Class Registration Failed!", L"Error", MB_ICONEXCLAMATION | MB_OK);
//        return;
//    }
//
//    HWND HWND = CreateWindowExW(
//        0,
//        CLASS_NAME.c_str(),
//        L"Simple UI Window",
//        WS_OVERLAPPEDWINDOW,
//        CW_USEDEFAULT, CW_USEDEFAULT,
//        500, 400,
//        NULL, NULL, hInstance, NULL
//    );
//
//    if (HWND == NULL) {
//        DWORD error = GetLastError();
//        std::cerr << "Window creation failed. Error: " << error << std::endl;
//        MessageBoxW(NULL, L"Window Creation Failed!", L"Error", MB_ICONEXCLAMATION | MB_OK);
//        return;
//    }
//
//    CreateWindowW(L"BUTTON", L"Test OpenCV",
//        WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
//        50, 100, 150, 50,
//        HWND, (HMENU) BUTTON_ONE, hInstance, NULL);
//
//    CreateWindowW(L"BUTTON", L"Button Two",
//        WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
//        250, 100, 150, 50,
//        HWND, (HMENU) BUTTON_TWO, hInstance, NULL);
//
//    ShowWindow(HWND, SW_SHOW);
//    UpdateWindow(HWND);
//
//    MSG MSG = {};
//    while (GetMessage(&MSG, NULL, 0, 0)) {
//        TranslateMessage(&MSG);
//        DispatchMessage(&MSG);
//    }
//}
//
//int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow) {
//    AllocConsole();
//    freopen("CONOUT$", "w", stdout);
//	freopen("CONOUT$", "w", stderr);
//
//    UI::CreateMainWindow(hInstance, nCmdShow);
//
//    FreeConsole();
//    return 0;
//
//}