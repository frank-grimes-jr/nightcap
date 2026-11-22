// Included inside nightcap::client_ui after AAChild. All controls are owned by
// the inspected item's window. Only a click on that window's Save writes a note.
struct NoteEditor {
    void* edit = nullptr;
    uint32_t item = 0;
    std::string saved;
};
static item_notes::Store note_store;
static std::unordered_map<void*, NoteEditor> note_editors;
static InventoryNotify original_note_notify = nullptr;
using ItemWindowDestroy = void* (__thiscall*)(void*, unsigned);
static ItemWindowDestroy original_item_window_destroy = nullptr;
inline void* __fastcall ItemWindowDestroyHook(void* window, void*, unsigned flags) {
    note_editors.erase(window);
    return original_item_window_destroy(window, flags);
}

inline void NoteText(void* control, const std::string& text) {
    EqString value{};
    item_description_assign(&value, text.c_str());
    using SetText = void (__thiscall*)(void*, const EqString*);
    reinterpret_cast<SetText>((*static_cast<void***>(control))[0x124/4])(control, &value);
    item_description_assign(&value, "");
}

inline void ClearItemNoteEditor(void* window) {
    if (!note_editors.erase(window)) return;
    if (auto edit = AAChild(window, "NC_NoteEdit")) NoteText(edit, "");
    if (auto status = AAChild(window, "NC_NoteStatus")) NoteText(status, "");
}

inline bool ReadNoteEdit(void* edit, char (&value)[item_notes::Limit + 1]) {
    __try {
        const auto rep = *reinterpret_cast<const BYTE**>(static_cast<BYTE*>(edit) + 0x1ec);
        if (!rep) { value[0] = 0; return true; }
        const auto length = *reinterpret_cast<const uint32_t*>(rep + 8);
        const auto encoding = *reinterpret_cast<const uint32_t*>(rep + 12);
        if (length > item_notes::Limit || encoding > 1 ||
            *reinterpret_cast<const uint32_t*>(rep + 4) < (length + 1) * (encoding + 1)) return false;
        const char* data = reinterpret_cast<const char*>(rep + 0x14);
        if (!encoding) {
            if (data[length] || memchr(data, 0, length)) return false;
            memcpy(value, data, length + 1);
            return true;
        }
        const auto wide = reinterpret_cast<const wchar_t*>(data);
        if (wide[length] || wmemchr(wide, 0, length)) return false;
        const bool utf8 = GetACP() == CP_UTF8;
        BOOL replaced = FALSE;
        return WideCharToMultiByte(CP_ACP, utf8 ? WC_ERR_INVALID_CHARS : WC_NO_BEST_FIT_CHARS,
            wide, length + 1, value, sizeof(value), nullptr, utf8 ? nullptr : &replaced) > 0 && !replaced;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

inline void RefreshItemNote(void* window, uint32_t id, std::string& description) {
    if (!original_note_notify) return;
    void* edit = AAChild(window, "NC_NoteEdit");
    void* status = AAChild(window, "NC_NoteStatus");
    if (!edit || !status) { note_editors.erase(window); return; }
    std::string saved;
    if (!note_store.Read(id, saved)) {
        auto existing = note_editors.find(window);
        if (existing == note_editors.end() || existing->second.item != id || existing->second.edit != edit) {
            note_editors.erase(window);
            NoteText(edit, "");
        }
        NoteText(status, "Could not read this item note.");
        return;
    }
    auto& previous = note_editors[window];
    const bool changed_item = previous.edit != edit || previous.item != id;
    if (changed_item) {
        *reinterpret_cast<int*>(static_cast<BYTE*>(edit) + 0x1e4) = static_cast<int>(item_notes::Limit);
        *reinterpret_cast<int*>(static_cast<BYTE*>(edit) + 0x1e8) = static_cast<int>(item_notes::Limit);
        NoteText(edit, saved);
        NoteText(status, "");
    } else if (saved != previous.saved) {
        char draft[item_notes::Limit + 1];
        if (ReadNoteEdit(edit, draft) && draft == previous.saved) NoteText(edit, saved);
        else NoteText(status, "Note changed elsewhere. Reload it or save your edit.");
    }
    previous = {edit, id, saved};
    if (!saved.empty()) {
        description += "<BR><c \"#00FFFF\">Private note</c><BR>";
        worn_comparison::AppendName(description, saved.c_str());
        description += "<BR>";
    }
}

inline int __fastcall ItemNoteNotify(void* window, void*, void* sender, uint32_t message, void* data) {
    if (window && sender) {
        void* edit = AAChild(window, "NC_NoteEdit");
        if (sender == edit) return 1;
        const bool save = sender == AAChild(window, "NC_NoteSave");
        if (save || sender == AAChild(window, "NC_NoteReload")) {
            if (message != 1) return 1;
            void* status = AAChild(window, "NC_NoteStatus");
            if (!edit || !status) return 1;
            uint32_t id = 0;
            char before[16385];
            if (!SnapshotItemDescription(window, id, before) || !id) return 1;
            const auto binding = note_editors.find(window);
            if (!save || binding == note_editors.end() || binding->second.item != id || binding->second.edit != edit) {
                note_editors.erase(window);
                ItemDescriptionHook(window, nullptr);
                return 1;
            }
            char text[item_notes::Limit + 1];
            if (!ReadNoteEdit(edit, text) || !item_notes::Valid(text)) {
                NoteText(status, "Use one line of up to 240 bytes in the client character set.");
                return 1;
            }
            if (!note_store.Save(id, text)) { NoteText(status, "Could not save. Your edit is still here."); return 1; }
            binding->second.saved = text;
            ItemDescriptionHook(window, nullptr);
            NoteText(status, *text ? "Note saved." : "Note removed.");
            return 1;
        }
    }
    return original_note_notify(window, sender, message, data);
}
