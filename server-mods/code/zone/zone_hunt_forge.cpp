#include "zone/client.h"
#include "zone/command.h"
#include "zone/advanced_loot_inventory.h"
#include "common/zone_hunt_catalog.h"
#include "common/zone_hunt_policy.h"
#include "common/content/world_content_service.h"
#include "common/say_link.h"
#include "common/seperator.h"

void command_zoneforge(Client *c, const Seperator *sep)
{
	c->ZoneForge(sep->arg[1]);
}

void Client::ZoneForge(const std::string &request_id)
{
	if (!Connected() || !ClientDataLoaded()) { return; }
	if (IsDead() || IsEngaged() || auto_attack || IsCasting() || IsStunned() || IsMezzed() || IsFeared() ||
		IsAIControlled() || (trade && trade->With()) || GetTradeskillObject() || IsLooting() ||
		GetMerchantSessionEntityID() || !m_inv.CursorEmpty()) {
		Message(Chat::Yellow,"Finish combat, close trading/loot windows, and empty your cursor before forging."); return;
	}
	if (WorldContentService::Instance()->GetCurrentExpansion()!=0) {
		Message(Chat::Yellow,"Classic zone forging is unavailable in this era."); return;
	}
	if (!request_id.empty()) {
		const auto found = m_zone_forge_quotes.find(request_id);
		if (found==m_zone_forge_quotes.end()) { Message(Chat::Yellow,"That choice has expired. Type #zoneforge for current choices."); return; }
		const auto inputs = found->second;
		m_zone_forge_quotes.clear(); // Never reuse an old choice, even after a rejected attempt.
		const auto result = NightcapLoot::ForgeItems(this, inputs, request_id);
		if (result==NightcapLoot::TransferResult::Delivered) {
			Message(Chat::Green,"Three copies became one upgraded reward. Type #zoneforge to see more choices.");
		} else if (result==NightcapLoot::TransferResult::Declined) {
			Message(Chat::Yellow,"The forge could not complete that choice. No items were exchanged. Type #zoneforge to refresh.");
		}
		return;
	}
	m_zone_forge_quotes.clear();
	auto state = database.QueryDatabase(fmt::format("SELECT revision FROM nightcap_zone_hunt_state WHERE id=1 AND enabled=1 AND revision={}",NightcapHunt::Revision),false);
	if (!state.Success() || state.RowCount()!=1) { Message(Chat::Yellow,"The zone forge is currently unavailable."); return; }
	std::map<uint32,std::vector<NightcapLoot::ForgeInput>> families;
	for (int16 slot : NightcapLoot::ForgeSlots(this)) {
		const auto item = m_inv.GetItem(slot);
		if (NightcapLoot::PlainForgeItem(item)) { families[item->GetID()].emplace_back(slot,item->GetSerialNumber()); }
	}
	Message(Chat::White,"Choose an upgrade: consume three identical copies from your bags for one next-quality copy, with no fee. Equipped, socketed and customized items are excluded.");
	for (const auto &[id, copies] : families) {
		if (copies.size()<3) { continue; }
		const auto output = database.GetItem(NightcapHunt::NextTier(id));
		const auto input = database.GetItem(id);
		if (!output || !input) { continue; }
		const auto token = NightcapLoot::NewDropID();
		m_zone_forge_quotes[token] = {copies.begin(),copies.begin()+3};
		EQ::SayLinkEngine link; link.SetLinkType(EQ::saylink::SayLinkItemData); link.SetItemData(output);
		const auto action = Saylink::Silent("#zoneforge "+token,"Forge three");
		Message(Chat::White,"3 x %s -> %s. %s",input->Name,link.GenerateLink().c_str(),action.c_str());
	}
	if (m_zone_forge_quotes.empty()) { Message(Chat::Yellow,"You do not have three eligible copies of any upgradeable zone reward."); }
}
