"""Character custody for loose trophies, socketed equipment and incoming containers."""
import unittest
import test_free_trade as native


class RaidCustodyTests(unittest.TestCase):
    def test_incoming_custody(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "zone/raid_augment_custody.h"
#include <cassert>
#include <set>

struct Data { unsigned ID; unsigned char BagSlots; };
struct Item {
 Data data;
 Item *children[10]{};
 unsigned GetID() const { return data.ID; }
 const Data *GetItem() const { return &data; }
 bool IsClassBag() const { return data.BagSlots > 0; }
 const Item *GetItem(unsigned char slot) const { return children[slot]; }
 const Item *GetAugment(unsigned char slot) const { return children[slot]; }
};
struct Client {
 std::set<unsigned> owned;
 bool CheckLoreConflict(const Data *item) const { return owned.count(item->ID) != 0; }
};
int main() {
 using NightcapRaidAug::IncomingTrophies;
 Item frost{{963200,0}}, prism{{963215,0}}, chest{{40,0}}, bag{{42,10}}, other{{1,0}};
 chest.children[5] = &frost;
 bag.children[9] = &chest;
 Client c{{963215,42}};
 assert(!IncomingTrophies{}.Conflict(c, &bag));
 assert(IncomingTrophies{}.Conflict(c, &prism) == 963215);
 c.owned.insert(963200);
 assert(IncomingTrophies{}.Conflict(c, &bag) == 963200);
 assert(IncomingTrophies{}.Conflict(c, &chest) == 963200);
 assert(!IncomingTrophies{}.Conflict(c, &chest, &frost));
 assert(IncomingTrophies{}.Conflict(c, &chest, &prism) == 963200);
 c.owned.clear();
 IncomingTrophies trade;
 assert(!trade.Conflict(c, &prism));
 assert(!trade.Conflict(c, &bag));
 assert(!trade.Conflict(c, &other));
 assert(trade.Conflict(c, &frost) == 963200);
 bag.children[0] = &frost;
 assert(IncomingTrophies{}.Conflict(c, &bag) == 963200);
}
''')

    def test_checks_precede_transfer(self):
        cases = [
            ('trading.cpp', 'bool Client::CheckTradeLoreConflict(', 'return has_lore_item'),
            ('trading.cpp', 'void Client::BuyTraderItem(', 'TakeMoneyFromPP('),
            ('client_packet.cpp', 'void Client::Handle_OP_GuildBank(', 'PushItemOnCursor(*inst.get()'),
            ('parcels.cpp', 'void Client::DoParcelRetrieve(', 'AutoPutLootInInventory('),
            ('object.cpp', 'bool Object::HandleClick(', 'sender->PutItemInInventory('),
            ('object.cpp', 'void Object::Close(', 'container->PopItem('),
            ('inventory.cpp', 'bool Client::SwapItem(', 'm_tradeskill_object->PopItem('),
            ('tradeskills.cpp', 'void Object::HandleAugmentation(', 'tobe_auged->PutAugment('),
        ]
        for source, signature, transfer in cases:
            with self.subTest(signature=signature):
                method = native.body((native.CODE / 'zone' / source).read_text(encoding='utf-8'), signature)
                self.assertLess(method.index('.Conflict('), method.index(transfer))


if __name__ == '__main__':
    unittest.main()
