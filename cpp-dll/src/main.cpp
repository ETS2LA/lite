#define NOMINMAX

#include <windows.h>

#include "scssdk_telemetry.h"
#include "eurotrucks2/scssdk_eut2.h"
#include "eurotrucks2/scssdk_telemetry_eut2.h"

#include "log.h"

#define PLUGIN_NAME "ETS2LA Lite"
#define PLUGIN_VERSION "1.0.0"

static scs_log_t game_log = nullptr;

static scs_telemetry_register_for_event_t register_for_event = nullptr;
static scs_telemetry_register_for_channel_t register_for_channel = nullptr;
static scs_telemetry_unregister_from_event_t unregister_from_event = nullptr;
static scs_telemetry_unregister_from_channel_t unregister_from_channel = nullptr;


SCSAPI_VOID telemetry_callback(const scs_event_t event, const void* const event_info, const scs_context_t context) {
    if (event == SCS_TELEMETRY_EVENT_paused) {
        log_message("ETS2LA Lite Plugin paused");
    }
    else if (event == SCS_TELEMETRY_EVENT_started) {
        log_message("ETS2LA Lite Plugin unpaused");
    }
}


SCSAPI_RESULT scs_telemetry_init(const scs_u32_t version, const scs_telemetry_init_params_t* const params) {
    if (version != SCS_TELEMETRY_VERSION_1_00 && version != SCS_TELEMETRY_VERSION_1_01) {
        return SCS_RESULT_unsupported;
    }

    const scs_telemetry_init_params_v100_t* const version_params = static_cast<const scs_telemetry_init_params_v100_t*>(params);

    // set log callback
    set_log(version_params->common.log);

    log_message("Initializing ETS2LA Lite Plugin" PLUGIN_VERSION);


    register_for_event = version_params->register_for_event;
    register_for_channel = version_params->register_for_channel;
    unregister_from_event = version_params->unregister_from_event;
    unregister_from_channel = version_params->unregister_from_channel;

    if (!register_for_event || !register_for_channel || !unregister_from_event || !unregister_from_channel) {
        log_error("Missing required callback functions");
        return SCS_RESULT_generic_error;
    }


    // register callbacks
    if (register_for_event(SCS_TELEMETRY_EVENT_paused, telemetry_callback, nullptr) != SCS_RESULT_ok) {
        log_error("Unable to register paused event callback");
        return SCS_RESULT_generic_error;
    }

    if (register_for_event(SCS_TELEMETRY_EVENT_started, telemetry_callback, nullptr) != SCS_RESULT_ok) {
        log_error("Unable to register started event callback");
        return SCS_RESULT_generic_error;
    }


    log_message("ETS2LA Lite Plugin initialized successfully");

    return SCS_RESULT_ok;
}


SCSAPI_VOID scs_telemetry_shutdown(void) {
    if (unregister_from_event) {
        unregister_from_event(SCS_TELEMETRY_EVENT_frame_start);
        unregister_from_event(SCS_TELEMETRY_EVENT_paused);
        unregister_from_event(SCS_TELEMETRY_EVENT_started);
    }

    log_message("ETS2LA Lite Plugin shutdown");
}


BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
        case DLL_PROCESS_ATTACH:
            break;
        case DLL_THREAD_ATTACH:
            break;
        case DLL_THREAD_DETACH:
            break;
        case DLL_PROCESS_DETACH:
            break;
    }
    return TRUE;
}