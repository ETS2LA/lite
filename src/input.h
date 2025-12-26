#pragma once

#include <functional>
#include <string>
#include <vector>

#include <windows.h>


/**
 * Key binding structure defining a key and its associated function.
 * @param key_binding The key to bind (can include modifiers like Ctrl, Alt, Shift, e.g., "Ctrl+X").
 * @param function The function to invoke when the key is pressed.
 */
struct KeyBinding {
    std::string key_binding;
    std::function<void()> function;
};


class InputHandler {
public:
    void register_key_binding(const KeyBinding& key_binding);
    void update();

private:
    /**
     * Modifier bitmask definitions.
     */
    enum Modifier : UINT {
        kNone   = 0,
        kCtrl   = 1u << 0,
        kAlt    = 1u << 1,
        kShift  = 1u << 2,
        kWin    = 1u << 3,
    };

    /**
     * Parsed binding structure storing the parsed key binding information.
     * @param vk The virtual key code for the main key.
     * @param modifiers The bitmask of required modifiers.
     * @param fn The callback function to invoke.
     * @param was_down Track the previous state to fire on key-down.
     */
    struct ParsedBinding {
        UINT vk;
        UINT modifiers;
        std::function<void()> fn;
        bool was_down = false;
    };

    static UINT parse_virtual_key(const std::string& token);
    static UINT parse_modifier(const std::string& token);
    static std::string trim(const std::string& text);
    void parse_and_store(const KeyBinding& key_binding);
    bool modifiers_pressed(UINT modifiers) const;

    std::vector<ParsedBinding> bindings_;
};