#include "../src/dllmain.cpp"
#include <wincrypt.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#pragma comment(lib,"advapi32.lib")
static unsigned failures=0,checks=0;
static void Check(bool okay,const char* text) { if (!okay) { std::cerr<<text<<"\n";ExitProcess(2); } }
static void Expect(bool okay,const char* text) { ++checks;if(!okay){++failures;std::cerr<<"FAIL: "<<text<<"\n";} }
static BYTE* LoadClient(const char* path) {
    std::ifstream file(path,std::ios::binary);
    Check(bool(file),"open pinned client read-only");
    std::vector<char> raw((std::istreambuf_iterator<char>(file)),{});
    Check(raw.size()==kExpectedEqgameSize,"client size");
    HCRYPTPROV provider=0; HCRYPTHASH hash=0;
    Check(CryptAcquireContext(&provider,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=0,"hash provider");
    Check(CryptCreateHash(provider,CALG_SHA_256,0,0,&hash)!=0,"hash create");
    Check(CryptHashData(hash,reinterpret_cast<const BYTE*>(raw.data()),static_cast<DWORD>(raw.size()),0)!=0,"hash data");
    BYTE digest[32]; DWORD length=sizeof(digest);
    Check(CryptGetHashParam(hash,HP_HASHVAL,digest,&length,0)!=0,"hash result");
    CryptDestroyHash(hash); CryptReleaseContext(provider,0);
    Check(!memcmp(digest,kExpectedEqgameSha256,32),"pinned client SHA256");
    auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(raw.data());
    auto nt=reinterpret_cast<IMAGE_NT_HEADERS32*>(raw.data()+dos->e_lfanew);
    auto image=static_cast<BYTE*>(VirtualAlloc(nullptr,nt->OptionalHeader.SizeOfImage,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    Check(image!=nullptr,"image allocation");
    memcpy(image,raw.data(),nt->OptionalHeader.SizeOfHeaders);
    auto sections=IMAGE_FIRST_SECTION(nt);
    for(unsigned i=0;i<nt->FileHeader.NumberOfSections;++i)
        memcpy(image+sections[i].VirtualAddress,raw.data()+sections[i].PointerToRawData,sections[i].SizeOfRawData);
    const auto reloc=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
    for(DWORD pos=reloc.VirtualAddress;pos<reloc.VirtualAddress+reloc.Size;) {
        auto block=reinterpret_cast<IMAGE_BASE_RELOCATION*>(image+pos);
        Check(block->SizeOfBlock>=8,"relocation block");
        auto entries=reinterpret_cast<WORD*>(block+1);
        for(unsigned i=0;i<(block->SizeOfBlock-8)/2;++i)
            if(entries[i]>>12==IMAGE_REL_BASED_HIGHLOW)
                *reinterpret_cast<DWORD*>(image+block->VirtualAddress+(entries[i]&4095)) +=
                    reinterpret_cast<DWORD>(image)-nt->OptionalHeader.ImageBase;
        pos+=block->SizeOfBlock;
    }
    return image;
}
static void Jump(BYTE* site,const void* target) {
    site[0]=0xe9;
    *reinterpret_cast<int32_t*>(site+1)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(target)-reinterpret_cast<uintptr_t>(site+5));
}

using nightcap::client_ui::EqString;
static std::string rendered;
static uint32_t drawn_color=0;
static int __fastcall CaptureButtonText(void*,void*,uint32_t,const EqString*,void*,void*,uint32_t color,uint32_t,uint32_t) {
 drawn_color=color;return 0;
}
static void __fastcall Capture(void*,void*,EqString text,bool,void*) {
 const auto rep=static_cast<const BYTE*>(text.rep);
 rendered=rep?reinterpret_cast<const char*>(rep+0x14):"";
 if(rep)InterlockedDecrement(reinterpret_cast<volatile LONG*>(text.rep));
}
static void __fastcall Title(void*,void*,const EqString*) {}
static void __fastcall Release(void*,void*,void* value) { InterlockedDecrement(static_cast<volatile LONG*>(value)); }
struct Text {
 std::vector<BYTE> bytes;
 explicit Text(const char* s):bytes(0x14+strlen(s)+1,0){
  *reinterpret_cast<LONG*>(bytes.data())=1;
  *reinterpret_cast<uint32_t*>(bytes.data()+4)=static_cast<uint32_t>(strlen(s)+1);
  *reinterpret_cast<uint32_t*>(bytes.data()+8)=static_cast<uint32_t>(strlen(s));
  memcpy(bytes.data()+0x14,s,strlen(s)+1);
 }
};
static std::vector<std::unique_ptr<Text>> assigned;
static EqString* __fastcall Assign(EqString* self,void*,const char* value) {
 assigned.emplace_back(new Text(value));self->rep=assigned.back()->bytes.data();return self;
}
static BYTE definition[0x300]={};
static void* __fastcall Definition(void*,void*) { return definition; }

struct ComparisonItem {
    BYTE instance[0xd8]{};
    BYTE def[0x634]{};
    static BYTE* __fastcall Get(void* self, void*) {
        return static_cast<ComparisonItem*>(self)->def;
    }
    ComparisonItem(const char* name, int hp) {
        static void* table[] = {nullptr, nullptr, reinterpret_cast<void*>(&Get)};
        *reinterpret_cast<void***>(instance) = table;
        strcpy_s(reinterpret_cast<char*>(def), 64, name);
        *reinterpret_cast<int*>(def + 0x130) = hp;
    }
};
static BYTE comparison_profile[0x100]{};
static BYTE* __fastcall CurrentProfile(void*, void*) { return comparison_profile; }
static BYTE __fastcall Eligible(void*, void*, ComparisonItem** ref, int slot, bool first, bool second) {
    return !first && second && (*reinterpret_cast<unsigned*>((*ref)->def + 0xf0) & (1u << slot)) != 0;
}
static void CheckWornComparison(BYTE* image, BYTE* window) {
    nightcap::client_ui::base = reinterpret_cast<uintptr_t>(image);
    BYTE character[32]{}, game[0x600]{};
    int vb[2]{};
    *reinterpret_cast<int**>(character + 8) = vb;
    *reinterpret_cast<void**>(image + 0x9d261c) = character;
    *reinterpret_cast<void**>(image + 0xa67ccc) = game;
    int& state = *reinterpret_cast<int*>(game + 0x5c8);
    state = 5;
    Jump(image + kSpellMenuProfileRva, reinterpret_cast<void*>(&CurrentProfile));
    Jump(image + 0x183550, reinterpret_cast<void*>(&Eligible));
    ComparisonItem ring("Candidate", 12), left("Old <Ring>", 6), right("Heavy Ring", 30), aug("Gem", 3);
    auto& slots = *reinterpret_cast<unsigned*>(ring.def + 0xf0);
    slots = (1u << 15) | (1u << 16);
    ring.def[0x128] = 0xfe; // signed STR -2
    aug.def[0x1d4] = 54;
    aug.def[0x183] = 3; aug.def[0x184] = 2;
    ring.def[0x183] = 2; ring.def[0x184] = 2;
    void* gems[] = {nullptr, &aug};
    *reinterpret_cast<void***>(left.instance + 0xa8) = gems;
    *reinterpret_cast<int*>(left.instance + 0xac) = 2;
    void* worn[23]{};
    worn[15] = &left; worn[16] = &right;
    *reinterpret_cast<void***>(comparison_profile + 0x20) = worn;
    *reinterpret_cast<unsigned*>(comparison_profile + 0x18) = 34;
    int& count = *reinterpret_cast<int*>(comparison_profile + 0x24);
    count = 23;
    Text original("Ordinary item description<BR>");
    *reinterpret_cast<void**>(window + 0x294) = original.bytes.data();
    *reinterpret_cast<void**>(window + 0x2b0) = &ring;
    auto refresh = [&]() { reinterpret_cast<nightcap::client_ui::UpdateItemDescription>(
        image + kItemDescriptionUpdateRva)(window); };
    refresh();
    Expect(rendered.find("Left ring: Old &lt;Ring&gt;<BR>HP +3, STR -2") != std::string::npos,
           "left ring includes socketed stats and escapes names");
    Expect(rendered.find("Right ring: Heavy Ring<BR>HP -18, STR -2") != std::string::npos,
           "right ring has an independent signed baseline");
    Expect(rendered.find("Fire damage +2, Cold damage -2") != std::string::npos,
           "different elemental types do not cancel each other");
    const auto both = rendered;
    refresh();
    Expect(rendered == both && rendered.find("Ordinary item description") == 0, "refresh is idempotent");
    worn[15] = nullptr;
    worn[16] = &ring;
    refresh();
    Expect(rendered.find("Left ring: Empty<BR>HP +12") != std::string::npos &&
           rendered.find("Right ring: Candidate<BR>Same listed stats") != std::string::npos,
           "empty and identical slots");
    slots = (1u << 1) | (1u << 4) | (1u << 9) | (1u << 10);
    refresh();
    Expect(rendered.find("Right ring:") == std::string::npos && rendered.find("Left ear:") != std::string::npos &&
           rendered.find("Right ear:") != std::string::npos && rendered.find("Left wrist:") != std::string::npos &&
           rendered.find("Right wrist:") != std::string::npos, "new slot mask replaces all old rows");
    slots = 1u << 15;
    worn[15] = &left;
    *reinterpret_cast<int*>(left.instance + 0xac) = 7;
    refresh();
    Expect(rendered == "Ordinary item description<BR>", "incomplete socket read discards partial comparison");
    *reinterpret_cast<int*>(left.instance + 0xac) = 2;
    count = 12;
    refresh();
    Expect(rendered.find("Left ring: Empty<BR>HP +12") != std::string::npos, "unallocated trailing slot is empty");
    count = -1;
    refresh();
    Expect(rendered == "Ordinary item description<BR>", "unavailable inventory never appears empty");
    count = 23;
    state = 1;
    refresh();
    Expect(rendered == "Ordinary item description<BR>", "zoning clears comparison");
    state = 5;
    ring.def[0x1d4] = 54;
    refresh();
    Expect(rendered == "Ordinary item description<BR>", "standalone augment has no worn comparison");
    nightcap::client_ui::base = 0;
}
static BYTE note_controls[4][0x240]{};
static const char* NoteControlText(void* control) {
    const auto rep = *reinterpret_cast<BYTE**>(static_cast<BYTE*>(control) + 0x1ec);
    return rep ? reinterpret_cast<const char*>(rep + 0x14) : "";
}
static void __fastcall NoteSetText(void* control, void*, const EqString* text) {
    *reinterpret_cast<void**>(static_cast<BYTE*>(control) + 0x1ec) = text->rep;
}
static void* __fastcall NoteChild(void*, void*, const EqString* text) {
    const char* name = reinterpret_cast<const char*>(text->rep) + 0x14;
    const char* names[] = {"NC_NoteEdit", "NC_NoteSave", "NC_NoteReload", "NC_NoteStatus"};
    for (size_t i = 0; i < std::size(names); ++i) if (!strcmp(name, names[i])) return note_controls[i];
    return nullptr;
}
static int __fastcall StockItemNotify(void*, void*, void*, uint32_t, void*) { return 71; }
static void* __fastcall StockItemDestroy(void* window, void*, unsigned flags) { return flags == 1 ? window : nullptr; }
static void CheckPrivateNotes(BYTE* image, BYTE* window) {
    using namespace nightcap::client_ui;
    using namespace nightcap::item_notes;
    const std::string key = "Software\\NightcapNotesFixture-" + std::to_string(GetCurrentProcessId()) +
                            "-" + std::to_string(GetTickCount64());
    HKEY test_key{}; DWORD disposition{};
    Check(RegCreateKeyExA(HKEY_CURRENT_USER, key.c_str(), 0, nullptr, REG_OPTION_VOLATILE,
                          KEY_ALL_ACCESS, nullptr, &test_key, &disposition) == ERROR_SUCCESS &&
          disposition == REG_CREATED_NEW_KEY, "unique temporary notes registry key");
    RegCloseKey(test_key);
    note_store = Store(key.c_str());
    std::string stored;
    Expect(!note_store.Save(0, "invalid") && !note_store.Save(1, std::string(241, 'x')) &&
           !note_store.Save(1, "two\nlines"), "reject invalid key, oversized and multiline notes");
    Expect(note_store.Save(1, std::string(240, 'x')) && Store(key.c_str()).Read(1, stored) &&
           stored.size() == 240, "maximum note survives reopening store");
    base = reinterpret_cast<uintptr_t>(image);
    *reinterpret_cast<void**>(image + 0xa67ccc) = nullptr; // comparison has separate fixture
    Jump(image + kUIStringAssignRva, reinterpret_cast<void*>(&Assign));
    Jump(image + kUIChildRva, reinterpret_cast<void*>(&NoteChild));
    void* vtable[0x128 / 4]{};
    vtable[0x124 / 4] = reinterpret_cast<void*>(&NoteSetText);
    for (auto& control : note_controls) *reinterpret_cast<void***>(control) = vtable;
    original_note_notify = reinterpret_cast<InventoryNotify>(&StockItemNotify);
    Check(PatchBazaarSlot(base + kItemNoteNotifySlotRva, kExpectedItemNoteNotifySlot, base,
          reinterpret_cast<uintptr_t>(&ItemNoteNotify)), "bind actual item notify vtable slot");
    auto click = [&](unsigned button, unsigned message = 1) {
        return (*reinterpret_cast<InventoryNotify*>(base + kItemNoteNotifySlotRva))(
            window, note_controls[button], message, nullptr);
    };
    auto update = reinterpret_cast<UpdateItemDescription>(image + kItemDescriptionUpdateRva);
    auto type = [](Text& text) { *reinterpret_cast<void**>(note_controls[0] + 0x1ec) = text.bytes.data(); };
    ComparisonItem a("Ring", 4), b("Ring", 7);
    *reinterpret_cast<uint32_t*>(a.def + 0xec) = 14679;
    *reinterpret_cast<uint32_t*>(b.def + 0xec) = 214679;
    auto& item = *reinterpret_cast<void**>(window + 0x2b0);
    item = &a;
    Text native("Native stats"), draft("Save <for> A & B"), blank("");
    *reinterpret_cast<void**>(window + 0x294) = native.bytes.data();
    update(window);
    type(draft); update(window); click(1, 2);
    Expect(!strcmp(NoteControlText(note_controls[0]), "Save <for> A & B") &&
           note_store.Read(14679, stored) && stored.empty(), "refresh and non-click preserve unsaved edit");
    click(1);
    Expect(rendered.find("Save &lt;for&gt; A &amp; B") != std::string::npos &&
           rendered.find("Native stats") == 0 && !strcmp(NoteControlText(note_controls[3]), "Note saved."),
           "save renders escaped private note through the native description");
    type(blank); click(2);
    Expect(!strcmp(NoteControlText(note_controls[0]), "Save <for> A & B"), "reload discards unsaved draft");
    item = &b; click(1);
    Expect(note_store.Read(214679, stored) && stored.empty() && !*NoteControlText(note_controls[0]) &&
           rendered.find("Private note") == std::string::npos, "stale save cannot cross same-name variants");
    item = &a; update(window);
    Expect(!strcmp(NoteControlText(note_controls[0]), "Save <for> A & B"), "reinspection retrieves note by ID");
    Text keep("unsaved changes");
    type(keep);
    DWORD wrong_type = 7;
    Check(RegSetKeyValueA(HKEY_CURRENT_USER, key.c_str(), "14679", REG_DWORD, &wrong_type,
                          sizeof(wrong_type)) == ERROR_SUCCESS, "simulate unreadable saved value");
    update(window);
    Expect(!strcmp(NoteControlText(note_controls[0]), "unsaved changes") &&
           !strcmp(NoteControlText(note_controls[3]), "Could not read this item note."),
           "read error preserves the draft for the same item");
    alignas(4) BYTE wide[0x14 + 8]{};
    *reinterpret_cast<DWORD*>(wide + 4) = 8;
    *reinterpret_cast<DWORD*>(wide + 8) = 3;
    *reinterpret_cast<DWORD*>(wide + 12) = 1;
    memcpy(wide + 0x14, L"Gem", 8);
    *reinterpret_cast<void**>(note_controls[0] + 0x1ec) = wide;
    click(1);
    Expect(note_store.Read(14679, stored) && stored == "Gem", "native UTF16 edit saves through the client code page");
    type(blank); click(1);
    Expect(note_store.Read(14679, stored) && stored.empty() && rendered.find("Private note") == std::string::npos,
           "blank save removes this item only");
    Expect(note_store.Read(1, stored) && stored.size() == 240, "other note retained after removal");
    item = nullptr; update(window);
    Expect(note_editors.empty() && !*NoteControlText(note_controls[0]), "empty window drops draft binding");
    Expect(ItemNoteNotify(window, nullptr, window, 1, nullptr) == 71, "stock notifications delegate");
    item = &a; update(window);
    original_item_window_destroy = reinterpret_cast<ItemWindowDestroy>(&StockItemDestroy);
    Check(PatchBazaarSlot(base + kItemWindowDestroySlotRva, kExpectedItemWindowDestroySlot, base,
          reinterpret_cast<uintptr_t>(&ItemWindowDestroyHook)), "bind actual item destruction slot");
    Expect((*reinterpret_cast<ItemWindowDestroy*>(base + kItemWindowDestroySlotRva))(window,1) == window &&
           note_editors.empty(), "UI destruction removes editor binding and preserves native callback");
    original_note_notify = nullptr; base = 0; note_store = Store();
    Check(RegDeleteKeyA(HKEY_CURRENT_USER, key.c_str()) == ERROR_SUCCESS, "remove temporary test key");
}
int main(int argc,char** argv) {
 Check(argc==2,"read-only client path required");auto image=LoadClient(argv[1]);
 Jump(image+0x489a50,reinterpret_cast<void*>(&CaptureButtonText));
 // Execute actual CButtonWnd::DrawText through its normal/hover/pressed/disabled
 // selectors, stopping only at the font renderer (no graphics device in tests).
 BYTE button[0x280]={};int rect[4]={0,0,200,22};Text button_text("Tiered item");
 *reinterpret_cast<void**>(button+0x1a8)=button_text.bytes.data();
 *reinterpret_cast<uint32_t*>(button+0x218)=0xff777777;
 using DrawButton=int(__thiscall*)(void*,void*,void*);
 for(uint32_t color:{0xff00ff00u,0xff0070ddu,0xffa335eeu,0xffff8000u}){
  nightcap::SetItemNameTextColor(button,color,true);
  for(unsigned mode=0;mode<4;++mode){
   button[0x1a]=mode!=3;button[0x20]=mode==1;button[0x1e4]=mode==2;
   reinterpret_cast<DrawButton>(image+0x497b30)(button,rect,rect);
   Expect(drawn_color==(mode==3?0xff777777:color),"native button draw preserves tiers across hover/press and keeps disabled color");
  }
 }
 Jump(image+0x483e10,reinterpret_cast<void*>(&Capture));
 Jump(image+0x405b20,reinterpret_cast<void*>(&Release));
 BYTE window[0x600]={}; void* table[0x130/4]={};
 table[0x124/4]=reinterpret_cast<void*>(&Title);*reinterpret_cast<void***>(window)=table;
 *reinterpret_cast<void**>(window+0x220)=window;
 BYTE name_label[0x200]={};
 *reinterpret_cast<void**>(window+0x314)=name_label;
 auto& name_color=*reinterpret_cast<uint32_t*>(name_label+0x12c);
 *reinterpret_cast<uint32_t*>(definition+0xec)=940282;
 void* item_table[3]={nullptr,nullptr,reinterpret_cast<void*>(&Definition)};void** item=item_table;
 *reinterpret_cast<void**>(window+0x2b0)=&item;
 Text info("AC: 5<BR>HP: 114<BR>This Augmentation fits in slot types: 22");
 *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
 using Update=void(__thiscall*)(void*);
 nightcap::client_ui::original_item_description = reinterpret_cast<Update>(nightcap::client_ui::EntryHook(
  reinterpret_cast<uintptr_t>(image)+kItemDescriptionUpdateRva,kExpectedItemDescriptionUpdate,reinterpret_cast<void*>(&nightcap::client_ui::ItemDescriptionHook)));
 Check(nightcap::client_ui::original_item_description!=nullptr,"guarded item-description hook");
 nightcap::client_ui::item_description_assign=reinterpret_cast<nightcap::client_ui::AssignString>(&Assign);
 // Native item rendering has already selected green for usable equipment.
 // Exercise the installed description hook, including repeated window reuse.
 for(const auto& sample:std::vector<std::pair<const char*,uint32_t>>{
  {"Sword (Polished)",0xff0070ddu},{"Sword (Exalted)",0xffa335eeu},
  {"Sword (Ascended)",0xffff8000u},{"Sword",0xff00ff00u}}){
  strcpy_s(reinterpret_cast<char*>(definition),64,sample.first);
  *reinterpret_cast<uint32_t*>(definition+0xec)=213073;
  name_color=0xff00ff00;
  reinterpret_cast<Update>(image+0x29ae30)(window);
  Expect(name_color==sample.second,"item heading uses requested quality color");
  reinterpret_cast<Update>(image+0x29ae30)(window);
  Expect(name_color==sample.second,"repeat refresh preserves quality color");
 }
 strcpy_s(reinterpret_cast<char*>(definition),64,"Sword (Ascended)");
 for(uint32_t warning:{0xffff0000u,0xffa020f0u}){
  name_color=warning;
  reinterpret_cast<Update>(image+0x29ae30)(window);
  Expect(name_color==warning,"native equipment restriction warning retained");
 }
 *reinterpret_cast<uint32_t*>(definition+0xec)=940282;
 reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered.find("Shield Block: +1%")!=std::string::npos,"Exalted shield block must be visible in native Description");
 Expect(rendered.find("not Shielding")!=std::string::npos,"distinguishes Shielding");
 Expect(rendered.find("usable shield")!=std::string::npos,"shield requirement visible");
 Expect(rendered.find("socketed in worn armor")!=std::string::npos,"equipped socket requirement visible");
 Expect(rendered.find("strongest Hunt")!=std::string::npos,"stacking rule visible");
 const auto once=rendered;reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered==once,"repeated native refresh is idempotent");
 Expect(rendered.find("AC: 5<BR>HP: 114")!=std::string::npos,"ordinary Description retained");
 for(uint32_t base:{940040u,940280u,940528u})for(uint32_t tier=0;tier<4;++tier){
  *reinterpret_cast<uint32_t*>(definition+0xec)=base+tier;
  *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
  reinterpret_cast<Update>(image+0x29ae30)(window);
  const int bonus=tier==0?0:tier==3?2:1;
  Expect(bonus?rendered.find("Shield Block: +"+std::to_string(bonus)+"%")!=std::string::npos:rendered.find("Shield Block")==std::string::npos,"all shield-block families/tiers match server");
 }
 *reinterpret_cast<uint32_t*>(definition+0xec)=940282;
 *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
 reinterpret_cast<Update>(image+0x29ae30)(window);
 *reinterpret_cast<uint32_t*>(definition+0xec)=940100;
 reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered.find("Shield Block")==std::string::npos,"window reuse clears old annotation");
 *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
 *reinterpret_cast<void**>(window+0x2b0)=nullptr;
 reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered==reinterpret_cast<const char*>(info.bytes.data()+0x14),"missing item keeps native Description");
 char copy[16385]={};uint32_t id=0;
 Expect(!nightcap::client_ui::SnapshotItemDescription(nullptr,id,copy),"null window rejected");
 *reinterpret_cast<void**>(window+0x2b0)=&item;
 *reinterpret_cast<uint32_t*>(info.bytes.data()+12)=1;
 Expect(!nightcap::client_ui::SnapshotItemDescription(window,id,copy),"unsupported native string encoding rejected");
 *reinterpret_cast<uint32_t*>(info.bytes.data()+12)=0;
 *reinterpret_cast<uint32_t*>(info.bytes.data()+8)=16385;
 Expect(!nightcap::client_ui::SnapshotItemDescription(window,id,copy),"oversized string rejected");
 *reinterpret_cast<uint32_t*>(info.bytes.data()+8)=static_cast<uint32_t>(strlen("AC: 5<BR>HP: 114<BR>This Augmentation fits in slot types: 22"));
 Expect(!nightcap::client_ui::EntryHook(reinterpret_cast<uintptr_t>(image)+kItemDescriptionUpdateRva,kExpectedItemDescriptionUpdate,reinterpret_cast<void*>(&nightcap::client_ui::ItemDescriptionHook)),"foreign/repeated patch rejected");
 CheckWornComparison(image, window);
 CheckPrivateNotes(image, window);
 std::cout<<checks<<" checks, "<<failures<<" failures\n";return failures?1:0;
}
