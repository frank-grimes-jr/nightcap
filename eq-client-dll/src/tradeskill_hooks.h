// Included inside nightcap::client_ui after the shared native UI helpers.
static TradeskillRepeat craft_repeat;
static InventoryNotify original_tradeskill = nullptr;
using TradeskillFrame = int (__thiscall *)(void*);
static TradeskillFrame original_tradeskill_frame = nullptr;
static void* craft_window = nullptr;
static void* craft_container = nullptr;
static uint32_t craft_recipe = 0, craft_spawn = 0;
static char craft_name[64] = {};

inline bool ReadCraftContext(void* window, void*& container, uint32_t& recipe, bool& ready) {
    if (!window || !RequestContext()) return false;
    __try {
        auto bytes = static_cast<BYTE*>(window);
        if (!bytes[0x196]) return false;
        container = *reinterpret_cast<void**>(bytes + 0x424);
        using Selected = const uint32_t* (__thiscall *)(void*);
        const auto selected = reinterpret_cast<Selected>(base + kCraftSelectedRva)(window);
        if (!container || !selected || !*selected) return false;
        recipe = *selected;
        const auto button = *reinterpret_cast<BYTE**>(bytes + 0x278);
        ready = button && button[0x1a] && *reinterpret_cast<int*>(base + 0xA635AC) == 0;
        return true;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline void NativeCraftClick(void* window, size_t offset) {
    __try {
        const auto control = *reinterpret_cast<void**>(static_cast<BYTE*>(window) + offset);
        if (!control) { craft_repeat.NotDispatched(); return; }
        const int before = *reinterpret_cast<int*>(base + 0xA635AC);
        original_tradeskill(window, control, 1, nullptr);
        // The native combine increments this counter only on the send path.
        // A local class/cursor rejection is known unsent, so allow a new run.
        if (offset == 0x278 && before == 0 && *reinterpret_cast<int*>(base + 0xA635AC) == 0) {
            craft_repeat.NotDispatched();
            LootNotice("Crafting stopped before an attempt. Check the native recipe message and clear your cursor.");
        }
    } __except(EXCEPTION_EXECUTE_HANDLER) { craft_repeat.Stop(); }
}
inline bool ConsumeCraftReply(const char* message) {
    if (!message || strncmp(message, "[NCTS1]|", 8)) return false;
    uint32_t spawn=0, recipe=0;
    bool attempted=false;
    if (!ParseTradeskillReply(message, spawn, recipe, attempted)) return true;
    const bool was_active = craft_repeat.Active();
    if (craft_repeat.Ack(GetTickCount64(), spawn, recipe, attempted) && was_active && !craft_repeat.Active())
        LootNotice("Crafting stopped. Check the recipe requirements and remaining materials.");
    return true;
}
inline int __fastcall TradeskillWindowHook(void* self, void*, void* sender, uint32_t message, void* data) {
    if (self && sender && IsArmorControl(self, sender, "NC_CraftStop")) {
        if (message == 1) { craft_repeat.Stop(); LootNotice("Crafting stopped after the current attempt."); }
        return 1;
    }
    if (self && sender && IsArmorControl(self, sender, "NC_CraftAll")) {
        if (message != 1) return 1;
        void* container = nullptr;
        uint32_t recipe = 0, spawn = 0;
        bool ready = false;
        char name[64] = {};
        if (!ReadIdentity(spawn, name) || !ReadCraftContext(self, container, recipe, ready) || !ready ||
            !craft_repeat.Start(GetTickCount64(), spawn, recipe)) {
            LootNotice(craft_repeat.Uncertain()
                ? "Crafting completion could not be confirmed. Zone or relog before starting another run."
                : "Select a recipe and clear your cursor. Wait for any current attempt to finish.");
            return 1;
        }
        craft_window = self; craft_container = container; craft_recipe = recipe; craft_spawn = spawn;
        memcpy(craft_name, name, sizeof(craft_name));
        LootNotice("Crafting all available materials. Click Stop to end the run.");
        NativeCraftClick(self, 0x278);
        return 1;
    }
    // A manual recipe, search, close or experiment action ends repetition.
    // Preserve the outstanding result so Stop/Craft All cannot replay it.
    if (message == 1 || message == 3 || message == 6 || message == 15) {
        craft_repeat.Stop();
        if (craft_repeat.Pending() && self && sender && IsArmorControl(self, sender, "CombineButton")) return 1;
    }
    return original_tradeskill(self, sender, message, data);
}
inline int __fastcall TradeskillFrameHook(void* self, void*) {
    const int result = original_tradeskill_frame(self);
    if (!craft_repeat.Active() && !craft_repeat.Pending()) return result;
    void* container = nullptr;
    uint32_t recipe = 0, spawn = 0;
    bool ready = false;
    char name[64] = {};
    const bool same = self == craft_window && ReadIdentity(spawn, name) &&
        spawn == craft_spawn && !strcmp(name, craft_name) &&
        ReadCraftContext(self, container, recipe, ready) && container == craft_container && recipe == craft_recipe;
    const auto action = craft_repeat.Pulse(GetTickCount64(), ready, same);
    if (action == TradeskillRepeat::Action::Craft) NativeCraftClick(self, 0x278);
    else if (action == TradeskillRepeat::Action::Inventory) NativeCraftClick(self, 0x240);
    else if (action == TradeskillRepeat::Action::Stopped)
        LootNotice(craft_repeat.Uncertain()
            ? "Crafting completion could not be confirmed. Zone or relog before starting another run."
            : "Crafting stopped. Check your window, inventory space and connection before starting again.");
    return result;
}
