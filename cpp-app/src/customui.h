#ifndef CUSTOMUI_H
#define CUSTOMUI_H

#include <windows.h>
#include <iostream>
#include <string>
#include <thread>
#include <any>

class CustomUI {
public:
    static void Create(LPCWSTR Name, int X, int Y, int Width, int Height);
};

#endif