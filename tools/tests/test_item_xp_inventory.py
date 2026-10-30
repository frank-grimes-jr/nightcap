"""Native metadata and exact inventory update contracts for item training."""
import unittest
import test_free_trade as native


class ItemXPInventoryTests(unittest.TestCase):
    def test_metadata_and_saved_preimage(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/item_xp_metadata.h"
#include "common/item_xp_inventory.h"
#include <cstdio>
#include <cstdlib>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"%s\n",#x); std::exit(1); } } while(false)
int main() {
    using namespace NightcapItemXP;
    auto metadata=ReadMetadata("",1001,0);
    CHECK(metadata.valid && !metadata.present && metadata.progress==0);
    auto saved=WriteMetadata(metadata,1001,123);
    CHECK(saved=="nightcap_item_xp^1:1001:123^");
    auto loaded=ReadMetadata(saved,1001,0);
    CHECK(loaded.valid && loaded.present && loaded.progress==123);
    CHECK(!ReadMetadata(saved,1002,0).valid);
    CHECK(!ReadMetadata(saved,1001,3).valid);
    CHECK(WriteMetadata(loaded,201001,0).empty());
    loaded.fields["nightcap_paladin_grip"]="1";
    saved=WriteMetadata(loaded,1001,456);
    loaded=ReadMetadata(saved,1001,0);
    CHECK(loaded.valid && loaded.fields.at("nightcap_paladin_grip")=="1");
    CHECK(WriteMetadata(loaded,201001,0)=="nightcap_paladin_grip^1^");
    for(const auto* value : {"", "-1", "01", "18446744073709551616", "80000000", "1x"}) {
        CHECK(!ReadMetadata(std::string("nightcap_item_xp^1:1001:")+value+"^",1001,0).valid);
    }
    for(const auto* value : {"x^1^x^2^", "x^1^^x^2^", "x^1^^", "x^1", "^1^", "z^1^^a^2^"}) {
        CHECK(!ReadMetadata(value,1001,0).valid);
    }
    CHECK(ReadMetadata("quest^^",1001,0).valid);
    using NightcapBazaar::Row;
    Row before={"7","21","1001","32767","123","1","2","3","4","5","6","1","","8","9","-10","42"};
    auto after=before;
    after[2]="201001"; after[12]="6162";
    auto sql=UpdateSQL(before,after);
    CHECK(sql.find("UPDATE inventory SET item_id=201001,color=123,custom_data=X'6162' WHERE ")==0);
    CHECK(sql.find("`character_id`=7 AND `slot_id`=21 AND `item_id`=1001")!=std::string::npos);
    CHECK(sql.find("BINARY COALESCE(custom_data,'')=X''")!=std::string::npos);
    CHECK(sql.find("guid")==std::string::npos);
    for(size_t i=0;i<before.size();++i) {
        if(i==2 || i==4 || i==12) continue;
        auto altered=after; altered[i]="999";
        CHECK(UpdateSQL(before,altered).empty());
    }
    CHECK(UpdateSQL(before,before).empty());
    after[12]="6e"; CHECK(!UpdateSQL(before,after).empty());
    after[12]="';DELETE FROM inventory;--";
    CHECK(UpdateSQL(before,after).empty());
    before[0]="0"; CHECK(UpdateSQL(before,after).empty());
}
''')


if __name__ == '__main__':
    unittest.main()
