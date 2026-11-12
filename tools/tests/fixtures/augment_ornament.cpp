// Only item storage is doubled; classification, socket selection and updates
// are extracted from the production implementation by the Python runner.
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <string>
using uint32 = uint32_t;
using uint8 = uint8_t;
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr, "line %d: %s\n", __LINE__, #x); std::exit(1); } } while(false)
// NATIVE_ENUM
namespace Strings {
uint32 ToUnsignedInt(const char* value) { return static_cast<uint32>(std::strtoul(value, nullptr, 10)); }
}
namespace EQ {
template<typename T, typename A, typename B> bool ValueWithin(T value, A low, B high) { return value >= low && value <= high; }
namespace invaug { constexpr int SOCKET_BEGIN = 0, SOCKET_END = 5; }
struct ItemData {
 uint32 AugType = 0, Icon = 100, HerosForgeModel = 0;
 char IDFile[32] = "IT100";
 bool common = true;
 bool IsClassCommon() const { return common; }
};
struct ItemInstance {
 ItemData* m_item = nullptr;
 std::array<ItemInstance*, 6> augments{};
 uint32 icon = 0, model = 0, hero = 0;
 const ItemData* GetItem() const { return m_item; }
 int GetAugmentType() const { return m_item ? static_cast<int>(m_item->AugType) : 0; }
 ItemInstance* GetAugment(int index) const { return augments[index]; }
 void SetOrnamentIcon(uint32 value) { icon = value; }
 void SetOrnamentHeroModel(uint32 value) { hero = value; }
 void SetOrnamentationIDFile(uint32 value) { model = value; }
 bool IsOrnamentationAugment(ItemInstance*) const;
 ItemInstance* GetOrnamentationAugment() const;
 bool UpdateOrnamentationInfo();
};
}
// NATIVE_METHODS
constexpr uint32 Type(unsigned number) { return 1u << (number - 1); }
namespace AugmentActions { enum Action { Insert, Swap, Remove, Destroy }; }
namespace EQ { namespace invslot { constexpr int slotCursor = 30; } }
void Change(EQ::ItemInstance& host, AugmentActions::Action action, int index, EQ::ItemInstance* cursor) {
 struct { AugmentActions::Action augment_action; int augment_index; } request{action, index};
 auto* in_augment = &request;
 auto* tobe_auged = &host;
 struct Inventory {
  EQ::ItemInstance* cursor;
  EQ::ItemInstance* GetItem(int) { return cursor; }
 } user_inv{cursor};
 // The decision and refresh block are extracted from the actual packet handler.
 // Only the socket/cursor storage mutation between them is doubled.
 // NATIVE_AUGMENT_DECISION
 host.augments[index] = (action == AugmentActions::Insert || action == AugmentActions::Swap) ? cursor : nullptr;
 // NATIVE_AUGMENT_REFRESH
 // Keep boundary variables used by the unpatched RED fixture too.
 (void)in_augment; (void)user_inv;
}
int main() {
 EQ::ItemData base, stat, ornament;
 EQ::ItemInstance host, aug, cosmetic, missing;
 host.m_item = &base; aug.m_item = &stat; cosmetic.m_item = &ornament;
 stat.AugType = Type(22); stat.Icon = 944;
 host.augments[0] = &aug;

 // The shipped Hunt definitions use type22, empty IDFile and no Hero's Forge.
 std::snprintf(stat.IDFile, sizeof(stat.IDFile), "%s", "");
 CHECK(!host.IsOrnamentationAugment(&aug));
 CHECK(!host.GetOrnamentationAugment());
 CHECK(!host.UpdateOrnamentationInfo());
 CHECK(host.icon == 0 && host.model == 0 && host.hero == 0);

 // Ordinary model names, placeholders and arbitrary stat socket types do not
 // confer cosmetic intent. Numeric 20/21 are bit combinations, not type20/21.
 for (const char* id : {"", "IT63", "IT64", "IT900", "IT"}) {
  std::snprintf(stat.IDFile, sizeof(stat.IDFile), "%s", id);
  for (uint32 mask : {0u, Type(1), Type(7), Type(22), 20u, 21u, Type(1) | Type(22)}) {
   stat.AugType = mask;
   CHECK(!host.IsOrnamentationAugment(&aug));
  }
 }
 stat.AugType = Type(22); std::snprintf(stat.IDFile, sizeof(stat.IDFile), "%s", "IT900");
 CHECK(!host.IsOrnamentationAugment(nullptr));
 CHECK(!host.IsOrnamentationAugment(&missing));
 CHECK(!missing.IsOrnamentationAugment(&aug));
 base.common = false; CHECK(!host.UpdateOrnamentationInfo()); base.common = true;

 // Real ornaments behind stat sockets must still win. AugType is a mask.
 ornament.Icon = 700; std::snprintf(ornament.IDFile, sizeof(ornament.IDFile), "%s", "IT321");
 host.augments[5] = &cosmetic;
 for (uint32 mask : {Type(20), Type(21), Type(1) | Type(20), Type(20) | Type(21)}) {
  ornament.AugType = mask;
  CHECK(host.GetOrnamentationAugment() == &cosmetic);
  CHECK(host.UpdateOrnamentationInfo());
  CHECK(host.icon == 700 && host.model == 321 && host.hero == 0);
 }
 // Preserve the existing explicit Hero's Forge marker fallback.
 ornament.AugType = Type(1); ornament.HerosForgeModel = 7;
 CHECK(host.UpdateOrnamentationInfo()); CHECK(host.hero == 7);
 ornament.AugType = Type(20); ornament.HerosForgeModel = 0;
 std::snprintf(ornament.IDFile, sizeof(ornament.IDFile), "%s", "");
 CHECK(host.UpdateOrnamentationInfo()); CHECK(host.model == 0 && host.icon == 700);

 // Removing the ornament leaves stat augments/stats alone and clears all
 // derived cosmetic fields, including stale fields caused by the old bug.
 host.augments[5] = nullptr; host.icon = 944; host.model = 900; host.hero = 3;
 CHECK(!host.UpdateOrnamentationInfo());
 CHECK(host.icon == 0 && host.model == 0 && host.hero == 0);
 CHECK(host.augments[0] == &aug && stat.Icon == 944 && base.Icon == 100);

 // Mold/quest cosmetics are instance overrides without a socket ornament.
 // Ordinary stat insert/swap/remove/destroy must preserve all three fields.
 for (auto action : {AugmentActions::Insert, AugmentActions::Swap, AugmentActions::Remove, AugmentActions::Destroy}) {
  host.icon = 777; host.model = 333; host.hero = 7;
  host.augments[0] = &aug;
  Change(host, action, 0, &aug);
  CHECK(host.icon == 777 && host.model == 333 && host.hero == 7);
 }
 ornament.AugType = Type(20); std::snprintf(ornament.IDFile, sizeof(ornament.IDFile), "%s", "IT321");
 // A real ornament on the cursor is irrelevant to a Remove/Destroy request.
 for (auto action : {AugmentActions::Remove, AugmentActions::Destroy}) {
  host.icon = 777; host.model = 333; host.hero = 7; host.augments[0] = &aug;
  Change(host, action, 0, &cosmetic);
  CHECK(host.icon == 777 && host.model == 333 && host.hero == 7);
 }
 for (auto action : {AugmentActions::Insert, AugmentActions::Swap}) {
  host.augments[0] = &aug; Change(host, action, 0, &cosmetic);
  CHECK(host.icon == 700 && host.model == 321 && host.hero == 0);
 }
 for (auto action : {AugmentActions::Swap, AugmentActions::Remove, AugmentActions::Destroy}) {
  host.augments[0] = &cosmetic; host.icon = 700; host.model = 321;
  Change(host, action, 0, &aug);
  CHECK(host.icon == 0 && host.model == 0 && host.hero == 0);
 }
 std::puts("augment ornament native controls passed");
}
