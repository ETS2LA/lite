#include "controller.h"
#include <windows.h>
#include <iostream>


SCSController::SCSController() : initialized(false), map_file(NULL), buffer(NULL) {
    memset(static_cast<ControllerData*>(this), 0, sizeof(ControllerData));

    size_t shm_size = sizeof(ControllerData);

    map_file = CreateFileMappingA(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        (DWORD)shm_size,
        "Local\\SCSControls"
    );

    if (map_file == NULL) {
        std::printf("Could not create file mapping object (%lu).\n", GetLastError());
        return;
    }

    buffer = MapViewOfFile(
        map_file,
        FILE_MAP_ALL_ACCESS,
        0,
        0,
        shm_size
    );

    if (buffer == NULL) {
        std::printf("Could not map view of file (%lu).\n", GetLastError());
        CloseHandle(map_file);
        map_file = NULL;
        return;
    }

    initialized = true;
}

SCSController::~SCSController() {
    if (buffer) {
        UnmapViewOfFile(buffer);
        buffer = NULL;
    }
    if (map_file) {
        CloseHandle(map_file);
        map_file = NULL;
    }
}

void SCSController::update() {
    if (initialized && buffer) {
        memcpy(buffer, static_cast<ControllerData*>(this), sizeof(ControllerData));
    }
}