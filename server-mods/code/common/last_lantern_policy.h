#pragma once
#include <algorithm>
#include <cstdint>

// Native Tasks supply the completion bits at each operation. This policy does
// not persist a second campaign progress ledger.
namespace NightcapLantern {
constexpr uint32_t Revision = 2026110701;
constexpr unsigned FirstTask = 9500, TaskCount = 16;
constexpr unsigned FirstArmor = 964000, ArmorCount = 128, Charm = 900501;
constexpr unsigned OfferLevels[TaskCount] = {20,25,30,35,35,35,35,35,38,40,42,45,46,48,50,50};
constexpr unsigned SlotTasks[8] = {0,1,2,8,9,10,12,15};
constexpr unsigned AwardLevels[8] = {20,25,30,38,40,42,46,50};
constexpr unsigned WornSlots[8] = {19,12,9,10,7,18,2,17};
constexpr uint32_t FitClasses[4] = {65535, 65535 & ~15360u,
	65535 & ~(15360u | 32u | 64u | 16384u), 151};

struct Armor { bool valid=false; unsigned fit=0, grade=0, slot=0; };
constexpr bool IsArmor(unsigned id) { return id>=FirstArmor && id<FirstArmor+ArmorCount; }
constexpr bool IsCampaignItem(unsigned id) { return id==Charm || IsArmor(id); }
constexpr unsigned ArmorID(unsigned fit, unsigned grade, unsigned slot) {
	return fit<4 && grade<4 && slot<8 ? FirstArmor+fit*32+grade*8+slot : 0;
}
constexpr Armor Decode(unsigned id) {
	return IsArmor(id) ? Armor{true,(id-FirstArmor)/32,((id-FirstArmor)%32)/8,(id-FirstArmor)%8} : Armor{};
}
constexpr bool HasOath(uint16_t completed) {
	return (completed & 7)==7 && (completed & 248)!=0;
}
constexpr unsigned Grade(uint16_t completed) {
	return completed & (1u<<15) ? 3 : completed & (1u<<12) ? 2 : completed & (1u<<9) ? 1 : 0;
}
constexpr bool FitAllowed(unsigned fit,uint32_t classes) {
	return fit<4 && (classes & 65535) && !(classes & ~65535u) && (FitClasses[fit] & classes);
}
constexpr unsigned RequiredLevel(unsigned grade,unsigned slot) {
	return grade<4 && slot<8 ? std::max(AwardLevels[slot],grade==3 ? 50u : grade==2 ? 46u : grade==1 ? 40u : 0u) : 255;
}
constexpr bool CanOffer(unsigned task,unsigned level,uint16_t completed) {
	if (task<FirstTask || task>=FirstTask+TaskCount) { return false; }
	const unsigned index=task-FirstTask;
	if (level<OfferLevels[index] || (completed & (1u<<index))) { return false; }
	if (index<3) { return (completed & ((1u<<index)-1))==((1u<<index)-1); }
	if (index<8) { return (completed & 7)==7; }
	if (!HasOath(completed)) { return false; }
	const unsigned previous=((1u<<index)-1)&~255u;
	return (completed & previous)==previous;
}
constexpr bool ArmorEarned(unsigned id,unsigned level,uint32_t classes,uint16_t completed) {
	const auto a=Decode(id);
	if (!a.valid) { return false; }
	const unsigned earned=SlotTasks[a.slot];
	if (!CanOffer(FirstTask+earned,255,completed & ~(1u<<earned))) { return false; }
	if (a.grade) {
		const unsigned milestone=a.grade==3 ? 15 : a.grade==2 ? 12 : 9;
		if (!(completed&(1u<<milestone)) || !CanOffer(FirstTask+milestone,255,completed & ~(1u<<milestone))) { return false; }
	}
	return a.valid && FitAllowed(a.fit,classes) && level>=RequiredLevel(a.grade,a.slot) &&
		(completed & (1u<<SlotTasks[a.slot])) && (a.slot<3 || HasOath(completed)) && a.grade<=Grade(completed);
}
constexpr bool CanRefit(unsigned source,unsigned target,unsigned level,uint32_t classes,uint16_t completed) {
	const auto a=Decode(source), b=Decode(target);
	return source!=target && a.valid && b.valid && a.slot==b.slot && b.grade>=a.grade &&
		b.grade==Grade(completed) && ArmorEarned(target,level,classes,completed);
}

// Apply after global FreeTrade and item-disable rules, in the item cache used by
// every native consumer. Campaign equipment is an earned personal entitlement.
template<class Item> void ApplyEffectivePolicy(Item &item) {
	if (!IsCampaignItem(item.ID)) { return; }
	item.NoDrop=0; item.NoTransfer=1; item.NoPet=1; item.NoRent=255;
	item.FreeTrade=false; item.FVNoDrop=1;
	item.Price=0; item.FixedSellPrice=0; item.Attuneable=false; item.LoreFlag=false;
}
}
