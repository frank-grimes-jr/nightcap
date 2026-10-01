#include <windows.h>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"

using namespace nightcap::client_ui;
using Classes = uint32_t (__thiscall *)(void*, bool, bool);
static uint32_t stock_mask = 65535;
static int item_type = 20, spell_id = 4;
static uint32_t __fastcall StockClasses(void*, void*, bool first, bool second) {
    assert(first && !second); return stock_mask;
}
static int __fastcall ItemType(void* item, void*) {
    (void)*static_cast<volatile BYTE*>(item); // Native accessor dereferences its item.
    return item_type;
}
static int __fastcall ItemSpell(void*, void*, int effect) { assert(effect == 4); return spell_id; }
static uint8_t __fastcall StockLevel(void* spell, void*, int id) {
    return static_cast<BYTE*>(spell)[0x246 + id];
}
static const char* names[] = {"WAR","CLR","PAL","RNG","SHD","DRU","MNK","BRD",
    "ROG","SHM","NEC","WIZ","MAG","ENC","BST","BER"};
static const char* __fastcall ClassName(void*, void*, unsigned id, bool flag) {
    assert(id >= 1 && id <= 16 && !flag); return names[id - 1];
}
static int __cdecl Format(char* output, const char* format, const char* name, int level) {
    return sprintf_s(output, 256, format, name, level);
}
static void JumpTo(BYTE* address, void* function) {
    address[0] = 0xE9;
    const auto relative = static_cast<int32_t>(reinterpret_cast<uintptr_t>(function)
        - reinterpret_cast<uintptr_t>(address + 5));
    memcpy(address + 1, &relative, 4);
}
static void Append32(std::vector<BYTE>& bytes, uint32_t value) {
    const auto data = reinterpret_cast<const BYTE*>(&value);
    bytes.insert(bytes.end(), data, data + 4);
}
static void Local(std::vector<BYTE>& bytes, unsigned offset, uint32_t value) {
    bytes.insert(bytes.end(), {0xC7, 0x84, 0x24}); Append32(bytes, offset); Append32(bytes, value);
}
static std::vector<BYTE> Hex(const char* hex) {
    std::vector<BYTE> result;
    while (*hex) { unsigned byte = 0; assert(sscanf_s(hex, "%2x", &byte) == 1);
        result.push_back(static_cast<BYTE>(byte)); hex += 2; }
    return result;
}
static void Relocate(std::vector<BYTE>& bytes, uint32_t from, uint32_t to) {
    unsigned count = 0;
    for (size_t i = 0; i + 4 <= bytes.size(); ++i) {
        uint32_t found = 0; memcpy(&found, bytes.data() + i, 4);
        if (found == from) { memcpy(bytes.data() + i, &to, 4); ++count; i += 3; }
    }
    assert(count == 1);
}

// Exact complete enumeration blocks from pinned eqgame.exe SHA256
// 2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e.
// These execute the original bit test, class counter, formatting and concatenation.
// Only external addresses/calls are relocated to this disposable host. No game
// executable is loaded or modified. First RVA 0x2A39C3..0x2A3A63; second
// RVA 0x2A6D00..0x2A6DA2 (exclusive ends).
static std::string Render(bool second, void* item, void* spell, Classes classes, SpellLevel level) {
    static const char* blocks[] = {
        "8b4d006a008bf76a01d1cee80d13110085c674738b5424288b4c242c52e81bbde0ff8b0b0fb6c0506a00518b0dc425dd00e867cc1200508d94249c0100006864c09e0052e8238723008d8424a401000083c4108bc88a104084d275f98dbc24940000002bc18bf14feb038d49008a4f014784c975f88bc8c1e902f3a58bc883e103f3a48b7c2414ff44242883c304d1c7897c241481fbd4bbb2000f8e60ffffff",
        "8b9424100a00008b0a6a008bf36a01d1cee8cadf100085c674738b442428508bcfe8da89e0ff8b55000fb6c8518b0dc425dd006a0052e825991200508d8424f00000006864c09e0050e8e15323008d8424f800000083c4108bc88d9b000000008a104084d275f98dbc24fc0400002bc18bf14f8a4f014784c975f88bc8c1e902f3a58bc883e103f3a48b7c241cff44242883c504d1c381fdd4bbb2000f8e5effffff"
    };
    unsigned class_ids[16]; for (unsigned i = 0; i < 16; ++i) class_ids[i] = i + 1;
    void* item_ref = item; void* string_manager = nullptr; char output[512] = {};
    auto block = Hex(blocks[second ? 1 : 0]);
    const unsigned first_calls[] = {0x0B,0x1D,0x31,0x44}, second_calls[] = {0x11,0x21,0x36,0x49};
    const auto offsets = second ? second_calls : first_calls;
#ifndef NIGHTCAP_INSPECTION_BASELINE
    const uintptr_t native_start = second ? 0x2A6D00 : 0x2A39C3;
    assert((second ? kInspectionClasses2Rva : kInspectionClassesRva) == native_start + offsets[0]);
    assert((second ? kInspectionLevel2Rva : kInspectionLevelRva) == native_start + offsets[1]);
    assert(!memcmp(block.data()+offsets[0],second ? kExpectedInspectionClasses2 : kExpectedInspectionClasses,5));
    assert(!memcmp(block.data()+offsets[1],second ? kExpectedInspectionLevel2 : kExpectedInspectionLevel,5));
#endif
    Relocate(block, 0xDD25C4, reinterpret_cast<uint32_t>(&string_manager));
    Relocate(block, 0x9EC064, reinterpret_cast<uint32_t>("%s(%d) "));
    Relocate(block, 0xB2BBD4, reinterpret_cast<uint32_t>(&class_ids[15]));
    std::vector<BYTE> code = {0x55,0x53,0x56,0x57,0x81,0xEC}; // preserve registers; stack frame
    Append32(code, 0xA40);
    Local(code, 0x28, 1);
    Local(code, second ? 0x1C : 0x2C, reinterpret_cast<uint32_t>(spell));
    Local(code, second ? 0xA10 : 0x14, second ? reinterpret_cast<uint32_t>(&item_ref) : 2);
    const unsigned buffer = second ? 0x4FC : 0x94;
    Local(code, buffer, 0);
    code.push_back(0xBB); Append32(code, second ? 2 : reinterpret_cast<uint32_t>(class_ids));
    code.push_back(0xBD); Append32(code, second ? reinterpret_cast<uint32_t>(class_ids) : reinterpret_cast<uint32_t>(&item_ref));
    code.push_back(0xBF); Append32(code, second ? reinterpret_cast<uint32_t>(spell) : 2);
    const size_t start = code.size(); code.insert(code.end(), block.begin(), block.end());
    code.insert(code.end(), {0x8D,0xB4,0x24}); Append32(code, buffer); // copy native output
    code.push_back(0xBF); Append32(code, reinterpret_cast<uint32_t>(output));
    code.push_back(0xB9); Append32(code, sizeof(output)); code.insert(code.end(), {0xF3,0xA4,0x81,0xC4});
    Append32(code, 0xA40); code.insert(code.end(), {0x5F,0x5E,0x5B,0x5D,0xC3});
    auto memory = static_cast<BYTE*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(memory); memcpy(memory,code.data(),code.size());
    const uintptr_t targets[] = {reinterpret_cast<uintptr_t>(classes), reinterpret_cast<uintptr_t>(level),
        reinterpret_cast<uintptr_t>(&ClassName), reinterpret_cast<uintptr_t>(&Format)};
    for (unsigned i = 0; i < 4; ++i) {
        auto site = memory + start + offsets[i]; assert(*site == 0xE8);
        const auto relative = static_cast<int32_t>(targets[i] - reinterpret_cast<uintptr_t>(site + 5));
        memcpy(site + 1, &relative, 4);
    }
    assert(FlushInstructionCache(GetCurrentProcess(),memory,code.size()));
    reinterpret_cast<void (__cdecl *)()>(memory)();
    VirtualFree(memory,0,MEM_RELEASE);
    return output;
}

int main() {
    const auto started = GetTickCount64();
    auto host = static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(host); base = reinterpret_cast<uintptr_t>(host);
    JumpTo(host+kItemClassesRva,reinterpret_cast<void*>(&StockClasses));
    JumpTo(host+kItemTypeRva,reinterpret_cast<void*>(&ItemType));
    JumpTo(host+kItemSpellRva,reinterpret_cast<void*>(&ItemSpell));
    assert(FlushInstructionCache(GetCurrentProcess(),host,0xA68000));
    alignas(4) BYTE eq[0x600]={}, player[0x150]={}, spell[0x280]={}, item[4]={};
    *reinterpret_cast<void**>(host+0xA67CCC)=eq;
    *reinterpret_cast<void**>(host+0x9D2630)=player;
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    memcpy(player+0xA4,"Test",5);
    *reinterpret_cast<uint32_t*>(spell+0x174)=4;
    memset(spell+0x247,255,16); spell[0x246+13]=17;
    assert(state.Consume("[NCUI1]S|1|19|22|0|7|2|13|0|Test"));
    original_spell_level = reinterpret_cast<SpellLevel>(&StockLevel);

#ifdef NIGHTCAP_INSPECTION_BASELINE
    (void)started;
    for (bool second : {false,true}) {
        const auto output = Render(second,item,spell,reinterpret_cast<Classes>(&StockClasses),
            reinterpret_cast<SpellLevel>(&SpellLevelHook));
        std::cout << "Before fix, native path " << second << ": " << output << '\n';
        assert(output.find("WAR(255)") != std::string::npos && output.find("CLR(17)") != std::string::npos);
    }
    std::cerr << "RED: expected only MAG(17); both native renderers show unusable classes and a false CLR level\n";
    return 1;
#else
    const auto classes = reinterpret_cast<Classes>(&InspectionClassesHook);
    const auto level = reinterpret_cast<SpellLevel>(&InspectionSpellLevelHook);
    for (bool second : {false,true}) {
        assert(Render(second,item,spell,classes,level) == "MAG(17) ");
        stock_mask = 1u<<1; // Historical item restrictions must not invent CLR eligibility.
        assert(Render(second,item,spell,classes,level) == "MAG(17) ");
        stock_mask = 0; assert(Render(second,item,spell,classes,level).empty()); stock_mask = 65535;
    }
    assert(reinterpret_cast<SpellLevel>(&SpellLevelHook)(spell,2) == 17); // gameplay projection survives
    state.Clear(); // inspection requires no class snapshot or login state
    for (unsigned repeat = 0; repeat < 1000; ++repeat) {
        assert(classes(item,true,false) == (1u<<12)); assert(level(spell,13) == 17);
        assert(level(spell,2) == 255);
    }
    assert(state.Consume("[NCUI1]S|2|19|22|0|7|3|2|0|Test"));
    spell_id=11; *reinterpret_cast<uint32_t*>(spell+0x174)=11;
    spell[0x246+2]=1; spell[0x246+3]=15;
    assert(reinterpret_cast<SpellLevel>(&SpellLevelHook)(spell,3) == 1);
    for (bool second : {false,true}) assert(Render(second,item,spell,classes,level) == "CLR(1) PAL(15) ");
    *reinterpret_cast<uint32_t*>(player+0x148)=8; // stale identity cannot alter published class facts
    assert(classes(item,true,false) == ((1u<<1)|(1u<<2)) && level(spell,3)==15);
    item_type=0; stock_mask=1u<<8; assert(classes(item,true,false)==stock_mask);
    item_type=20; stock_mask=65535;
    spell_id=44999; *reinterpret_cast<uint32_t*>(spell+0x174)=44999;
    for (bool second : {false,true}) assert(Render(second,item,spell,classes,level).empty());
    assert(level(spell,13)==255 && level(spell,0)==255 && level(spell,17)==255);
    assert(classes(nullptr,true,false)==0 && level(nullptr,2)==255);
    assert(classes(reinterpret_cast<void*>(1),true,false)==0);
    assert(level(reinterpret_cast<void*>(1),2)==255);
    // Audit every catalog entry through the actual x86 hook boundaries, using
    // raw rows as the independent oracle rather than calling Mask/Level twice.
    size_t audited = 0;
    for (const auto& entry : NightcapSpellClasses::Catalog) {
        spell_id=static_cast<int>(entry.id); *reinterpret_cast<uint32_t*>(spell+0x174)=entry.id;
        uint32_t expected=0;
        for (unsigned id=1; id<=16; ++id) {
            const unsigned required=entry.levels[id-1];
            if (required>0 && required<255) expected|=1u<<(id-1);
            assert(level(spell,static_cast<int>(id))==required);
        }
        assert(classes(item,true,false)==expected);
        assert(level(spell,0)==255 && level(spell,17)==255);
        ++audited;
    }
    // Preserve the catalog's established 253/254 ownership semantics.
    for (unsigned marker : {253u,254u}) {
        bool found=false;
        for (const auto& entry : NightcapSpellClasses::Catalog) {
            for (unsigned id=1; id<=16; ++id) if (entry.levels[id-1]==marker) {
                spell_id=static_cast<int>(entry.id); *reinterpret_cast<uint32_t*>(spell+0x174)=entry.id;
                assert(level(spell,static_cast<int>(id))==marker && (classes(item,true,false)&(1u<<(id-1))));
                found=true; break;
            }
            if (found) break;
        }
        assert(found);
    }
    state.Clear(); base=0; original_spell_level=nullptr; VirtualFree(host,0,MEM_RELEASE);
    std::cout << "Both exact native spell inspection loops and x86 hook ABIs passed; "
        << audited << " catalog spells / " << audited*16 << " class levels; "
        << GetTickCount64()-started << " ms\n";
    return 0;
#endif
}
