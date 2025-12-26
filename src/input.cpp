#include "input.h"

#include <algorithm>
#include <cctype>
#include <sstream>

using namespace std;


/**
 * Trim leading and trailing whitespace from a string.
 * @param text The input string to trim.
 */
string InputHandler::trim(const string& text) {
    size_t start = 0;
    while (start < text.size() && isspace(static_cast<unsigned char>(text[start]))) {
        ++start;
    }
    size_t end = text.size();
    while (end > start && isspace(static_cast<unsigned char>(text[end - 1]))) {
        --end;
    }
    return text.substr(start, end - start);
}


/**
 * Parse a modifier token and return its corresponding bitmask.
 * @param token The modifier token to parse (e.g., "Ctrl", "Alt", "Shift", "Win").
 */
UINT InputHandler::parse_modifier(const string& token) {
    string upper = token;
    transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    if (upper == "CTRL" || upper == "CONTROL") {
        return Modifier::kCtrl;
    }
    if (upper == "ALT") {
        return Modifier::kAlt;
    }
    if (upper == "SHIFT") {
        return Modifier::kShift;
    }
    if (upper == "WIN" || upper == "WINDOWS") {
        return Modifier::kWin;
    }
    return Modifier::kNone;
}


/**
 * Parse a virtual key token and return its corresponding UINT value.
 * @param token The virtual key token to parse (e.g., "A", "F1", "Space").
 */
UINT InputHandler::parse_virtual_key(const string& token) {
    string upper = token;
    transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    // single character A-Z, 0-9
    if (upper.size() == 1) {
        char ch = upper[0];
        if (ch >= 'A' && ch <= 'Z') {
            return static_cast<UINT>(ch);
        }
        if (ch >= '0' && ch <= '9') {
            return static_cast<UINT>(ch);
        }
    }

    // function keys from F1 to F24
    if (upper.rfind("F", 0) == 0 && upper.size() <= 3) {
        int num = stoi(upper.substr(1));
        if (num >= 1 && num <= 24) {
            return VK_F1 + static_cast<UINT>(num - 1);
        }
    }

    // common named keys
    if (upper == "SPACE") return VK_SPACE;
    if (upper == "TAB") return VK_TAB;
    if (upper == "ENTER" || upper == "return") return VK_RETURN;
    if (upper == "ESC" || upper == "escape") return VK_ESCAPE;
    if (upper == "UP") return VK_UP;
    if (upper == "DOWN") return VK_DOWN;
    if (upper == "LEFT") return VK_LEFT;
    if (upper == "RIGHT") return VK_RIGHT;
    if (upper == "BACKSPACE" || upper == "BACK") return VK_BACK;
    if (upper == "DELETE" || upper == "DEL") return VK_DELETE;
    if (upper == "INSERT" || upper == "INS") return VK_INSERT;
    if (upper == "HOME") return VK_HOME;
    if (upper == "END") return VK_END;
    if (upper == "PAGEUP" || upper == "PGUP") return VK_PRIOR;
    if (upper == "PAGEDOWN" || upper == "PGDN") return VK_NEXT;

    // unknown key
    return 0;
}


/**
 * Parse and store a key binding.
 * @param key_binding The key binding to parse and store.
 */
void InputHandler::parse_and_store(const KeyBinding& key_binding) {
    string spec = key_binding.key_binding;
    stringstream ss(spec);
    string token;

    UINT modifiers = Modifier::kNone;
    UINT main_vk = 0;

    vector<string> tokens;
    while (getline(ss, token, '+')) {
        tokens.push_back(trim(token));
    }

    if (!tokens.empty()) {
        main_vk = parse_virtual_key(tokens.back());
        tokens.pop_back();
    }

    for (const auto& t : tokens) {
        modifiers |= parse_modifier(t);
    }

    if (main_vk == 0) {
        // invalid binding
        return;
    }

    bindings_.push_back(ParsedBinding{main_vk, modifiers, key_binding.function, false});
}


/**
 * Register a key binding with the input handler.
 * @param key_binding The key binding to register.
 */
void InputHandler::register_key_binding(const KeyBinding& key_binding) {
    parse_and_store(key_binding);
}


/**
 * Check if the required modifiers are currently pressed.
 * @param modifiers The bitmask of required modifiers.
 * @return True if all required modifiers are pressed, false otherwise.
 */
bool InputHandler::modifiers_pressed(UINT modifiers) const {
    auto down = [](int vk) {
        return (GetAsyncKeyState(vk) & 0x8000) != 0;
    };

    if ((modifiers & Modifier::kCtrl) && !(down(VK_LCONTROL) || down(VK_RCONTROL))) {
        return false;
    }
    if ((modifiers & Modifier::kAlt) && !(down(VK_LMENU) || down(VK_RMENU))) {
        return false;
    }
    if ((modifiers & Modifier::kShift) && !(down(VK_LSHIFT) || down(VK_RSHIFT))) {
        return false;
    }
    if ((modifiers & Modifier::kWin) && !(down(VK_LWIN) || down(VK_RWIN))) {
        return false;
    }
    return true;
}


/**
 * Update the input handler to check for key presses and invoke the associated function.
 */
void InputHandler::update() {
    for (auto& binding : bindings_) {
        bool main_down = (GetAsyncKeyState(static_cast<int>(binding.vk)) & 0x8000) != 0;
        bool active = main_down && modifiers_pressed(binding.modifiers);

        if (active && !binding.was_down) {
            binding.fn();
        }

        binding.was_down = active;
    }
}