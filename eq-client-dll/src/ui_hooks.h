#pragma once
#include "ui_state.h"
#include "pet_state.h"
#include "verified_patch.h"

namespace nightcap {
namespace client_ui {
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
using DisplayChat = void (__thiscall *)(void*, const char*, int, bool, bool);
using SetGameState = void (__thiscall *)(void*, int);
using UpdateAA = void (__thiscall *)(void*);
using GetRowData = uint32_t (__thiscall *)(void*, int);
using SetCellText = void (__thiscall *)(void*, int, int, const EqString*);
static uintptr_t base = 0;
static const char* install_failure = "not_started";
static UIState state;
static PetState pets;
using InventoryNotify = int (__thiscall *)(void*, void*, uint32_t, void*);
static InventoryNotify original_inventory = nullptr;
static ULONGLONG next_pet_refresh = 0;
static GetLabel original_label = nullptr;
static DisplayChat original_chat = nullptr;
static SetGameState original_state = nullptr;
static UpdateAA original_aa = nullptr;
static ULONGLONG next_refresh = 0;

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
inline void RequestRefresh() {
    uint32_t spawn = 0;
    char name[64] = {};
    if (!ReadIdentity(spawn, name) || GetTickCount64() < next_refresh) return;
    next_refresh = GetTickCount64() + 5000;
    using Interpret = void (__thiscall *)(void*, void*, char*);
    auto eq = *reinterpret_cast<void**>(base + 0xA67CCC);
    auto player = *reinterpret_cast<void**>(base + 0x9D2630);
    char command[] = "/say #nightcapui refresh";
    reinterpret_cast<Interpret>(base+kUIInterpretRva)(eq, player, command);
}
inline bool CurrentPetIdentity() {
    uint32_t spawn = 0;
    char name[64] = {};
    return ReadIdentity(spawn, name) && pets.Matches(spawn, name);
}
inline void ExecuteUICommand(std::string command) {
    uint32_t spawn = 0;
    char name[64] = {};
    if (command.empty() || !ReadIdentity(spawn, name)) return;
    using Interpret = void (__thiscall *)(void*, void*, char*);
    auto eq = *reinterpret_cast<void**>(base + 0xA67CCC);
    auto player = *reinterpret_cast<void**>(base + 0x9D2630);
    reinterpret_cast<Interpret>(base+kUIInterpretRva)(eq, player, command.data());
}
inline void RequestPetRefresh() {
    if (GetTickCount64() < next_pet_refresh) return;
    next_pet_refresh = GetTickCount64() + 5000;
    ExecuteUICommand("/say #nightcappet view");
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
inline int __fastcall InventoryHook(void* self, void*, void* sender, uint32_t message, void* data) {
    if (message == 1 && sender) {
        if (IsArmorControl(self, sender, "NCPA_Refresh")) { RequestPetRefresh(); return 1; }
        if (IsArmorControl(self, sender, "NCPA_Previous")) { pets.Next(-1); return 1; }
        if (IsArmorControl(self, sender, "NCPA_Next")) { pets.Next(1); return 1; }
        const char* ids[] = {"Equip", "Remove", "Inspect"};
        const char* verbs[] = {"equip", "remove", "inspect"};
        for (unsigned action = 0; action < 3; ++action) {
            for (unsigned slot = 0; slot < 8; ++slot) {
                const std::string id = std::string("NCPA_") + ids[action] + std::to_string(slot);
                if (!IsArmorControl(self, sender, id.c_str())) continue;
                if (CurrentPetIdentity()) ExecuteUICommand(pets.Command(verbs[action], slot));
                else RequestPetRefresh();
                return 1;
            }
        }
    }
    return original_inventory(self, sender, message, data);
}
inline bool __cdecl LabelHook(int type, EqString* output, bool* override_color, unsigned long* color) {
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
    if (state.Consume(message) || pets.Consume(message)) return;
    original_chat(self, message, color, log, convert);
}
inline void __fastcall StateHook(void* self, void*, int next) {
    if (next != 5) { state.Clear(); pets.Clear(); next_refresh = 0; next_pet_refresh = 0; }
    original_state(self, next);
}
inline bool ReadList(void* window, unsigned index, void*& list, int& rows, int& class_column) {
    __try {
        list = reinterpret_cast<void**>(static_cast<BYTE*>(window) + 0x2A0)[index];
        if (!list) return false;
        rows = *reinterpret_cast<int*>(static_cast<BYTE*>(list) + 0x1D8);
        if (rows < 0 || rows > 32768) return false;
        const int columns = *reinterpret_cast<int*>(static_cast<BYTE*>(list) + 0x1E8);
        const BYTE* entries = *reinterpret_cast<BYTE**>(static_cast<BYTE*>(list) + 0x1EC);
        if (columns < 1 || columns > 32 || !entries) return false;
        class_column = -1;
        for (int i = 0; i < columns; ++i) {
            const BYTE* rep = *reinterpret_cast<BYTE* const*>(entries + i*0x3C + 0x18);
            if (!rep || *reinterpret_cast<const uint32_t*>(rep+0x0C) != 0 ||
                *reinterpret_cast<const uint32_t*>(rep+0x08) != 5 ||
                *reinterpret_cast<const uint32_t*>(rep+0x04) < 6 ||
                memcmp(rep+0x14,"Class",6) != 0) continue;
            if (class_column != -1) return false;
            class_column = i;
        }
        return class_column != -1;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
inline void __fastcall AAHook(void* self, void*) {
    original_aa(self);
    const bool current = CurrentIdentity();
    if (!current) RequestRefresh();
    auto assign = reinterpret_cast<AssignString>(base + kUIStringAssignRva);
    auto row_data = reinterpret_cast<GetRowData>(base + kUIRowDataRva);
    auto set_text = reinterpret_cast<SetCellText>(base + kUICellTextRva);
    for (unsigned index = 0; index < 4; ++index) {
        void* list = nullptr;
        int rows = 0, class_column = -1;
        if (!ReadList(self, index, list, rows, class_column)) continue;
        for (int row = 0; row < rows; ++row) {
            const std::string text = current ? state.AAClasses(row_data(list, row)) : "Unknown";
            EqString value{};
            assign(&value, text.c_str());
            set_text(list, row, class_column, &value);
            // Release through the client's allocator/refcount, never our CRT.
            assign(&value, "");
        }
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
inline bool InstallPetArmor() {
    __try {
        if (memcmp(reinterpret_cast<void*>(base+kUIChildRva), kExpectedUIChild, sizeof(kExpectedUIChild))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    install_failure = "inventory_entry";
    original_inventory = reinterpret_cast<InventoryNotify>(SEHEntryHook(base+kUIInventoryNotifyRva,
        kExpectedUIInventoryNotify, reinterpret_cast<void*>(&InventoryHook), base));
    return original_inventory != nullptr;
}
inline bool Install(uintptr_t image_base) {
    base = image_base;
    // Callee signatures are independently guarded; all hooks are complete,
    // entry instructions; verified SEH operands follow the executable relocation.
    __try {
        install_failure = "UIInterpret_signature";
        if (!MatchSEH(base+kUIInterpretRva, kExpectedUIInterpret, base)) return false;
        install_failure = "UIStringAssign_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUIStringAssignRva), kExpectedUIStringAssign, sizeof(kExpectedUIStringAssign))) return false;
        install_failure = "UIRowData_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUIRowDataRva), kExpectedUIRowData, sizeof(kExpectedUIRowData))) return false;
        install_failure = "UICellText_signature";
        if (memcmp(reinterpret_cast<void*>(base+kUICellTextRva), kExpectedUICellText, sizeof(kExpectedUICellText))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
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
    return original_aa != nullptr;
}
}
}
