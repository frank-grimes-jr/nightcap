#pragma once
#include "ui_state.h"
#include "pet_state.h"
#include "pet_management.h"
#include "verified_patch.h"
#include "spell_access.h"
#include "advanced_loot_ui.h"
#include "advanced_loot_icons.h"
#include "tradeskill_repeat.h"
#include "bazaar_panel_controller.h"

namespace nightcap {
namespace client_ui {
inline void ResetMonkReuse();
inline bool ConsumeBazaarReply(const char *message);
inline void ResetBazaarPanel();
// All offsets and instruction boundaries belong to the pinned May 2013 RoF2
// executable. They are also guarded by the generated signed patch catalog.
struct EqString { void* rep; };
static_assert(sizeof(EqString) == 4, "RoF2 CXStr wrapper is x86");
using AssignString = EqString* (__thiscall *)(EqString*, const char*);
// Only the two final skin-name assignments in the native UI loader are
// redirected. Character window positions, hotbars and other INI reads stay native.
static AssignString skin_assign = nullptr;
inline EqString* __fastcall SkinHook(EqString* self, void*, const char*) {
    return skin_assign(self, "nightcap");
}
using GetLabel = bool (__cdecl *)(int, EqString*, bool*, unsigned long*);
// Native channel packet sender. Unlike InterpretCmd / Say, this does not echo
// text, touch the command buffer/history, or address the current NPC target.
using SendRequest = void (__thiscall *)(void*, int, const char*, const char*, int);
static SendRequest send_request = nullptr;
using DisplayChat = void (__thiscall *)(void*, const char*, int, bool, bool);
using SetGameState = void (__thiscall *)(void*, int);
using UpdateAA = void (__thiscall *)(void*);
using GetRowData = uint32_t (__thiscall *)(void*, int);
using SetCellText = void (__thiscall *)(void*, int, int, const EqString*);
static uintptr_t base = 0;
static const char* install_failure = "not_started";
static UIState state;
static PetState pets;
static PetManagement pet_management;
using InventoryNotify = int (__thiscall *)(void*, void*, uint32_t, void*);
static InventoryNotify original_inventory = nullptr;
static InventoryNotify original_pet_window = nullptr;
static InventoryNotify original_merchant = nullptr;
using PetAvailable = bool (__thiscall *)(void*, unsigned);
static PetAvailable original_pet_available = nullptr;
static ULONGLONG next_management_refresh = 0;
static ULONGLONG management_received = 0;
static ULONGLONG next_pet_refresh = 0;
static GetLabel original_label = nullptr;
static DisplayChat original_chat = nullptr;
static SetGameState original_state = nullptr;
using InterpretCommand = void (__thiscall *)(void*, void*, const char*);
static InterpretCommand original_command = nullptr;
static UpdateAA original_aa = nullptr;
using AAFilter = bool (__thiscall *)(void*, const void*);
static AAFilter original_aa_filter = nullptr;
static InventoryNotify original_aa_notify = nullptr;
static bool aa_filter_active = false;
static ULONGLONG next_refresh = 0;
using SpellLevel = uint8_t (__thiscall *)(void*, int);
static SpellLevel original_spell_level = nullptr;
using SpellMenuFrame = int (__thiscall *)(void*);
using RebuildSpellMenu = void (__thiscall *)(void*);
using CurrentSpellProfile = void* (__thiscall *)(void*);
static SpellMenuFrame original_spell_menu_frame = nullptr;
static RebuildSpellMenu rebuild_spell_menu = nullptr;
static CurrentSpellProfile current_spell_profile = nullptr;
static bool spell_menu_dirty = true;
static bool spell_menu_refreshing = false;
inline void RequestRefresh();
inline const void*& ActiveSpellItem() {
    static thread_local const void* item = nullptr;
    return item;
}

// Keep SEH and C++ object lifetimes separate. No memory dereference is based on
// a server-provided pointer or row index.
inline bool ReadIdentity(uint32_t& spawn, char (&name)[64]) {
    __try {
        const uintptr_t eq = *reinterpret_cast<uintptr_t*>(base + 0xA67CCC);
        const uintptr_t player = *reinterpret_cast<uintptr_t*>(base + 0x9D2630);
        if (!eq || !player || *reinterpret_cast<int*>(eq + 0x5C8) != 5) return false;
        spawn = *reinterpret_cast<uint32_t*>(player + 0x148);
        memcpy(name, reinterpret_cast<void*>(player + 0xA4), sizeof(name));
        return memchr(name, 0, sizeof(name)) != nullptr;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline bool CurrentIdentity() {
    uint32_t spawn = 0;
    char name[64] = {};
    return ReadIdentity(spawn, name) && state.Matches(spawn, name);
}
inline uint8_t __fastcall SpellLevelHook(void* spell, void*, int queried_class) {
    // Only replace the local character's primary-class access query. Inspection
    // class lists use the separate canonical hooks below; queries before identity
    // arrives retain native behavior.
    const bool current = CurrentIdentity();
    if (!current) RequestRefresh();
    if (current && queried_class == static_cast<int>(state.PrimaryClass())) {
        __try {
            return HeldSpellLevel(*reinterpret_cast<uint32_t*>(static_cast<BYTE*>(spell)+0x174), state.ClassMask());
        } __except(EXCEPTION_EXECUTE_HANDLER) { return 255; }
    }
    return original_spell_level(spell, queried_class);
}
// Only the native spellbook's scribing-level call uses this projection. The
// shared level accessor, inspection, menu, memorization and casting keep the
// original held-class level. Missing identity must not grant early scribing.
inline uint8_t __fastcall ScribeSpellLevelHook(void* spell, void*, int queried_class) {
    if (!CurrentIdentity()) { RequestRefresh(); return 255; }
    if (queried_class != static_cast<int>(state.PrimaryClass())) return 255;
    __try {
        const auto level = HeldSpellLevel(
            *reinterpret_cast<uint32_t*>(static_cast<BYTE*>(spell)+0x174), state.ClassMask());
        return level == 255 ? 255 : 1;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return 255; }
}
inline bool SpellMenuContextReady(void* window) {
    if (!window || !current_spell_profile || !CurrentIdentity()) return false;
    __try {
        if (window != *reinterpret_cast<void**>(base+0x91FC84) ||
            !*reinterpret_cast<void**>(base+0xA646B0) ||
            !*reinterpret_cast<void**>(base+0x11D391C)) return false;
        auto character = *reinterpret_cast<BYTE**>(base+0x9D261C);
        if (!character) return false;
        const auto vbase = *reinterpret_cast<const int32_t**>(character+8);
        if (!vbase) return false;
        // Same virtual-base/profile traversal as the native menu builder.
        auto profile = static_cast<BYTE*>(current_spell_profile(character+vbase[1]+12));
        return profile && profile[0x3374] == state.PrimaryClass();
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline int __fastcall SpellMenuFrameHook(void* window, void*) {
    // The native menu caches both labels and ordering before class metadata
    // arrives. Rebuild on its own UI frame, never inside snapshot dispatch.
    if (spell_menu_dirty && !spell_menu_refreshing && rebuild_spell_menu && SpellMenuContextReady(window)) {
        spell_menu_dirty = false;
        spell_menu_refreshing = true;
        __try { rebuild_spell_menu(window); }
        __finally { spell_menu_refreshing = false; }
    }
    return original_spell_menu_frame(window);
}
inline uint32_t __fastcall MerchantClassesHook(void* item, void*, bool flag1, bool flag2) {
    using ItemClasses = uint32_t (__thiscall *)(void*, bool, bool);
    using ItemType = int (__thiscall *)(void*);
    using ItemSpell = int (__thiscall *)(void*, int);
    const auto stock = reinterpret_cast<ItemClasses>(base+kItemClassesRva)(item,flag1,flag2);
    if (!CurrentIdentity()) { RequestRefresh(); return stock; }
    if (!stock) return stock;
    __try {
        const bool scroll = reinterpret_cast<ItemType>(base+kItemTypeRva)(item)==20;
        const auto id = scroll ? reinterpret_cast<ItemSpell>(base+kItemSpellRva)(item,4) : 0;
        return MerchantClassMask(stock,state.PrimaryClass(),state.ClassMask(),scroll,id);
    } __except(EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
// These hooks belong only to the two native scroll-inspection class lists.
// Item masks can contain legacy extra classes; the list must use spell
// eligibility, without projecting a held class onto the character's base class.
inline uint32_t __fastcall InspectionClassesHook(void* item, void*, bool flag1, bool flag2) {
    if (!item) return 0;
    using ItemClasses = uint32_t (__thiscall *)(void*, bool, bool);
    using ItemType = int (__thiscall *)(void*);
    using ItemSpell = int (__thiscall *)(void*, int);
    __try {
        const auto stock = reinterpret_cast<ItemClasses>(base+kItemClassesRva)(item,flag1,flag2);
        if (!stock || reinterpret_cast<ItemType>(base+kItemTypeRva)(item) != 20) return stock;
        const auto spell = reinterpret_cast<ItemSpell>(base+kItemSpellRva)(item,4);
        return NightcapSpellClasses::Mask(spell);
    } __except(EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
inline uint8_t __fastcall InspectionSpellLevelHook(void* spell, void*, int queried_class) {
    if (!spell) return 255;
    __try {
        return NightcapSpellClasses::Level(
            *reinterpret_cast<uint32_t*>(static_cast<BYTE*>(spell)+0x174), queried_class);
    } __except(EXCEPTION_EXECUTE_HANDLER) { return 255; }
}
inline uint32_t ScribeClassMask(uint32_t stock, const void* item, bool flag1, bool flag2) {
    if (!stock || !item || item != ActiveSpellItem() || !flag1 || flag2 || !CurrentIdentity()) return stock;
    using ItemType = int (__thiscall *)(void*);
    using ItemSpell = int (__thiscall *)(void*, int);
    __try {
        if (reinterpret_cast<ItemType>(base+kItemTypeRva)(const_cast<void*>(item)) != 20) return stock;
        const auto spell = reinterpret_cast<ItemSpell>(base+kItemSpellRva)(const_cast<void*>(item),4);
        return MerchantClassMask(stock,state.PrimaryClass(),state.ClassMask(),true,spell);
    } __except(EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
inline BYTE __fastcall CanUseSpellItem(void* character, void*, const void* item_ref, bool required, bool output) {
    using CanUse = BYTE (__thiscall *)(void*, const void*, bool, bool);
    const auto original = reinterpret_cast<CanUse>(base+kCanUseItemRva);
    const void* item = nullptr;
    if (!character || !item_ref) return 0;
    __try { item = *reinterpret_cast<const void* const*>(item_ref); }
    __except(EXCEPTION_EXECUTE_HANDLER) { return 0; }
    if (!item) return 0;
    if (!CurrentIdentity()) RequestRefresh();
    const auto previous = ActiveSpellItem();
    ActiveSpellItem() = item;
    BYTE result = 0;
    __try { result = original(character,item_ref,required,output); }
    __finally { ActiveSpellItem() = previous; }
    return result;
}
inline void* RequestContext() {
    uint32_t spawn = 0;
    char name[64] = {};
    if (!ReadIdentity(spawn, name)) return nullptr;
    __try {
        // The native serializer also reads the character profile and connection.
        if (!*reinterpret_cast<void**>(base+0x9D261C) ||
            !*reinterpret_cast<void**>(base+0x9D25AC)) return nullptr;
        return *reinterpret_cast<void**>(base+0xA67CCC);
    } __except(EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
}
inline bool ExecuteUIRequest(const std::string& request) {
    if (!send_request || request.empty() || request.size() > 128 || request[0] != '#') return false;
    auto eq = RequestContext();
    if (!eq) return false;
    // Keep the existing server command dispatcher/validation, but bypass the
    // client interpreter and Say's local echo. '#' requests never broadcast.
    send_request(eq, 8, nullptr, request.c_str(), 0);
    return true;
}
inline void LootNotice(const char* message) {
    auto eq = RequestContext();
    if (eq && original_chat) original_chat(eq, message, 13, false, false);
}
inline void LootPulse() {
    uint32_t spawn = 0;
    char name[64] = {};
    if (!ReadIdentity(spawn, name)) spawn = 0;
    AdvancedLootUI::Pulse(GetTickCount64(), spawn, name);
}
inline void __fastcall CommandHook(void* self, void*, void* player, const char* text) {
    const char* command = text;
    if (command) {
        while (*command == ' ' || *command == '\t') ++command;
        if (_strnicmp(command, "/advloot", 8) == 0 &&
            (!command[8] || command[8] == ' ' || command[8] == '\t')) {
            command += 8;
            while (*command == ' ' || *command == '\t') ++command;
            LootPulse();
            if (*command) LootNotice("Use /advloot to open the window. Manage filters and loot options there.");
            else AdvancedLootUI::Toggle();
            return;
        }
    }
    original_command(self, player, text);
}
inline void RequestRefresh() {
    if (GetTickCount64() < next_refresh) return;
    if (ExecuteUIRequest("#nightcapui refresh")) {
        // Older servers still supply class metadata; only paired servers opt in
        // to the new recommendation messages. Both requests are silent/bounded.
        ExecuteUIRequest("#nightcapui recommended");
        next_refresh = GetTickCount64() + 5000;
    }
}
inline bool CurrentPetIdentity() {
    uint32_t spawn = 0;
    char name[64] = {};
    return ReadIdentity(spawn, name) && pets.Matches(spawn, name);
}
inline void RequestPetRefresh() {
    if (GetTickCount64() < next_pet_refresh) return;
    if (ExecuteUIRequest("#nightcappet view")) next_pet_refresh = GetTickCount64() + 5000;
}
inline bool IsArmorControl(void* window, void* sender, const char* name) {
    using Child = void* (__thiscall *)(void*, const EqString*);
    auto assign = reinterpret_cast<AssignString>(base + kUIStringAssignRva);
    EqString id{};
    assign(&id, name);
    void* child = reinterpret_cast<Child>(base + kUIChildRva)(window, &id);
    assign(&id, "");
    return child && child == sender;
}
inline bool CurrentManagementIdentity() {
    uint32_t spawn = 0;
    char name[64] = {};
    return ReadIdentity(spawn, name) && pet_management.Matches(spawn, name) &&
        GetTickCount64() - management_received < 5000;
}
#include "tradeskill_hooks.h"
inline int __fastcall MerchantWindowHook(void* self, void*, void* sender, uint32_t message, void* data) {
    // Resolve against this window each time: no cached child survives a skin
    // reload. Consume only our control; all stock merchant notifications pass on.
    if (self && sender && IsArmorControl(self, sender, "NC_MerchantSellAll")) {
        if (message == 1) ExecuteUIRequest("#sellall");
        return 1;
    }
    return original_merchant(self, sender, message, data);
}
inline void RequestManagementRefresh() {
    if (GetTickCount64() < next_management_refresh) return;
    if (ExecuteUIRequest("#nightcappet manage")) next_management_refresh = GetTickCount64() + 3000;
}
__declspec(noinline) inline bool __fastcall PetAvailablePolicy(void* self, void*, unsigned command) {
    // Let the authoritative server validate each pet's permissions. RoF2's
    // cached singular-pet flags cannot describe a mixed class roster.
    if (command < 34 && command != 30 && CurrentManagementIdentity() && pet_management.HasPets()) return true;
    return original_pet_available(self, command);
}
// RoF2's pet-arrival loop (VA 0x70F74F) calls the preference getter next
// without reloading ECX. Its original leaf predicate preserves ECX/EDX;
// an ordinary C++ hook may clobber them even with the correct __thiscall ABI.
__declspec(naked) inline bool __fastcall PetAvailableHook(void*, void*, unsigned) {
    __asm {
        push ecx
        push edx
        push dword ptr [esp + 12]
        call PetAvailablePolicy
        pop edx
        pop ecx
        ret 4
    }
}
inline bool NativePetCommand(void* window, void* sender, unsigned& command) {
    // CPetInfoWnd maps configurable native buttons into this capability array.
    // Mapping is pinned by the exact-client verifier (GetCommand at 0x70F1C0).
    static constexpr unsigned commands[] = {0,1,2,3,4,5,6,9,31,12,15,18,21,24,27,28,29,30};
    __try {
        const auto controls = reinterpret_cast<void**>(static_cast<BYTE*>(window)+0x26C);
        for (unsigned i = 0; i < 18; ++i) {
            if (sender && controls[i] == sender) { command = commands[i]; return command != 30; }
        }
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    return false;
}
inline int __fastcall PetWindowHook(void* self, void*, void* sender, uint32_t message, void* data) {
    if (sender) {
        std::string request;
        bool handled = false;
        if (IsArmorControl(self, sender, "NCPM_All")) { request = pet_management.AllCommand(); handled = true; }
        for (unsigned row = 0; row < 3; ++row) {
            const std::string id = "NCPM_Pet" + std::to_string(row);
            if (IsArmorControl(self, sender, id.c_str()) || IsArmorControl(self, sender, (id+"Name").c_str())) {
                request = pet_management.SelectCommand(row); handled = true;
            }
        }
        const unsigned commands[] = {2,4,5,12,6,9,31,28,15,18,24,21,0,29};
        for (unsigned index = 0; index < 14; ++index) {
            const std::string id = "NCPM_Command" + std::to_string(index);
            if (IsArmorControl(self, sender, id.c_str())) { request = pet_management.OrderCommand(commands[index]); handled = true; }
        }
        if (handled) {
            // Native drag notification 0x17 assumes one of its own slots and
            // otherwise creates a slot-0 hotbutton. Never forward custom senders.
            if (message == 1) {
                if (CurrentManagementIdentity()) ExecuteUIRequest(request);
                else RequestManagementRefresh();
            }
            return 1;
        }
        unsigned command = 0;
        if (message == 1 && NativePetCommand(self, sender, command)) {
            if (CurrentManagementIdentity()) ExecuteUIRequest(pet_management.OrderCommand(command));
            else RequestManagementRefresh();
            return 1;
        }
    }
    return original_pet_window(self, sender, message, data);
}
inline int __fastcall InventoryHook(void* self, void*, void* sender, uint32_t message, void* data) {
    if (message == 1 && sender) {
        if (IsArmorControl(self, sender, "NCPA_Refresh")) { RequestPetRefresh(); return 1; }
        if (IsArmorControl(self, sender, "NCPA_Previous")) { pets.Next(-1); return 1; }
        if (IsArmorControl(self, sender, "NCPA_Next")) { pets.Next(1); return 1; }
        if (IsArmorControl(self, sender, "NCPA_PagePrevious")) { pets.NextPage(-1); return 1; }
        if (IsArmorControl(self, sender, "NCPA_PageNext")) { pets.NextPage(1); return 1; }
        const char* ids[] = {"Equip", "Remove", "Inspect"};
        const char* verbs[] = {"equip", "remove", "inspect"};
        for (unsigned action = 0; action < 3; ++action) {
            for (unsigned slot = 0; slot < 8; ++slot) {
                const std::string id = std::string("NCPA_") + ids[action] + std::to_string(slot);
                if (!IsArmorControl(self, sender, id.c_str())) continue;
                if (CurrentPetIdentity()) ExecuteUIRequest(pets.Command(verbs[action], slot));
                else RequestPetRefresh();
                return 1;
            }
        }
    }
    return original_inventory(self, sender, message, data);
}
inline bool __cdecl LabelHook(int type, EqString* output, bool* override_color, unsigned long* color) {
    // The always-visible HUD requests identity too; opening Inventory/AA is not
    // a prerequisite for a correct shop or spellbook. Requests are throttled.
    if (!CurrentIdentity()) RequestRefresh();
    if (!CurrentManagementIdentity()) RequestManagementRefresh();
    LootPulse();
    if (type >= 10030 && type <= 10033) {
        const std::string text = !CurrentManagementIdentity() ? "Pets loading" :
            type == 10030 ? pet_management.ScopeText() : pet_management.RowText(type-10031);
        reinterpret_cast<AssignString>(base + kUIStringAssignRva)(output, text.c_str());
        if (override_color) *override_color = false;
        return true;
    }
    if (type >= 10020 && type <= 10028) {
        const bool current = CurrentPetIdentity();
        if (!current) RequestPetRefresh();
        const std::string text = !current ? "Pet armor loading" : type == 10020 ? pets.TitleText() : pets.SlotText(type - 10021);
        reinterpret_cast<AssignString>(base + kUIStringAssignRva)(output, text.c_str());
        if (override_color) *override_color = false;
        return true;
    }
    if (type != 10001) return original_label(type, output, override_color, color);
    const bool current = CurrentIdentity();
    if (!current) RequestRefresh();
    const std::string text = current ? state.Classes() : "Classes loading";
    reinterpret_cast<AssignString>(base + kUIStringAssignRva)(output, text.c_str());
    if (override_color) *override_color = false;
    return true;
}
inline void __fastcall ChatHook(void* self, void*, const char* message, int color, bool log, bool convert) {
    LootPulse();
    if (ConsumeCraftReply(message)) return;
    if (ConsumeBazaarReply(message)) return;
    if (message && AdvancedLootUI::Consume(message)) return;
    if (pet_management.Consume(message)) { management_received = GetTickCount64(); return; }
    if (state.Consume(message)) {
        if (message[7] == 'S') spell_menu_dirty = true;
        return;
    }
    if (pets.Consume(message)) return;
    original_chat(self, message, color, log, convert);
}
inline void __fastcall StateHook(void* self, void*, int next) {
    if (next != 5) ResetMonkReuse();
    if (next != 5) ResetBazaarPanel();
    if (next != 5) { craft_repeat.Reset(); craft_window = nullptr; craft_container = nullptr; }
    if (next != 5) AdvancedLootUI::Reset();
    if (next != 5) { state.Clear(); spell_menu_dirty = true; pets.Clear(); pet_management.Clear(); next_refresh = 0; next_pet_refresh = 0; next_management_refresh = 0; management_received = 0; }
    original_state(self, next);
    if (next == 5) RequestRefresh();
}
inline void* AAChild(void* window, const char* name) {
    using Child = void* (__thiscall *)(void*, const EqString*);
    auto assign = reinterpret_cast<AssignString>(base+kUIStringAssignRva);
    EqString id{}; assign(&id,name);
    void* child = reinterpret_cast<Child>(base+kUIChildRva)(window,&id);
    assign(&id,""); return child;
}
#include "bazaar_panel_hooks.h"
inline void ResetBazaarPanel(){bazaar_panel.Close();bazaar_next_render=0;}
inline bool AARecommendedChecked(void* window) {
    __try {
        auto button=AAChild(window,"NC_AARecommended");
        // Native TrainFilter reads CButtonWnd::Checked at +0x1e4.
        return button && *reinterpret_cast<BYTE*>(static_cast<BYTE*>(button)+0x1e4)!=0;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline void ResetAARecommended(void* window) {
    __try {
        auto button=AAChild(window,"NC_AARecommended");
        if (button) *reinterpret_cast<BYTE*>(static_cast<BYTE*>(button)+0x1e4)=0;
    } __except(EXCEPTION_EXECUTE_HANDLER) {}
}
inline bool __fastcall AAFilterHook(void* self, void*, const void* rank) {
    if (!original_aa_filter(self,rank)) return false;
    if (!aa_filter_active) return true;
    __try { return rank && state.Recommended(*static_cast<const uint32_t*>(rank)); }
    __except(EXCEPTION_EXECUTE_HANDLER) { return true; }
}
inline void CallOriginalAA(void* self) {
    const bool previous=aa_filter_active;
    aa_filter_active=CurrentIdentity() && state.RecommendationsReady() && AARecommendedChecked(self);
    __try { original_aa(self); }
    __finally { aa_filter_active=previous; }
}
// Native AA +/- controls use a byte and step ten without saturating.
inline void ClampAAButtonBoundary(void* self, void* sender) {
    __try {
        auto window=static_cast<BYTE*>(self);
        auto character=*reinterpret_cast<BYTE**>(base+0x9D261C);
        if (!window || !sender || !character) return;
        BYTE& percent=character[0x2081];
        if (sender==*reinterpret_cast<void**>(window+0x24C) && percent>0 && percent<10) percent=10;
        else if (sender==*reinterpret_cast<void**>(window+0x250) && percent>90 && percent<100) percent=90;
    } __except(EXCEPTION_EXECUTE_HANDLER) {}
}
inline bool MatchAAAllocationControls() {
    __try {
        if (memcmp(reinterpret_cast<void*>(base+kUIAAExpResetRva),kExpectedUIAAExpReset,sizeof(kExpectedUIAAExpReset)) ||
            memcmp(reinterpret_cast<void*>(base+kUIAAExpMinusLevelRva),kExpectedUIAAExpMinusLevel,sizeof(kExpectedUIAAExpMinusLevel)) ||
            memcmp(reinterpret_cast<void*>(base+kUIAAExpPlusLevelRva),kExpectedUIAAExpPlusLevel,sizeof(kExpectedUIAAExpPlusLevel))) return false;
        // Each native sequence has one HIGHLOW-relocated character global.
        BYTE minus[sizeof(kExpectedUIAAExpMinusNative)],plus[sizeof(kExpectedUIAAExpPlusNative)];
        memcpy(minus,kExpectedUIAAExpMinusNative,sizeof(minus));
        memcpy(plus,kExpectedUIAAExpPlusNative,sizeof(plus));
        const auto character_global=static_cast<uint32_t>(base+0x9D261C);
        memcpy(minus+9,&character_global,4);memcpy(plus+9,&character_global,4);
        return !memcmp(reinterpret_cast<void*>(base+kUIAAExpMinusNativeRva),minus,sizeof(minus)) &&
            !memcmp(reinterpret_cast<void*>(base+kUIAAExpPlusNativeRva),plus,sizeof(plus));
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline bool InstallAAAllocationControls() {
    if (!MatchAAAllocationControls()) return false;
    BYTE reset[sizeof(kExpectedUIAAExpReset)],minus[sizeof(kExpectedUIAAExpMinusLevel)],plus[sizeof(kExpectedUIAAExpPlusLevel)];
    memcpy(reset,kExpectedUIAAExpReset,sizeof(reset));reset[4]=0;
    memcpy(minus,kExpectedUIAAExpMinusLevel,sizeof(minus));minus[4]=1;
    memcpy(plus,kExpectedUIAAExpPlusLevel,sizeof(plus));plus[4]=1;
    return WriteVerifiedPatch(reinterpret_cast<BYTE*>(base+kUIAAExpResetRva),kExpectedUIAAExpReset,reset,sizeof(reset)) &&
        WriteVerifiedPatch(reinterpret_cast<BYTE*>(base+kUIAAExpMinusLevelRva),kExpectedUIAAExpMinusLevel,minus,sizeof(minus)) &&
        WriteVerifiedPatch(reinterpret_cast<BYTE*>(base+kUIAAExpPlusLevelRva),kExpectedUIAAExpPlusLevel,plus,sizeof(plus));
}
inline void __fastcall AAHook(void* self, void*);
inline int __fastcall AANotifyHook(void* self, void*, void* sender, uint32_t message, void* data) {
    if (self && sender && IsArmorControl(self,sender,"NC_AARecommended")) {
        if (message==1) { RequestRefresh(); AAHook(self,nullptr); }
        return 1;
    }
    if (self && sender && message==1 && IsArmorControl(self,sender,"ResetFilter")) ResetAARecommended(self);
    if (self && sender && message==1) ClampAAButtonBoundary(self,sender);
    return original_aa_notify(self,sender,message,data);
}
inline bool ReadList(void* window, unsigned index, void*& list, int& rows, int& class_column, int& recommendation_column) {
    __try {
        list = reinterpret_cast<void**>(static_cast<BYTE*>(window) + 0x2A0)[index];
        if (!list) return false;
        rows = *reinterpret_cast<int*>(static_cast<BYTE*>(list) + 0x1D8);
        if (rows < 0 || rows > 32768) return false;
        const int columns = *reinterpret_cast<int*>(static_cast<BYTE*>(list) + 0x1E8);
        const BYTE* entries = *reinterpret_cast<BYTE**>(static_cast<BYTE*>(list) + 0x1EC);
        if (columns < 1 || columns > 32 || !entries) return false;
        class_column = recommendation_column = -1;
        for (int i = 0; i < columns; ++i) {
            const BYTE* rep = *reinterpret_cast<BYTE* const*>(entries + i*0x3C + 0x18);
            if (!rep || *reinterpret_cast<const uint32_t*>(rep+0x0C) != 0) continue;
            const auto length=*reinterpret_cast<const uint32_t*>(rep+0x08);
            const auto capacity=*reinterpret_cast<const uint32_t*>(rep+0x04);
            if (length==5 && capacity>=6 && memcmp(rep+0x14,"Class",6)==0) {
                if (class_column!=-1) return false;
                class_column=i;
            }
            if (length==11 && capacity>=12 && memcmp(rep+0x14,"Recommended",12)==0) {
                if (recommendation_column!=-1) return false;
                recommendation_column=i;
            }
        }
        return class_column != -1;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline void __fastcall AAHook(void* self, void*) {
    CallOriginalAA(self);
    const bool current = CurrentIdentity();
    if (!current) RequestRefresh();
    auto assign = reinterpret_cast<AssignString>(base + kUIStringAssignRva);
    auto row_data = reinterpret_cast<GetRowData>(base + kUIRowDataRva);
    auto set_text = reinterpret_cast<SetCellText>(base + kUICellTextRva);
    for (unsigned index = 0; index < 4; ++index) {
        void* list = nullptr;
        int rows = 0, class_column = -1, recommendation_column = -1;
        if (!ReadList(self, index, list, rows, class_column, recommendation_column)) continue;
        for (int row = 0; row < rows; ++row) {
            const std::string text = current ? state.AAClasses(row_data(list, row)) : "Unknown";
            EqString value{};
            assign(&value, text.c_str());
            set_text(list, row, class_column, &value);
            if (recommendation_column!=-1) {
                const auto why=current ? state.Recommendation(row_data(list,row)) : "";
                assign(&value,why.c_str());
                set_text(list,row,recommendation_column,&value);
            }
            // Release through the client's allocator/refcount, never our CRT.
            assign(&value, "");
        }
    }
    const char* note = !current || !state.RecommendationsReady() ? "Recommendations unavailable - showing all abilities." :
        !state.RecommendationCount() ? "Starter recommendations complete. Clear Recommended to explore other abilities." :
        "Later needs a supporting skill or pet. Can Purchase also requires enough points. Clear filters to browse all.";
    auto label=AAChild(self,"NC_AARecommendationStatus");
    if (label) {
        using Text = void (__thiscall *)(void*, const EqString*);
        EqString value{}; assign(&value,note);
        reinterpret_cast<Text>((*static_cast<void***>(label))[0x124/4])(label,&value);
        assign(&value,"");
    }
}

template<size_t N> inline void* EntryHook(uintptr_t address, const BYTE (&expected)[N], void* hook) {
    static_assert(N >= 5, "whole instructions must cover the jump");
    BYTE* trampoline = static_cast<BYTE*>(VirtualAlloc(nullptr, N + 5, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    if (!trampoline) return nullptr;
    memcpy(trampoline, expected, N);
    trampoline[N] = 0xE9;
    const int32_t back = static_cast<int32_t>(address + N - (reinterpret_cast<uintptr_t>(trampoline) + N + 5));
    memcpy(trampoline + N + 1, &back, sizeof(back));
    DWORD previous = 0;
    if (!VirtualProtect(trampoline, N + 5, PAGE_EXECUTE_READ, &previous) ||
        !FlushInstructionCache(GetCurrentProcess(), trampoline, N + 5)) {
        VirtualFree(trampoline, 0, MEM_RELEASE);
        return nullptr;
    }
    BYTE replacement[N];
    memset(replacement, 0x90, N);
    replacement[0] = 0xE9;
    const int32_t destination = static_cast<int32_t>(reinterpret_cast<uintptr_t>(hook) - (address + 5));
    memcpy(replacement + 1, &destination, sizeof(destination));
    if (!WriteVerifiedPatch(reinterpret_cast<BYTE*>(address), expected, replacement, N)) {
        VirtualFree(trampoline, 0, MEM_RELEASE);
        return nullptr;
    }
    return trampoline; // proxy is pinned for the process lifetime
}
// These three pinned prologues contain push <absolute SEH table>. Windows
// rebases their HIGHLOW entries when eqgame does not load at its preferred base.
// Rebase only that verified operand; all other bytes still must match exactly.
template<size_t N> inline bool RebaseSEH(const BYTE (&original)[N], uintptr_t image_base, BYTE (&expected)[N]) {
    static_assert(N >= 7, "SEH prologue needs its complete absolute operand");
    if (original[0] != 0x6A || original[1] != 0xFF || original[2] != 0x68) return false;
    memcpy(expected, original, N);
    uint32_t table = 0;
    memcpy(&table, original + 3, sizeof(table));
    table += static_cast<uint32_t>(image_base) - 0x00400000u;
    memcpy(expected + 3, &table, sizeof(table));
    return true;
}
template<size_t N> inline bool MatchSEH(uintptr_t address, const BYTE (&original)[N], uintptr_t image_base) {
    BYTE expected[N];
    if (!RebaseSEH(original, image_base, expected)) return false;
    __try { return memcmp(reinterpret_cast<void*>(address), expected, N) == 0; }
    __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template<size_t N> inline void* SEHEntryHook(uintptr_t address, const BYTE (&original)[N], void* hook, uintptr_t image_base) {
    BYTE expected[N];
    if (!RebaseSEH(original, image_base, expected)) return nullptr;
    return EntryHook(address, expected, hook);
}
inline bool InstallSpellMenu() {
    __try {
        if (memcmp(reinterpret_cast<void*>(base+kSpellMenuBuildRva), kExpectedSpellMenuBuild, sizeof(kExpectedSpellMenuBuild)) ||
            memcmp(reinterpret_cast<void*>(base+kSpellMenuProfileRva), kExpectedSpellMenuProfile, sizeof(kExpectedSpellMenuProfile))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    rebuild_spell_menu = reinterpret_cast<RebuildSpellMenu>(base+kSpellMenuBuildRva);
    current_spell_profile = reinterpret_cast<CurrentSpellProfile>(base+kSpellMenuProfileRva);
    original_spell_menu_frame = reinterpret_cast<SpellMenuFrame>(EntryHook(base+kSpellMenuFrameRva,
        kExpectedSpellMenuFrame, reinterpret_cast<void*>(&SpellMenuFrameHook)));
    return original_spell_menu_frame != nullptr;
}
inline bool InstallMerchantSellAll() {
    original_merchant = reinterpret_cast<InventoryNotify>(EntryHook(base+kUIMerchantNotifyRva,
        kExpectedUIMerchantNotify, reinterpret_cast<void*>(&MerchantWindowHook)));
    return original_merchant != nullptr;
}
inline bool InstallTradeskillRepeat() {
    __try {
        if (memcmp(reinterpret_cast<void*>(base+kCraftSelectedRva), kExpectedCraftSelected, sizeof(kExpectedCraftSelected))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    original_tradeskill = reinterpret_cast<InventoryNotify>(EntryHook(base+kCraftNotifyRva,
        kExpectedCraftNotify, reinterpret_cast<void*>(&TradeskillWindowHook)));
    original_tradeskill_frame = reinterpret_cast<TradeskillFrame>(EntryHook(base+kCraftFrameRva,
        kExpectedCraftFrame, reinterpret_cast<void*>(&TradeskillFrameHook)));
    return original_tradeskill && original_tradeskill_frame;
}
inline bool InstallPetArmor() {
    __try {
        if (memcmp(reinterpret_cast<void*>(base+kUIChildRva), kExpectedUIChild, sizeof(kExpectedUIChild))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    install_failure = "inventory_entry";
    original_inventory = reinterpret_cast<InventoryNotify>(SEHEntryHook(base+kUIInventoryNotifyRva,
        kExpectedUIInventoryNotify, reinterpret_cast<void*>(&InventoryHook), base));
    if (!original_inventory) return false;
    install_failure = "pet_window_entry";
    original_pet_window = reinterpret_cast<InventoryNotify>(EntryHook(base+kUIPetNotifyRva,
        kExpectedUIPetNotify, reinterpret_cast<void*>(&PetWindowHook)));
    if (!original_pet_window) return false;
    install_failure = "pet_available_entry";
    original_pet_available = reinterpret_cast<PetAvailable>(EntryHook(base+kUIPetAvailableRva,
        kExpectedUIPetAvailable, reinterpret_cast<void*>(&PetAvailableHook)));
    return original_pet_available != nullptr;
}
inline bool Install(uintptr_t image_base) {
    base = image_base;
    // Callee signatures are independently guarded; all hooks are complete,
    // entry instructions; verified SEH operands follow the executable relocation.
    __try {
        install_failure = "UISendRequest_signature";
        if (!MatchSEH(base+kUISendRequestRva, kExpectedUISendRequest, base)) return false;
        install_failure = "UIStringAssign_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUIStringAssignRva), kExpectedUIStringAssign, sizeof(kExpectedUIStringAssign))) return false;
        install_failure = "UIRowData_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUIRowDataRva), kExpectedUIRowData, sizeof(kExpectedUIRowData))) return false;
        install_failure = "UIAAFilter_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUIAAFilterRva),kExpectedUIAAFilter,sizeof(kExpectedUIAAFilter))) return false;
        install_failure = "UIAAButton_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUIAAButtonRva),kExpectedUIAAButton,sizeof(kExpectedUIAAButton))) return false;
        if (memcmp(reinterpret_cast<void*>(base+kUIChildRva),kExpectedUIChild,sizeof(kExpectedUIChild))) return false;
        install_failure = "UICellText_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUICellTextRva), kExpectedUICellText, sizeof(kExpectedUICellText))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    install_failure = "aa_allocation_controls";
    if (!InstallAAAllocationControls()) return false;
    send_request = reinterpret_cast<SendRequest>(base+kUISendRequestRva);
    install_failure = "label_entry";
    original_label = reinterpret_cast<GetLabel>(EntryHook(base+kUILabelRva, kExpectedUILabel, reinterpret_cast<void*>(&LabelHook)));
    if (!original_label) return false;
    install_failure = "chat_entry";
    original_chat = reinterpret_cast<DisplayChat>(EntryHook(base+kUIChatRva, kExpectedUIChat, reinterpret_cast<void*>(&ChatHook)));
    if (!original_chat) return false;
    install_failure = "state_entry";
    original_state = reinterpret_cast<SetGameState>(EntryHook(base+kUIStateRva, kExpectedUIState, reinterpret_cast<void*>(&StateHook)));
    if (!original_state) return false;
    install_failure = "aa_entry";
    original_aa = reinterpret_cast<UpdateAA>(SEHEntryHook(base+kUIAARva, kExpectedUIAA, reinterpret_cast<void*>(&AAHook), base));
    if (!original_aa) return false;
    install_failure = "aa_notify";
    original_aa_notify=reinterpret_cast<InventoryNotify>(EntryHook(base+kUIAANotifyRva,kExpectedUIAANotify,reinterpret_cast<void*>(&AANotifyHook)));
    if (!original_aa_notify) return false;
    install_failure = "aa_filter";
    original_aa_filter=reinterpret_cast<AAFilter>(base+kUIAAFilterRva);
    BYTE call[5]={0xE8};
    const auto relative=static_cast<int32_t>(reinterpret_cast<uintptr_t>(&AAFilterHook)-(base+kUIAAFilterCallRva+5));
    memcpy(call+1,&relative,4);
    return WriteVerifiedPatch(reinterpret_cast<BYTE*>(base+kUIAAFilterCallRva),kExpectedUIAAFilterCall,call,sizeof(call));
}
inline bool MatchLootNative() {
    __try {
        if (!MatchSEH(base+kLootCommandRva, kExpectedLootCommand, base) ||
            !MatchSEH(base+kLootConstructRva, kExpectedLootConstruct, base)) return false;
        if (memcmp(reinterpret_cast<void*>(base+kLootAllocateRva), kExpectedLootAllocate, sizeof(kExpectedLootAllocate)) ||
            memcmp(reinterpret_cast<void*>(base+kLootChildrenRva), kExpectedLootChildren, sizeof(kExpectedLootChildren)) ||
            memcmp(reinterpret_cast<void*>(base+kLootDestroyRva), kExpectedLootDestroy, sizeof(kExpectedLootDestroy)) ||
            memcmp(reinterpret_cast<void*>(base+kLootNotifyRva), kExpectedLootNotify, sizeof(kExpectedLootNotify)) ||
            memcmp(reinterpret_cast<void*>(base+kLootFrameRva), kExpectedLootFrame, sizeof(kExpectedLootFrame)) ||
            memcmp(reinterpret_cast<void*>(base+kLootShowRva), kExpectedLootShow, sizeof(kExpectedLootShow)) ||
            memcmp(reinterpret_cast<void*>(base+kLootTextRva), kExpectedLootText, sizeof(kExpectedLootText))) return false;
        // This catalog entry includes the RTTI locator and every vtable slot.
        // Each word is a HIGHLOW-relocated preferred-base pointer.
        for (size_t offset = 0; offset < sizeof(kExpectedLootTable); offset += 4) {
            uint32_t preferred = 0;
            memcpy(&preferred, kExpectedLootTable + offset, 4);
            if (*reinterpret_cast<uint32_t*>(base+kLootTableRva+offset) != preferred + static_cast<uint32_t>(base) - 0x400000u) return false;
        }
        return true;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline bool InstallAdvancedLoot(void (*trace)(const char*) = nullptr) {
    install_failure = "advanced_loot_native_guards";
    if (!MatchLootNative()) return false;
    // Exact native item cache and CButtonWnd decal assignment, independently
    // recovered from the pinned executable and the RoF2 MQ2 symbol stubs.
    install_failure = "advanced_loot_icon_guards";
    __try {
        if (memcmp(reinterpret_cast<void*>(base+kLootItemIconCacheRva), kExpectedLootItemIconCache, sizeof(kExpectedLootItemIconCache)) ||
            !MatchSEH(base+kLootItemIconRva, kExpectedLootItemIcon, base) ||
            memcmp(reinterpret_cast<void*>(base+kLootItemIconDecalsRva), kExpectedLootItemIconDecals, sizeof(kExpectedLootItemIconDecals))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    AdvancedLootIcons::cache = reinterpret_cast<AdvancedLootIcons::Cache>(base+kLootItemIconCacheRva);
    AdvancedLootIcons::get = reinterpret_cast<AdvancedLootIcons::Get>(base+kLootItemIconRva);
    LootScreenAPI api;
    api.allocate = reinterpret_cast<LootScreenAPI::Allocate>(base+kLootAllocateRva);
    api.construct = reinterpret_cast<LootScreenAPI::Construct>(base+kLootConstructRva);
    api.children = reinterpret_cast<LootScreenAPI::Children>(base+kLootChildrenRva);
    api.assign = reinterpret_cast<LootScreenAPI::Assign>(base+kUIStringAssignRva);
    api.child = reinterpret_cast<LootScreenAPI::Child>(base+kUIChildRva);
    api.vtable = reinterpret_cast<void**>(base+kLootTableRva+4);
    api.icon = &AdvancedLootIcons::Set;
    if (!AdvancedLootScreen::Bind(api, &AdvancedLootUI::Notify, &LootPulse, &AdvancedLootUI::Destroyed)) return false;
    install_failure = "advanced_loot_command_entry";
    original_command = reinterpret_cast<InterpretCommand>(SEHEntryHook(base+kLootCommandRva,
        kExpectedLootCommand, reinterpret_cast<void*>(&CommandHook), base));
    if (!original_command) return false;
    AdvancedLootUI::Initialize(&ExecuteUIRequest, &LootNotice, trace);
    return true;
}
}
}

#include "trainer_hooks.h"
#include "monk_reuse.h"
