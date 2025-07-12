#pragma once

#include "eurotrucks2/scssdk_eut2.h"
#include <cstring>

void set_log(scs_log_t log);
void log_message(const char *message);
void log_warning(const char *message);
void log_error(const char *message);