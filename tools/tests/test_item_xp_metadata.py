"""Exercise the actual native metadata loader used by inventory and Bazaar."""
import unittest
import test_free_trade as native


class ItemXPMetadataTests(unittest.TestCase):
    def test_native_roundtrip(self):
        source = (native.CODE / 'common/item_instance.cpp').read_text(encoding='utf-8')
        methods = '\n'.join(native.body(source, signature) for signature in (
            'std::string EQ::ItemInstance::GetCustomDataString(',
            'void EQ::ItemInstance::SetCustomDataString(',
        ))
        native.FreeTradeTests.compile_run(self, r'''
#include <cassert>
#include <map>
#include <string>
#include <vector>
#include <cstdio>
#include <cstdlib>
#undef assert
#define assert(condition) do { if (!(condition)) { std::fprintf(stderr, "%s\n", #condition); std::exit(1); } } while (false)
namespace Strings {
std::vector<std::string> Split(const std::string& s, const std::string& delimiter) {
    std::vector<std::string> out;
    size_t start=0, end;
    while ((end=s.find(delimiter,start))!=std::string::npos) {
        out.push_back(s.substr(start,end-start)); start=end+delimiter.size();
    }
    out.push_back(s.substr(start)); return out;
}
}
namespace EQ {
struct ItemInstance {
    std::map<std::string,std::string> m_custom_data;
    std::string GetCustomDataString() const;
    void SetCustomDataString(const std::string&);
    void SetCustomData(const std::string& key,const std::string& value) {
        m_custom_data[key]=value;
    }
};
}
''' + methods + r'''
int main() {
    EQ::ItemInstance original, loaded;
    original.SetCustomData("nightcap_item_xp", "12345");
    original.SetCustomData("nightcap_paladin_grip", "1");
    original.SetCustomData("quest_value", "");
    loaded.SetCustomDataString(original.GetCustomDataString());
    assert(loaded.m_custom_data == original.m_custom_data);
    assert(loaded.GetCustomDataString() == original.GetCustomDataString());
    EQ::ItemInstance single;
    single.SetCustomDataString("nightcap_paladin_grip^1^");
    assert(single.GetCustomDataString()=="nightcap_paladin_grip^1^");
    EQ::ItemInstance compact;
    compact.SetCustomDataString("a^1^b^2^");
    assert(compact.m_custom_data.size()==2 && compact.m_custom_data.at("b")=="2");
    EQ::ItemInstance empty_value;
    empty_value.SetCustomDataString("a^^^b^2^");
    assert(empty_value.m_custom_data.size()==2 && empty_value.m_custom_data.at("a").empty());
    EQ::ItemInstance invalid;
    invalid.SetCustomData("existing","keep");
    for (const auto* data : {"a^1^^b", "^1^", "a^1^^^b^2^", "a^1^^a^2^"}) {
        invalid.SetCustomDataString(data);
        assert(invalid.m_custom_data.size()==1 && invalid.m_custom_data.at("existing")=="keep");
    }
}
''')


if __name__ == '__main__':
    unittest.main()
