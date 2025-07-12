#include "log.h"

static scs_log_t game_log;
const int MAX_LOG_LENGTH = 1024;

void set_log(scs_log_t log) {
    game_log = log;
}

void log_message(const char *message) {
    char buffer[MAX_LOG_LENGTH];
    strcpy_s(buffer, "[ets2la_lite] ");
    strcat_s(buffer, message);
    game_log(SCS_LOG_TYPE_message, buffer);
}

void log_warning(const char *message) {
    char buffer[MAX_LOG_LENGTH];
    strcpy_s(buffer, "[ets2la_lite] ");
    strcat_s(buffer, message);
    game_log(SCS_LOG_TYPE_warning, buffer);
}

void log_error(const char *message) {
    char buffer[MAX_LOG_LENGTH];
    strcpy_s(buffer, "[ets2la_lite] ");
    strcat_s(buffer, message);
    game_log(SCS_LOG_TYPE_error, buffer);
}