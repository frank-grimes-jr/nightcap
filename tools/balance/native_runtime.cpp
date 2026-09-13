// Isolated native runtime adapter. No sockets, production objects, or headers are modified.
#include "native_runtime.h"
#include "zone/client.h"
#include "zone/entity.h"
#include "zone/npc.h"
#include "zone/zone.h"
#include "zone/aa_ability.h"
#include "zone/mob_movement_manager.h"
#include "common/eq_stream_intf.h"
#include "common/ptimer.h"
#include "common/misc_functions.h"
#include "common/opcodemgr.h"
#include "common/servertalk.h"
#include <sys/time.h>
#include <ctime>
#include <deque>
#include <map>
#include <set>
#include <stdexcept>

using json = nlohmann::json;
extern EntityList entity_list;
extern Zone *zone;
extern volatile bool is_zone_loaded;
extern uint32 current_time;
extern uint32 last_time;
extern double frame_time;
// The isolated harness has no world connection. Fail closed on unmodeled
// notifications instead of dereferencing its absent network connection.
extern "C" bool __wrap__ZN11WorldServer10SendPacketEP12ServerPacket(void *, ServerPacket *packet)
{
	throw std::runtime_error("Unexpected isolated world notification opcode " + std::to_string(packet->opcode));
}
static bool virtual_clock = false;
static uint64_t elapsed_ms = 0;
static constexpr time_t epoch = 1789171200;
extern "C" int __real_gettimeofday(timeval *, void *);
extern "C" time_t __real_time(time_t *);
extern "C" int __wrap_gettimeofday(timeval *tv, void *tz)
{
	if (!virtual_clock) { return __real_gettimeofday(tv,tz); }
	if (tz) { throw std::runtime_error("Unsupported timezone argument to diagnostic clock"); }
	tv->tv_sec = epoch + elapsed_ms / 1000;
	tv->tv_usec = (elapsed_ms % 1000) * 1000;
	return 0;
}
extern "C" time_t __wrap_time(time_t *out)
{
	if (!virtual_clock) { return __real_time(out); }
	auto value = epoch + elapsed_ms / 1000;
	if (out) { *out = value; }
	return value;
}
static void Advance(uint32 milliseconds)
{
	elapsed_ms += milliseconds;
	frame_time = milliseconds / 1000.0;
	Timer::SetCurrentTime();
	if (Timer::GetCurrentTime() != elapsed_ms) { throw std::runtime_error("Native clock drift"); }
}
void NightcapBalanceStartClock()
{
	if (virtual_clock) { throw std::runtime_error("Clock can only start once per process"); }
	virtual_clock = true;
	elapsed_ms = 0;
	current_time = last_time = 0;
	Timer::SetCurrentTime();
}

class BalanceStream : public EQStreamInterface {
public:
	RegularOpcodeManager opcode_manager;
	uint64_t outgoing = 0;
	bool capture_messages = false;
	bool capture_damage_type = false;
	json events = json::array();
	std::deque<EQApplicationPacket *> incoming;
	EQStreamState state = ESTABLISHED;
	void QueuePacket(const EQApplicationPacket *p, bool = true) override
	{
		++outgoing;
		if (events.size() >= 50000) { throw std::runtime_error("Packet trace limit exceeded"); }
		if (p->GetOpcode() == OP_Damage && p->size == sizeof(CombatDamage_Struct)) {
			auto *d = reinterpret_cast<const CombatDamage_Struct *>(p->pBuffer);
			events.push_back({{"ms",Timer::GetCurrentTime()},{"type","damage"},
				{"source",d->source},{"target",d->target},{"spell",d->spellid},{"damage",static_cast<int32>(d->damage)}});
			if (capture_damage_type) { events.back()["damage_type"] = d->type; }
		} else if (p->GetOpcode() == OP_BeginCast && p->size == sizeof(BeginCast_Struct)) {
			auto *d = reinterpret_cast<const BeginCast_Struct *>(p->pBuffer);
			events.push_back({{"ms",Timer::GetCurrentTime()},{"type","begin_cast"},
				{"source",d->caster_id},{"spell",d->spell_id},{"raw_cast_ms",d->cast_time}});
		} else if (capture_messages && p->GetOpcode() == OP_FormattedMessage && p->size >= sizeof(FormattedMessage_Struct)) {
			auto *d = reinterpret_cast<const FormattedMessage_Struct *>(p->pBuffer);
			events.push_back({{"ms",Timer::GetCurrentTime()},{"type","message"},{"string_id",d->string_id}});
		} else if (capture_messages && p->GetOpcode() == OP_SimpleMessage && p->size == sizeof(SimpleMessage_Struct)) {
			auto *d = reinterpret_cast<const SimpleMessage_Struct *>(p->pBuffer);
			events.push_back({{"ms",Timer::GetCurrentTime()},{"type","message"},{"string_id",d->string_id}});
		}
	}
	void FastQueuePacket(EQApplicationPacket **p, bool = true) override
	{
		if (*p) { QueuePacket(*p); delete *p; *p = nullptr; }
	}
	EQApplicationPacket *PopPacket() override
	{
		if (incoming.empty()) { return nullptr; }
		auto *p = incoming.front(); incoming.pop_front(); return p;
	}
	void Close() override { state = CLOSED; }
	void ReleaseFromUse() override {}
	void RemoveData() override { while (auto *p = PopPacket()) { delete p; } }
	std::string GetRemoteAddr() const override { return "127.0.0.1"; }
	uint32 GetRemoteIP() const override { return 0x0100007f; }
	uint16 GetRemotePort() const override { return 0; }
	bool CheckState(EQStreamState value) override { return state == value; }
	std::string Describe() const override { return "isolated balance packet sink"; }
	EQStreamState GetState() override { return state; }
	void SetOpcodeManager(OpcodeManager **) override {}
	OpcodeManager *GetOpcodeManager() const override { return const_cast<RegularOpcodeManager *>(&opcode_manager); }
	const EQ::versions::ClientVersion ClientVersion() const override { return EQ::versions::ClientVersion::RoF2; }
	Stats GetStats() const override { return {}; }
	void ResetStats() override {}
	EQStreamManagerInterface *GetManager() const override { return nullptr; }
};
static std::map<Client *,BalanceStream *> streams;
static std::set<Mob *> terminal;
static bool capture_terminal = false;
static json terminal_events = json::array();
bool NightcapBalanceIsTerminal(Mob *mob) { return terminal.count(mob); }
bool NightcapBalanceRecordDeath(Mob *mob)
{
	if (!virtual_clock) { throw std::runtime_error("Unexpected death outside runtime mode"); }
	const bool first = terminal.insert(mob).second;
	if (capture_terminal && first) {
		terminal_events.push_back({{"ms",Timer::GetCurrentTime()},{"entity_id",mob->GetID()},
			{"hp",mob->GetHP()},{"max_hp",mob->GetMaxHP()},{"mana",mob->GetMana()}});
	}
	return true;
}
EQStreamInterface *NightcapBalanceStream(Client *client)
{
	if (!virtual_clock) { return nullptr; }
	auto *stream = new BalanceStream();
	streams.emplace(client,stream);
	return stream;
}

json NightcapBalanceRuntimeProbe(Client *c)
{
	if (!virtual_clock || !streams.count(c) || !c->Connected()) {
		throw std::runtime_error("Runtime probe requires a connected diagnostic client");
	}
	// Distinct boundary conventions are intentional engine behavior.
	Timer ordinary(1000);
	PersistentTimer persistent(c->CharacterID(),pTimerAAStart,1);
	Advance(1000);
	json clock = {{"at_1000_timer",ordinary.Check(false)},
		{"at_1000_persistent",persistent.Expired(nullptr,true)},
		{"seconds",Timer::GetTimeSeconds()},{"time",time(nullptr)}};
	Advance(1);
	clock["at_1001_timer"] = ordinary.Check(false);
	Advance(999);
	clock["at_2000_persistent"] = persistent.Expired(nullptr,true);
	if (clock["at_1000_timer"] != false || clock["at_1001_timer"] != true
		|| clock["at_1000_persistent"] != true
		|| clock["at_2000_persistent"] != true || clock["seconds"] != epoch+1 || clock["time"] != epoch+1) {
		throw std::runtime_error("Native timer boundary control failed");
	}
	c->SetName("BalanceProbe");
	c->ChangeSize(6,true);
	c->SetPosition(0,0,0);
	entity_list.AddClient(c);
	c->SetHP(c->GetMaxHP()/2);
	c->Mob::SetMana(c->GetMaxMana());
	const uint16 spell_id = 9; // Superior Healing: full CastSpell/SpellProcess path.
	c->GetPP().mem_spells[0] = spell_id;
	json trace = json::array();
	auto sample = [&]() { trace.push_back({{"ms",Timer::GetCurrentTime()},
		{"hp",c->GetHP()},{"mana",c->GetMana()},{"casting",c->CastingSpellID()}}); };
	sample();
	const bool accepted = c->CastSpell(spell_id,c->GetID(),static_cast<EQ::spells::CastingSlot>(0));
	sample();
	for (int step = 0; step < 200; ++step) {
		const auto hp = c->GetHP(), mana = c->GetMana();
		const auto casting = c->CastingSpellID();
		Advance(50);
		if (!c->Process()) { throw std::runtime_error("Native client processing terminated"); }
		if (step % 10 == 9 || hp != c->GetHP() || mana != c->GetMana() || casting != c->CastingSpellID()) { sample(); }
	}
	const auto *npc_type = content_db.LoadNPCTypesData(32040);
	if (!npc_type) { throw std::runtime_error("Missing damage-control NPC"); }
	auto *npc = new NPC(npc_type,nullptr,glm::vec4(0,0,0,0),GravityBehavior::Water);
	const auto hp_before = c->GetHP();
	c->Damage(npc,100,SPELL_UNKNOWN,EQ::skills::SkillHandtoHand,false);
	const auto hp_after = c->GetHP();
	if (!c->ClientFinishedLoading() || hp_before <= hp_after || hp_before-hp_after > 100) {
		throw std::runtime_error("Native damage control failed; fixture may have login protection");
	}
	return {{"clock",clock},{"cast_accepted",accepted},{"trace",trace},
		{"damage_control",{{"requested_damage",100},{"hp_before",hp_before},{"hp_after",hp_after},
			{"client_finished_loading",c->ClientFinishedLoading()}}},
		{"outgoing_packets",streams.at(c)->outgoing},{"connected",c->Connected()},
		{"client_version_bit",c->ClientVersionBit()},
		{"scope","Native clock/connected Client::Process/self-heal control; not a boss fight"}};
}

static json AABuffState(Client *c)
{
	json buffs = json::array();
	for (int slot = 0; slot < c->GetMaxTotalSlots(); ++slot) {
		const auto &b = c->GetBuffs()[slot];
		if (IsValidSpell(b.spellid)) {
			buffs.push_back({{"slot",slot},{"spell",b.spellid},{"ticks",b.ticsremaining},{"hits",b.hit_number}});
		}
	}
	return {{"hp",c->GetHP()},{"max_hp",c->GetMaxHP()},{"mana",c->GetMana()},
		{"casting",c->CastingSpellID()},{"buffs",buffs}};
}

static json PetCombat(Client *c, const json &input);

json NightcapBalancePetProbe(Client *c, const json &input)
{
	if (!virtual_clock || !c->Connected() || !c->ClientFinishedLoading() || c->GetGM()) {
		throw std::runtime_error("Pet control requires a connected non-GM runtime client");
	}
	const auto &actions = input.at("actions");
	if (!actions.is_array() || actions.empty() || actions.size() > 24) {
		throw std::runtime_error("Pet control requires 1..24 actions");
	}
	zone->ReloadMaps();
	if (!zone->zonemap || !zone->pathing || !zone->watermap) { throw std::runtime_error("Pet control requires native maps"); }
	is_zone_loaded = true;
	c->SetName("BalancePetOwner"); c->ChangeSize(6,true);
	if (input.contains("combat")) {
		const auto &combat = input.at("combat");
		const auto p = combat.at("npc_position").get<std::vector<float>>();
		const float distance = combat.at("starting_distance");
		if (p.size() != 4 || !std::all_of(p.begin(),p.end(),[](float v) { return std::isfinite(v); })
			|| !std::isfinite(distance) || distance < 10 || distance > 500) { throw std::runtime_error("Invalid pet combat position"); }
		c->SetPosition(p[0]+distance,p[1],p[2]);
	} else { c->SetPosition(-861,-1395,104.879997); }
	c->SetHP(c->GetMaxHP()); c->Mob::SetMana(c->GetMaxMana());
	entity_list.AddClient(c);
	auto *stream = streams.at(c);
	stream->capture_messages = true;
	stream->capture_damage_type = true;
	// Explicit inventory supplies; native completion performs reagent checks and consumption.
	int supply_slot = EQ::invslot::GENERAL_BEGIN;
	for (const auto &supply : input.value("reagents",json::array())) {
		const int id = supply.at("id"), count = supply.at("count");
		if ((id != 10015 && id != 13073 && id != 13080) || count < 1 || count > 20
			|| supply_slot > EQ::invslot::GENERAL_END) { throw std::runtime_error("Invalid pet reagent supply"); }
		std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(id,count));
		if (!item || c->GetInv().PutItem(supply_slot,*item) != supply_slot) { throw std::runtime_error("Pet reagent insertion failed"); }
		++supply_slot;
	}
	auto state = [&]() {
		json pets = json::array(), refs = json::array(), supplies = json::array();
		for (int class_id : {10,11,13}) { refs.push_back({{"class",class_id},{"entity_id",c->GetClassPet(class_id)}}); }
		for (const auto &entry : entity_list.GetNPCList()) {
			auto *pet = entry.second;
			json buffs = json::array();
			for (int slot = 0; slot < pet->GetMaxTotalSlots(); ++slot) {
				const auto &b = pet->GetBuffs()[slot];
				if (IsValidSpell(b.spellid)) { buffs.push_back({{"spell",b.spellid},{"ticks",b.ticsremaining}}); }
			}
			pets.push_back({{"entity_id",pet->GetID()},{"npc_id",pet->GetNPCTypeID()},
				{"owner_id",pet->GetOwnerID()},{"spell",pet->GetPetSpellID()},{"level",pet->GetLevel()},
				{"hp",pet->GetHP()},{"max_hp",pet->GetMaxHP()},{"mana",pet->GetMana()},
				{"ac",pet->GetAC()},{"atk",pet->GetATK()},{"haste",pet->GetHaste()},
				{"min_damage",pet->GetMinDMG()},{"max_damage",pet->GetMaxDMG()},{"power",pet->GetPetPower()},
				{"engaged",pet->IsEngaged()},{"depop",pet->GetDepop()},
				{"position",{pet->GetX(),pet->GetY(),pet->GetZ()}},{"buffs",buffs}});
		}
		std::sort(pets.begin(),pets.end(),[](const json &a,const json &b) { return a.at("entity_id") < b.at("entity_id"); });
		for (int slot = EQ::invslot::GENERAL_BEGIN; slot < supply_slot; ++slot) {
			const auto *item = c->GetInv().GetItem(slot);
			supplies.push_back({{"slot",slot},{"id",item ? item->GetID() : 0},{"count",item ? item->GetCharges() : 0}});
		}
		return json{{"ms",Timer::GetCurrentTime()},{"player",AABuffState(c)},
			{"primary_pet",c->GetPetID()},{"class_pets",refs},{"pets",pets},{"reagents",supplies}};
	};
	auto process = [&]() {
		Advance(50);
		entity_list.MobProcess();
		MobMovementManager::Get().Process();
		if (!terminal.empty() || !c->Connected()) { throw std::runtime_error("Pet control lost its client"); }
	};
	json results = json::array();
	const json initial = state();
	for (const auto &action : actions) {
		const int spell_id = action.at("spell");
		const std::set<int> supported = {633,443,166,690,107,67,145,60,61,168,170,644};
		if (!supported.count(spell_id)) {
			throw std::runtime_error("Unsupported pet-control spell");
		}
		if (!IsValidSpell(spell_id) || c->GetSpellMinLevel(spell_id) > c->GetLevel()) {
			throw std::runtime_error("Level-ineligible pet-control spell");
		}
		uint32 recast_wait = 0;
		if (input.value("recover_before_combat",false)) {
			auto *timer = c->GetPTimers().Get(pTimerSpellStart+spell_id);
			while (timer && timer->GetRemainingTime() > 0 && recast_wait < 60000) { process(); recast_wait += 50; }
			if (timer && timer->GetRemainingTime() > 0) { throw std::runtime_error("Pet preparation recast wait exceeded one minute"); }
		}
		const int target_class = action.value("target_class",0);
		Mob *target = c;
		if (target_class) {
			if (target_class != 13 && target_class != 11 && target_class != 10) { throw std::runtime_error("Unsupported pet target class"); }
			target = entity_list.GetMob(target_class == 13 ? c->GetPetID() : c->GetClassPet(target_class));
			if (!target) { throw std::runtime_error("Pet-control target is absent"); }
		}
		c->SetTarget(target);
		c->GetPP().mem_spells[0] = spell_id;
		const json before = state();
		const bool accepted = c->CastSpell(spell_id,target->GetID(),static_cast<EQ::spells::CastingSlot>(0));
		uint32 waited = 0;
		do { process(); waited += 50; } while (c->IsCasting() && waited < 60000);
		if (c->IsCasting()) { throw std::runtime_error("Pet-control cast exceeded time budget"); }
		const json completed = state();
		const uint32 settle = std::max<uint32>(1500,spells[spell_id].recovery_time + 50);
		for (uint32 ms = 0; ms < settle; ms += 50) { process(); }
		results.push_back({{"input",action},{"accepted",accepted},{"before",before},{"completed",completed},{"settled",state()}});
		if (input.value("recover_before_combat",false)) { results.back()["recast_wait_ms"] = recast_wait; }
	}
	json owner_check;
	if (input.contains("owner_lookup_control")) {
		const std::string method = input.at("owner_lookup_control");
		if (method != "owner" && method != "owner_or_self") { throw std::runtime_error("Unknown owner lookup control"); }
		auto *pet = entity_list.GetMob(c->GetClassPet(11));
		if (!pet) { throw std::runtime_error("Owner lookup control requires a surviving Necromancer pet"); }
		owner_check = {{"method",method},{"pet_id",pet->GetID()},
			{"registered_owner",pet->GetOwner() == c},{"registered_owner_or_self",pet->GetOwnerOrSelf() == c}};
		// Negative control: a mere owner ID must not retain an unregistered pet.
		c->RemoveClassPet(11);
		auto *resolved = method == "owner" ? pet->GetOwner() : pet->GetOwnerOrSelf();
		owner_check["unregistered_result"] = resolved ? resolved->GetID() : 0;
		owner_check["unregistered_owner_id"] = pet->GetOwnerID();
		owner_check["unregistered_depop"] = pet->CastToNPC()->GetDepop();
	}
	for (int ms = 0; ms < 12000; ms += 50) { process(); }
	json recovery;
	if (input.value("recover_before_combat",false)) {
		const auto recovery_start = Timer::GetCurrentTime();
		json trace = json::array(), heals = json::array();
		auto recovery_state = [&]() { auto s = state(); s["sitting"] = c->IsSitting(); return s; };
		trace.push_back(recovery_state());
		auto posture = [&](bool sitting) {
			if (c->IsSitting() == sitting) { return true; }
			auto *packet = new EQApplicationPacket(OP_SpawnAppearance,sizeof(SpawnAppearance_Struct));
			auto *a = reinterpret_cast<SpawnAppearance_Struct *>(packet->pBuffer);
			a->spawn_id = c->GetID(); a->type = AppearanceType::Animation;
			a->parameter = sitting ? Animation::Sitting : Animation::Standing;
			stream->incoming.push_back(packet);
			return false;
		};
		uint32 ready = 0;
		bool was_casting = false, done = false;
		for (int ms = 50; ms <= 900000; ms += 50) {
			process();
			if (was_casting && !c->IsCasting()) { ready = ms + std::max<uint32>(250,spells[15].recovery_time); }
			was_casting = c->IsCasting();
			bool pets_full = true;
			Mob *heal_target = c->GetHPRatio() < 90 ? c : nullptr;
			for (const auto &entry : entity_list.GetNPCList()) {
				auto *pet = entry.second;
				if (pet->GetOwnerID() != c->GetID()) { continue; }
				pets_full = pets_full && pet->GetHP() == pet->GetMaxHP();
				if (pet->GetHP() < pet->GetMaxHP() && (!heal_target || pet->GetHPRatio() < heal_target->GetHPRatio())) { heal_target = pet; }
			}
			if (!c->IsCasting() && ms >= ready) {
				if (c->GetMana() == c->GetMaxMana() && c->GetHPRatio() >= 95 && pets_full) {
					if (!posture(false)) { continue; }
					done = true; break;
				}
				auto *heal_timer = c->GetPTimers().Get(pTimerSpellStart+15);
				if (heal_target && c->GetMana() >= 2*spells[15].mana && (!heal_timer || heal_timer->GetRemainingTime() == 0)) {
					if (!posture(false)) { continue; }
					c->GetPP().mem_spells[0] = 15;
					const bool accepted = c->CastSpell(15,heal_target->GetID(),static_cast<EQ::spells::CastingSlot>(0));
					heals.push_back({{"ms",Timer::GetCurrentTime()},{"target",heal_target->GetID()},{"accepted",accepted}});
					was_casting = c->IsCasting(); ready = ms+250;
				} else { posture(true); }
			}
			if (ms % 6000 == 0) { trace.push_back(recovery_state()); }
		}
		if (!done) { throw std::runtime_error("Pet preparation failed to recover native resources within 15 minutes"); }
		trace.push_back(recovery_state());
		recovery = {{"elapsed_ms",Timer::GetCurrentTime()-recovery_start},{"trace",trace},{"heals",heals},
			{"max_mana",c->GetMaxMana()},
			{"scope","Native sitting recovery and Greater Healing; full mana/pet HP, owner HP at least95% with Lich active; no resource resets"}};
	}
	json result = {{"input",input},{"player_entity_id",c->GetID()},{"initial",initial},{"actions",results},
		{"final",state()},{"events",stream->events},
		{"owner_lookup_control",owner_check},
		{"scope","Native cast completion, reagent inventory, entity processing and pet movement; no fabricated ownership or stats, no encounter claim"}};
	if (!recovery.is_null()) { result["recovery"] = recovery; }
	if (input.contains("combat")) { result["combat"] = PetCombat(c,input.at("combat")); }
	return result;
}

static AA::Rank *ValidateActiveRank(Client *c, int rank_id)
{
	auto *r = zone->GetAlternateAdvancementRank(rank_id);
	const std::set<int> supported = {300,308,38,169,515};
	if (!r || !r->base_ability || !supported.count(r->base_ability->id)
		|| r->base_ability->charges || !r->effects.empty() || !IsValidSpell(r->spell)
		|| !c->CanUseAlternateAdvancementRank(r) || r->level_req > c->GetLevel()
		|| c->GetAA(rank_id) != r->current_value) {
		throw std::runtime_error("Unsupported or unowned active AA rank " + std::to_string(rank_id));
	}
	return r;
}

static json AttemptAA(Client *c, AA::Rank *r)
{
	const auto timer = r->spell_type + pTimerAAStart;
	const auto before_timer = c->GetPTimers().GetRemainingTime(timer);
	const auto before = AABuffState(c);
	c->ActivateAlternateAdvancementAbility(r->id,c->GetID());
	const auto after_timer = c->GetPTimers().GetRemainingTime(timer);
	// ActivateAlternateAdvancementAbility returns void. Record native evidence
	// of acceptance; a request alone is never counted as a successful activation.
	const bool started = (!before_timer && after_timer > 0)
		|| (!before.at("casting").get<uint16>() && c->CastingSpellID() == r->spell);
	return {{"ms",Timer::GetCurrentTime()},{"rank_id",r->id},{"ability_id",r->base_ability->id},
		{"spell",r->spell},{"cooldown_group",r->spell_type},
		{"spell_minimum_level",GetSpellMinimumLevel(r->spell)},
		{"buff_level_restrictions",RuleB(Spells,BuffLevelRestrictions)},
		{"target_type",spells[r->spell].target_type},{"raw_duration",spells[r->spell].buff_duration},
		{"duration_formula",spells[r->spell].buff_duration_formula},{"short_buff_box",spells[r->spell].short_buff_box},
		{"effective_recast_seconds",std::max(0,r->recast_time-c->GetAlternateAdvancementCooldownReduction(r))},
		{"timer_before",before_timer},{"timer_after",after_timer},{"started",started},
		{"before",before},{"after",AABuffState(c)}};
}

json NightcapBalanceAAProbe(Client *c, const json &input)
{
	const int duration = input.at("duration_ms");
	const int percent = input.value("initial_hp_percent",40);
	if (!virtual_clock || !c->Connected() || duration < 1000 || duration > 300000
		|| duration % 50 || percent < 1 || percent > 100) {
		throw std::runtime_error("Invalid AA probe runtime/duration/resources");
	}
	int previous_ms = 0;
	for (const auto &action : input.at("actions")) {
		const int ms = action.at("ms");
		if (ms <= previous_ms || ms > duration || ms % 50) { throw std::runtime_error("Invalid AA action time"); }
		if (action.contains("rank_id") == action.contains("spell_id")) {
			throw std::runtime_error("A probe action must select exactly one AA or preparation spell");
		}
		if (action.contains("rank_id")) {
			ValidateActiveRank(c,action.at("rank_id"));
		} else {
			const auto id = action.at("spell_id").get<uint16>();
			bool eligible = false;
			if (IsValidSpell(id)) {
				for (auto held : c->GetMulticlassList()) { eligible |= spells[id].classes[held-1] <= c->GetLevel(); }
			}
			if (!eligible || !IsBeneficialSpell(id) || !IsBuffSpell(id)) {
				throw std::runtime_error("Ineligible preparation spell in duration control");
			}
		}
		previous_ms = ms;
	}
	c->SetName("BalanceAAProbe"); c->ChangeSize(6,true); c->SetPosition(0,0,0);
	streams.at(c)->capture_messages = true;
	entity_list.AddClient(c);
	is_zone_loaded = true;
	c->SetHP(c->GetMaxHP()*percent/100); c->Mob::SetMana(c->GetMaxMana());
	json trace = json::array(), actions = json::array();
	auto sample = [&]() { auto state = AABuffState(c); state["ms"] = Timer::GetCurrentTime(); trace.push_back(state); };
	size_t next = 0;
	sample();
	for (int ms = 50; ms <= duration && terminal.empty(); ms += 50) {
		Advance(50);
		if (!c->Process()) { throw std::runtime_error("AA probe client processing stopped"); }
		if (!terminal.empty()) { sample(); break; }
		if (next < input.at("actions").size() && input.at("actions")[next].at("ms") == ms) {
			const auto &action = input.at("actions")[next++];
			if (action.contains("rank_id")) {
				actions.push_back(AttemptAA(c,ValidateActiveRank(c,action.at("rank_id"))));
			} else {
				const auto id = action.at("spell_id").get<uint16>();
				const auto before = AABuffState(c);
				c->GetPP().mem_spells[0] = id;
				const bool accepted = c->CastSpell(id,c->GetID(),static_cast<EQ::spells::CastingSlot>(0));
				actions.push_back({{"ms",ms},{"spell",id},{"started",accepted},{"before",before},{"after",AABuffState(c)}});
			}
			sample();
		} else if (ms % 500 == 0 || ms == duration) { sample(); }
	}
	return {{"actions",actions},{"trace",trace},{"events",streams.at(c)->events},
		{"result",terminal.count(c) ? "player_death" : "duration"},
		{"scope","Native self-target AA activation/buff/cooldown lifecycle; no opponent, no resource resets after start"}};
}

class BalanceNPC : public NPC {
public:
	using NPC::NPC;
	bool capture_damage = false;
	uint32 damage_depth = 0;
	json damage_ledger = json::array();
	bool Death(Mob *, int64, uint16, EQ::skills::SkillType, KilledByTypes, bool) override
	{ return NightcapBalanceRecordDeath(this); }
	void Damage(Mob *from, int64 damage, uint16 spell, EQ::skills::SkillType skill,
		bool avoidable, int8 slot, bool tick, eSpecialAttacks special) override
	{
		if (!NightcapBalanceIsTerminal(this)) {
			const auto before = GetHP();
			const auto source_id = from ? from->GetID() : 0;
			const auto depth = damage_depth;
			if (capture_damage) { ++damage_depth; }
			NPC::Damage(from,damage,spell,skill,avoidable,slot,tick,special);
			if (capture_damage) {
				--damage_depth;
				if (damage_ledger.size() >= 50000) { throw std::runtime_error("Native damage ledger limit exceeded"); }
				damage_ledger.push_back({{"ms",Timer::GetCurrentTime()},{"source",source_id},
					{"spell",spell},{"requested",damage},{"hp_before",before},{"hp_after",GetHP()},{"depth",depth}});
			}
		}
	}
};

// Explicit player movement policy. NPC navigation commands require AI control,
// which would change client combat/casting. Submit ordinary bounded position
// packets instead, using native pathfinding and native resolved movement speed.
class BalanceMeleeReturn {
	IPathfinder::IPath route;
	uint32 next_path_ms = 0;
	uint16 sequence = 0;
	uint32 next_history_ms = 0;
	bool moving = false;
	bool pending_move = false;
public:
	json events = json::array();
	uint32 failed_paths = 0;
	uint32 history_packets = 0;
	bool Step(Client *c, NPC *npc, BalanceStream *stream, uint32 pulse_ms, float approach_range = 0, uint16 heal_spell = 9)
	{
		const bool controlled = c->IsAIControlled() || c->IsFeared() || c->IsStunned() || c->IsMezzed();
		const bool healing = c->GetHPRatio() < 55 && c->GetMana() >= spells[heal_spell].mana;
		const int speed = c->GetRunspeed();
		const auto from = glm::vec3(c->GetPosition());
		const bool in_range = (approach_range > 0 ? glm::distance(from,glm::vec3(npc->GetPosition())) <= approach_range : c->CombatRange(npc)) && c->CheckLosFN(npc);
		if (controlled || c->IsCasting() || speed <= 0 || healing || in_range) {
			route.clear();
			if (moving && !controlled) { Submit(c,stream,from,0); }
			moving = false;
			return false;
		}
		const auto now = Timer::GetCurrentTime();
		if (route.empty() || now >= next_path_ms) {
			if (now < next_path_ms && route.empty()) { return false; }
			PathfinderOptions options;
			options.flags = PathingNotDisabled & ~PathingZoneLine & ~PathingPortal;
			options.step_size = RuleR(Pathing,NavmeshStepSize);
			options.offset = c->GetZOffset();
			bool partial = false, stuck = false;
			route = zone->pathing->FindPath(from,glm::vec3(npc->GetPosition()),partial,stuck,options);
			next_path_ms = now + 500;
			if (partial || stuck || route.empty() || std::any_of(route.begin(),route.end(),[](const auto &n) { return n.teleport; })) {
				route.clear(); ++failed_paths;
				if (moving) { Submit(c,stream,from,0); moving = false; }
				return false;
			}
		}
		while (!route.empty() && glm::distance(from,route.front().pos) < 0.1f) { route.pop_front(); }
		if (route.empty()) {
			if (moving) { Submit(c,stream,from,0); moving = false; }
			return false;
		}
		const auto waypoint = route.front().pos;
		const float distance = glm::distance(from,waypoint);
		// Conservative NPC-ground-motion conversion; client speed parity remains QA.
		const float limit = pulse_ms / 1000.0f * speed * 0.4f * 1.45f;
		const auto to = from + (waypoint-from) * std::min(1.0f,limit/distance);
		if (!std::isfinite(distance) || !std::isfinite(limit) || !zone->zonemap->CheckLoS(from,to)) {
			route.clear(); ++failed_paths;
			if (moving) { Submit(c,stream,from,0); moving = false; }
			return false;
		}
		events.push_back({{"ms",now},{"from",{from.x,from.y,from.z}},
			{"to",{to.x,to.y,to.z}},{"speed",speed},{"limit",limit},
			{"casting",c->IsCasting()},{"controlled",controlled},{"in_range",in_range}});
		Submit(c,stream,to,speed);
		pending_move = true;
		moving = true;
		return true;
	}
	void Confirm(Client *c)
	{
		if (!pending_move) { return; }
		auto &event = events.back();
		event["actual"] = {c->GetX(),c->GetY(),c->GetZ()};
		event["accepted"] = event["actual"] == event["to"];
		if (event["accepted"] == false) { event["controlled_after"] = c->IsAIControlled(); }
		if (event["accepted"] == false && !c->IsAIControlled()) {
			throw std::runtime_error("Ordinary client position packet was not applied");
		}
		pending_move = false;
	}
private:
	void Submit(Client *c, BalanceStream *stream, const glm::vec3 &to, int speed)
	{
		if (Timer::GetCurrentTime() >= next_history_ms) {
			auto *history = new EQApplicationPacket(OP_FloatListThing,sizeof(UpdateMovementEntry));
			auto *entry = reinterpret_cast<UpdateMovementEntry *>(history->pBuffer);
			entry->X = c->GetX(); entry->Y = c->GetY(); entry->Z = c->GetZ();
			// A position sample using the engine's non-exempting history type.
			// No teleport/zone-line entry or anti-cheat exemption is fabricated.
			entry->type = UpdateMovementType::Unknown0x5;
			entry->timestamp = Timer::GetCurrentTime();
			stream->incoming.push_back(history);
			next_history_ms = Timer::GetCurrentTime() + 10000;
			++history_packets;
		}
		auto *packet = new EQApplicationPacket(OP_ClientUpdate,sizeof(PlayerPositionUpdateClient_Struct));
		auto *p = reinterpret_cast<PlayerPositionUpdateClient_Struct *>(packet->pBuffer);
		p->sequence = ++sequence;
		p->spawn_id = c->GetID();
		p->x_pos = to.x; p->y_pos = to.y; p->z_pos = to.z;
		p->heading = FloatToEQ12(speed ? c->CalculateHeadingToTarget(to.x,to.y) : c->GetHeading());
		p->animation = speed;
		stream->incoming.push_back(packet);
	}
};

class BalanceAAActions {
	std::vector<AA::Rank *> ranks;
	std::set<int> attempted;
public:
	json events = json::array();
	BalanceAAActions(Client *c, const std::string &policy)
	{
		if (policy.empty()) { return; }
		if (policy != "burst" && policy != "burst_regeneration" && policy != "burst_tenacity") {
			throw std::runtime_error("Unknown activated-AA policy");
		}
		std::vector<int> abilities = {515,308};
		if (policy == "burst_regeneration") { abilities.push_back(38); }
		if (policy == "burst_tenacity") { abilities.push_back(300); }
		for (int id : abilities) {
			const auto owned = c->GetAAByAAID(id);
			if (!owned) { continue; }
			auto pair = zone->GetAlternateAdvancementAbilityAndRank(id,owned);
			if (!pair.second) { throw std::runtime_error("Owned active AA has no rank"); }
			ranks.push_back(ValidateActiveRank(c,pair.second->id));
		}
	}
	bool Step(Client *c, uint32 &next_request)
	{
		for (auto *r : ranks) {
			if (attempted.count(r->id)) { continue; }
			const bool sustain = r->base_ability->id == 38 || r->base_ability->id == 300;
			if (sustain && c->GetHPRatio() >= 80) { continue; }
			attempted.insert(r->id);
			events.push_back(AttemptAA(c,r));
			next_request = Timer::GetCurrentTime() + 250;
			if (events.back().at("started") == true && !c->IsCasting()) {
				next_request = Timer::GetCurrentTime() + std::max<uint32>(250,spells[r->spell].recovery_time);
			}
			return true;
		}
		return false;
	}
};

static json PetCombat(Client *c, const json &input)
{
	const int npc_id = input.at("npc_id"), duration = input.at("duration_ms");
	const bool commands_only = input.value("commands_only",false);
	const auto owner_policy = input.value("owner_policy",std::string("none"));
	const bool support = owner_policy == "pet_support";
	capture_terminal = input.value("capture_terminal",false);
	if (capture_terminal && !support) { throw std::runtime_error("Terminal evidence requires pet support combat"); }
	const auto approach_policy = input.value("approach_policy",std::string("ranged80"));
	const bool native_spell_range = approach_policy == "native_spell_range";
	if ((approach_policy != "ranged80" && !native_spell_range) || (native_spell_range && !support)) {
		throw std::runtime_error("Invalid pet approach policy");
	}
	if ((owner_policy != "none" && !support) || (support && commands_only)) { throw std::runtime_error("Invalid pet owner policy"); }
	if ((npc_id != 32040 && npc_id != 73057) || duration < 50 || duration > (commands_only ? 1000 : 900000)) {
		throw std::runtime_error("Unsupported pet combat target/duration");
	}
	const auto p = input.at("npc_position").get<std::vector<float>>();
	const auto *type = content_db.LoadNPCTypesData(npc_id);
	if (!type) { throw std::runtime_error("Missing pet combat NPC"); }
	auto *boss = new BalanceNPC(type,nullptr,glm::vec4(p[0],p[1],p[2],p[3]),GravityBehavior::Water);
	boss->capture_damage = !commands_only;
	const bool range_immune = boss->GetSpecialAbility(SpecialAbility::CastingFromRangeImmunity);
	const int approach_range = native_spell_range && range_immune ? 0 : 80;
	std::vector<uint16> pet_ids;
	for (const auto &entry : entity_list.GetNPCList()) {
		if (entry.second->GetOwnerID() == c->GetID()) { pet_ids.push_back(entry.first); }
	}
	std::sort(pet_ids.begin(),pet_ids.end());
	if (pet_ids.empty()) { throw std::runtime_error("Pet combat requires an owned pet"); }
	entity_list.AddNPC(boss,false);
	c->SetTarget(boss);
	auto *stream = streams.at(c);
	stream->events.clear();
	const uint32 start = Timer::GetCurrentTime();
	const auto &commands = input.at("commands");
	if (!commands.is_array() || commands.empty() || commands.size() > 20) { throw std::runtime_error("Invalid pet command schedule"); }
	int previous_ms = -1;
	for (const auto &cmd : commands) {
		const int ms = cmd.at("ms"), command = cmd.at("command");
		if (ms < 0 || ms <= previous_ms || ms >= duration || (command != PET_ATTACK && command != PET_QATTACK && command != PET_BACKOFF && command != PET_FOLLOWME && command != PET_TAUNT_ON)) {
			throw std::runtime_error("Unsupported pet command or unordered schedule");
		}
		previous_ms = ms;
	}
	auto state = [&]() {
		json pets = json::array();
		for (const auto id : pet_ids) {
			auto *pet = entity_list.GetMob(id);
			if (!pet) { pets.push_back({{"id",id},{"present",false}}); continue; }
			pets.push_back({{"id",id},{"present",true},{"owner_id",pet->GetOwnerID()},
				{"hp",pet->GetHP()},{"mana",pet->GetMana()},{"engaged",pet->IsEngaged()},
				{"target",pet->GetTarget() ? pet->GetTarget()->GetID() : 0},
				{"hate",pet->GetHateAmount(boss)},{"melee_range",pet->CombatRange(boss)},
				{"los",pet->CheckLosFN(boss)},{"position",{pet->GetX(),pet->GetY(),pet->GetZ()}}});
		}
		json result = {{"ms",Timer::GetCurrentTime()-start},{"player",AABuffState(c)},
			{"player_position",{c->GetX(),c->GetY(),c->GetZ()}},{"pets",pets},
			{"boss_hp",boss->GetHP()},{"boss_mana",boss->GetMana()},
			{"boss_target",boss->GetTarget() ? boss->GetTarget()->GetID() : 0},
			{"boss_position",{boss->GetX(),boss->GetY(),boss->GetZ()}}};
		if (support) {
			json buffs = json::array();
			for (int slot = 0; slot < boss->GetMaxTotalSlots(); ++slot) {
				const auto &b = boss->GetBuffs()[slot];
				if (IsValidSpell(b.spellid)) { buffs.push_back({{"spell",b.spellid},{"ticks",b.ticsremaining}}); }
			}
			result["boss_buffs"] = buffs; result["boss_haste"] = boss->GetHaste();
			result["player"]["sitting"] = c->IsSitting(); result["player"]["max_mana"] = c->GetMaxMana();
			if (native_spell_range) {
				result["owner_combat_range"] = c->CombatRange(boss);
				result["owner_los"] = c->CheckLosFN(boss);
			}
		}
		return result;
	};
	json trace = json::array(), requests = json::array();
	json owner_actions = json::array();
	BalanceMeleeReturn movement;
	std::unique_ptr<BalanceAAActions> aa_actions;
	// Choose eight gems before combat. Match cold/fire offense to the boss,
	// and reserve a gem for native resistance reduction before slow/DoTs.
	const std::vector<uint16> gems = {15,507,112,436,static_cast<uint16>(npc_id == 32040 ? 32 : 6),
		static_cast<uint16>(npc_id == 32040 ? 510 : 120),754,447};
	std::map<uint16,uint32> retry;
	uint32 next_request = 0;
	uint16 owner_cast = 0;
	if (support) {
		for (size_t gem = 0; gem < gems.size(); ++gem) {
			if (!IsValidSpell(gems[gem]) || c->GetSpellMinLevel(gems[gem]) > c->GetLevel()) { throw std::runtime_error("Ineligible pet support gem"); }
			c->GetPP().mem_spells[gem] = gems[gem];
		}
		aa_actions = std::make_unique<BalanceAAActions>(c,"burst");
	}
	auto posture = [&](bool sitting) {
		if (c->IsSitting() == sitting) { return true; }
		auto *packet = new EQApplicationPacket(OP_SpawnAppearance,sizeof(SpawnAppearance_Struct));
		auto *a = reinterpret_cast<SpawnAppearance_Struct *>(packet->pBuffer);
		a->spawn_id = c->GetID(); a->type = AppearanceType::Animation;
		a->parameter = sitting ? Animation::Sitting : Animation::Standing;
		stream->incoming.push_back(packet); return false;
	};
	auto has_buff = [](Mob *target, uint16 spell_id) {
		for (int slot = 0; slot < target->GetMaxTotalSlots(); ++slot) {
			if (target->GetBuffs()[slot].spellid == spell_id) { return true; }
		}
		return false;
	};
	auto finish_owner_cast = [&]() {
		auto &action = owner_actions.back();
		auto *target = entity_list.GetMob(action.at("target").get<uint16>());
		action["ended_ms"] = Timer::GetCurrentTime()-start;
		action["owner_hp_after"] = c->GetHP(); action["owner_mana_after"] = c->GetMana();
		action["target_hp_after"] = target ? json(target->GetHP()) : json(nullptr);
		if (target) { action["buff_present_after"] = has_buff(target,action.at("spell").get<uint16>()); }
	};
	trace.push_back(state());
	size_t command_index = 0;
	for (int ms = 0; ms < duration && terminal.empty(); ms += 50) {
		json before;
		bool requested = false;
		if (command_index < commands.size() && commands[command_index].at("ms").get<int>() <= ms) {
			before = state(); requested = true;
			auto *packet = new EQApplicationPacket(OP_PetCommands,sizeof(PetCommand_Struct));
			auto *command = reinterpret_cast<PetCommand_Struct *>(packet->pBuffer);
			command->command = commands[command_index].at("command"); command->target = boss->GetID();
			stream->incoming.push_back(packet);
		}
		Advance(50);
		bool moving = false;
		if (support) {
			const auto now = Timer::GetCurrentTime();
			const bool controlled = c->IsAIControlled() || c->IsFeared() || c->IsStunned() || c->IsMezzed();
			const bool in_range = approach_range == 0 ? c->CombatRange(boss) :
				glm::distance(glm::vec3(c->GetPosition()),glm::vec3(boss->GetPosition())) <= approach_range;
			const bool needs_return = !in_range || !c->CheckLosFN(boss);
			if (!controlled && !c->IsCasting() && needs_return && c->IsSitting()) { posture(false); }
			else { moving = movement.Step(c,boss,stream,50,approach_range,15); }
			if (!moving && !controlled && !c->IsCasting() && now >= next_request) {
				Mob *target = boss;
				uint16 selected = 0;
				std::string reason;
				const double mana_ratio = c->GetMana()*100.0/c->GetMaxMana();
				if (c->GetHPRatio() < 55 && c->GetMana() >= spells[15].mana) {
					selected = 15; target = c; reason = "self_heal";
				} else if (!needs_return) {
					Mob *lowest = nullptr;
					for (auto id : pet_ids) {
						auto *pet = entity_list.GetMob(id);
						if (pet && pet->GetHP() > 0 && pet->GetOwnerID() == c->GetID() && pet->GetHPRatio() < 65
							&& (!lowest || pet->GetHPRatio() < lowest->GetHPRatio())) { lowest = pet; }
					}
					if (lowest && c->GetMana() >= spells[15].mana) { selected = 15; target = lowest; reason = "pet_heal"; }
					else if (!has_buff(boss,112) && now >= retry[112] && c->GetMana() >= spells[112].mana) { selected = 112; reason = "resist_debuff"; }
					else if (!has_buff(boss,507) && now >= retry[507] && c->GetMana() >= spells[507].mana) { selected = 507; reason = "slow"; }
					else if (mana_ratio < 45 && c->GetHPRatio() > 65) { selected = 754; target = c; reason = "cannibalize"; }
					else {
						for (uint16 dot : {gems[4],gems[3]}) {
							if (!has_buff(boss,dot) && now >= retry[dot] && c->GetMana() >= spells[dot].mana + 2*spells[15].mana) { selected = dot; reason = "dot"; break; }
						}
						if (!selected && mana_ratio > 60) { selected = c->GetHPRatio() < 85 ? 447 : gems[5]; reason = "filler"; }
					}
				}
				if (selected && posture(false)) {
					auto *timer = c->GetPTimers().Get(pTimerSpellStart+selected);
					if ((!timer || timer->GetRemainingTime() == 0) &&
						((selected == 15 || selected == 754 || selected == 112 || selected == 507) || !aa_actions->Step(c,next_request))) {
						const auto gem = std::find(gems.begin(),gems.end(),selected)-gems.begin();
						const auto hp = c->GetHP(), target_hp = target->GetHP();
						const auto mana = c->GetMana();
						const bool accepted = c->CastSpell(selected,target->GetID(),static_cast<EQ::spells::CastingSlot>(gem));
						owner_actions.push_back({{"ms",now-start},{"spell",selected},{"gem",gem},{"target",target->GetID()},
							{"reason",reason},{"accepted",accepted},{"owner_hp_before",hp},{"owner_mana_before",mana},{"target_hp_before",target_hp}});
						if (native_spell_range) {
							owner_actions.back()["owner_combat_range"] = c->CombatRange(boss);
							owner_actions.back()["owner_los"] = c->CheckLosFN(boss);
						}
						// Repeated resisted debuffs must not starve the rest of the rotation.
						retry[selected] = now+30000; next_request = now+250;
						owner_cast = c->CastingSpellID();
						if (accepted && !owner_cast) { finish_owner_cast(); next_request = now+std::max<uint32>(250,spells[selected].recovery_time); }
					}
				} else if (!selected && !needs_return && mana_ratio < 75 && boss->GetTarget() != c) { posture(true); }
			}
		}
		if (commands_only) {
			if (!c->Process()) { throw std::runtime_error("Pet command client stopped"); }
		} else {
			entity_list.MobProcess();
			MobMovementManager::Get().Process();
		}
		if (support) {
			movement.Confirm(c);
			if (owner_cast && !c->IsCasting()) {
				finish_owner_cast(); next_request = Timer::GetCurrentTime()+std::max<uint32>(250,spells[owner_cast].recovery_time); owner_cast = 0;
			}
		}
		if (requested) { requests.push_back({{"input",commands[command_index++]},{"before",before},{"after",state()}}); }
		if ((ms+50) % 500 == 0 || !terminal.empty() || ms+50 >= duration) { trace.push_back(state()); }
	}
	for (auto &event : stream->events) { event["ms"] = event.at("ms").get<uint32>()-start; }
	json result = {{"input",input},{"boss_id",boss->GetID()},{"player_id",c->GetID()},{"pet_ids",pet_ids},
		{"trace",trace},{"commands",requests},{"events",stream->events},
		{"result",terminal.count(boss) ? "boss_death" : terminal.count(c) ? "player_death" : "timeout"},
		{"scope",commands_only ? "Native command boundary only; NPC AI paused to distinguish immediate command damage from attack orders" : "Native pet-only combat and movement; owner issues commands but does not yet cast, heal, kite or use activated AAs"}};
	if (capture_terminal) {
		for (auto &event : terminal_events) { event["ms"] = event.at("ms").get<uint32>()-start; }
		result["terminal_events"] = terminal_events;
		// The mock death adapter ends the fight without a real corpse transition.
		// MobProcess can finish a heal later in this same pulse. The first native
		// death callback, not post-pulse HP or boss-first precedence, ends combat.
		if (!terminal_events.empty()) {
			const auto first = terminal_events.front().at("entity_id").get<uint16>();
			if (first != c->GetID() && first != boss->GetID()) { throw std::runtime_error("Unexpected terminal actor"); }
			result["result"] = first == c->GetID() ? "player_death" : "boss_death";
		}
	}
	if (!commands_only) {
		for (auto &event : boss->damage_ledger) { event["ms"] = event.at("ms").get<uint32>()-start; }
		result["damage_ledger"] = boss->damage_ledger;
	}
	if (support) {
		for (auto &event : movement.events) { event["ms"] = event.at("ms").get<uint32>()-start; }
		for (auto &event : aa_actions->events) { event["ms"] = event.at("ms").get<uint32>()-start; }
		result["owner_actions"] = owner_actions; result["gems"] = gems;
		result["movement"] = {{"events",movement.events},{"failed_paths",movement.failed_paths},{"history_packets",movement.history_packets},{"approach_range",approach_range}};
		result["activated_aa"] = aa_actions->events;
		result["scope"] = "Native pet support: eight fixed gems, self/pet healing, slow, DoTs, Cannibalize II, filler nukes/taps, purchased burst AA, native sitting and bounded return to80 units; no pet resummoning or continuous kiting";
		if (native_spell_range) {
			result["range_immunity"] = range_immune;
			result["scope"] = "Native pet support with the captured ranged-spell immunity respected: approach native melee range for belly casters, otherwise80 units; eight fixed gems, native recovery/movement, no pet resummoning or continuous kiting";
		}
	}
	return result;
}


static json PreparationState(Client *c)
{
	auto state = AABuffState(c);
	state["max_mana"] = c->GetMaxMana();
	state["mr"] = c->GetMR(); state["fr"] = c->GetFR(); state["cr"] = c->GetCR();
	state["sitting"] = c->IsSitting();
	return state;
}

// Requests normal combat buttons through Client::Process. The native handler owns
// class/skill/range checks, damage, Master Wu and cooldown calculation.
class BalanceMonkActions {
	std::map<int,uint32> next_request;
	bool pending = false;
public:
	json events = json::array();
	void Queue(Client *c, NPC *npc, BalanceStream *stream)
	{
		if (c->IsCasting() || c->IsAIControlled() || c->IsFeared() || c->IsStunned() || c->IsMezzed()
			|| (c->GetHPRatio() < 55 && c->GetMana() >= spells[9].mana)
			|| !c->CombatRange(npc) || !c->CheckLosFN(npc)) { return; }
		for (auto skill : {EQ::skills::SkillFlyingKick,EQ::skills::SkillTigerClaw}) {
			const auto timer_id = skill == EQ::skills::SkillTigerClaw ? pTimerCombatAbility2 : pTimerCombatAbility;
			auto *timer = c->GetPTimers().Get(timer_id);
			if (!c->GetSkill(skill) || Timer::GetCurrentTime() < next_request[skill]
				|| (timer && timer->GetRemainingTime())) { continue; }
			auto *packet = new EQApplicationPacket(OP_CombatAbility,sizeof(CombatAbility_Struct));
			auto *action = reinterpret_cast<CombatAbility_Struct *>(packet->pBuffer);
			action->m_target = npc->GetID(); action->m_atk = 100; action->m_skill = skill;
			stream->incoming.push_back(packet);
			events.push_back({{"ms",Timer::GetCurrentTime()},{"skill",skill},{"timer_id",timer_id},
				{"timer_before",timer ? timer->GetRemainingTime() : 0},{"skill_value",c->GetSkill(skill)},
				{"target",npc->GetID()},{"npc_hp_before",npc->GetHP()},{"player_hp_before",c->GetHP()},
				{"player_mana_before",c->GetMana()}});
			next_request[skill] = Timer::GetCurrentTime()+250;
			pending = true;
			return; // One button per pulse; separate native RoF2 cooldown groups.
		}
	}
	void Confirm(Client *c, NPC *npc)
	{
		if (!pending) { return; }
		auto *timer = c->GetPTimers().Get(events.back().at("timer_id").get<int>());
		events.back()["timer_after"] = timer ? timer->GetRemainingTime() : 0;
		events.back()["npc_hp_after"] = npc->GetHP();
		events.back()["player_hp_after"] = c->GetHP();
		events.back()["player_mana_after"] = c->GetMana();
		pending = false;
	}
};

static json PrepareEncounter(Client *c, const json &input)
{
	const auto ids = input.at("spell_ids").get<std::vector<int>>();
	const int maximum = input.value("max_duration_ms",900000);
	const bool recover = input.value("recover",true);
	if (ids.size() > 16 || std::set<int>(ids.begin(),ids.end()).size() != ids.size()
		|| maximum < 1000 || maximum > 900000 || maximum % 50) {
		throw std::runtime_error("Invalid preparation limits or duplicate spell");
	}
	for (int id : ids) {
		bool eligible = false;
		if (id > 0 && id < 65535 && IsValidSpell(id)) {
			for (auto held : c->GetMulticlassList()) {
				const int level = spells[id].classes[held-1];
				eligible |= level > 0 && level <= c->GetLevel();
			}
		}
		if (!eligible || !IsBeneficialSpell(id) || !IsBuffSpell(id)) {
			throw std::runtime_error("Ineligible preparation spell " + std::to_string(id));
		}
	}
	auto *stream = streams.at(c);
	stream->capture_messages = true;
	json trace = json::array(), actions = json::array();
	auto posture = [&](bool sitting) {
		if (c->IsSitting() == sitting) { return true; }
		auto *packet = new EQApplicationPacket(OP_SpawnAppearance,sizeof(SpawnAppearance_Struct));
		auto *appearance = reinterpret_cast<SpawnAppearance_Struct *>(packet->pBuffer);
		appearance->spawn_id = c->GetID(); appearance->type = AppearanceType::Animation;
		appearance->parameter = sitting ? Animation::Sitting : Animation::Standing;
		stream->incoming.push_back(packet);
		return false; // Confirm the native client state after the next Process call.
	};
	auto sample = [&]() { auto state = PreparationState(c); state["ms"] = Timer::GetCurrentTime(); trace.push_back(state); };
	sample();
	size_t next = 0;
	uint32 ready = 0;
	uint16 casting = 0;
	int retries = 0;
	bool complete = false;
	for (int ms = 50; ms <= maximum; ms += 50) {
		Advance(50);
		if (!c->Process() || !terminal.empty()) { throw std::runtime_error("Preparation did not survive native processing"); }
		if (casting && !c->IsCasting()) {
			actions.back()["completed_ms"] = ms;
			actions.back()["completed_state"] = PreparationState(c);
			ready = ms + std::max<uint32>(250,spells[casting].recovery_time);
			casting = 0;
		}
		if (!c->IsCasting() && ms >= ready) {
			if (next < ids.size()) {
				if (!posture(false)) { continue; }
				const int id = ids[next];
				const auto before = PreparationState(c);
				c->GetPP().mem_spells[0] = id;
				const bool accepted = c->CastSpell(id,c->GetID(),static_cast<EQ::spells::CastingSlot>(0));
				actions.push_back({{"ms",ms},{"spell",id},{"accepted",accepted},{"before",before},{"after",PreparationState(c)}});
				ready = ms + 250;
				if (accepted) {
					casting = c->CastingSpellID(); ++next; retries = 0;
					if (!casting) { actions.back()["completed_ms"] = ms; actions.back()["completed_state"] = PreparationState(c); }
				} else if (++retries >= 3) { throw std::runtime_error("Preparation spell failed three native attempts"); }
			} else if (!recover || (c->GetHP() == c->GetMaxHP() && c->GetMana() == c->GetMaxMana())) {
				if (!posture(false)) { continue; }
				sample(); complete = true; break;
			} else { posture(true); }
		}
		if (ms % 500 == 0) { sample(); }
	}
	if (!complete) { throw std::runtime_error("Preparation exceeded its native recovery time budget"); }
	const json result = {{"input",input},{"actions",actions},{"trace",trace},{"events",stream->events},
		{"elapsed_ms",Timer::GetCurrentTime()},{"final_state",PreparationState(c)},
		{"scope","Native self-buff casts followed by optional sitting recovery; no resource resets or opponent during preparation"}};
	stream->events.clear();
	return result;
}

json NightcapBalanceEncounter(Client *c, const json &input)
{
	const int npc_id = input.at("npc_id").get<int>();
	const int duration = input.value("duration_ms",120000);
	const bool return_to_melee = input.value("return_to_melee",false);
	const std::string combat_policy = input.value("combat_policy",std::string("caster_heal"));
	const bool melee_heal = combat_policy == "melee_heal";
	const bool melee_specials = input.value("melee_specials",true);
	if (combat_policy != "caster_heal" && !melee_heal) { throw std::runtime_error("Unknown native combat policy"); }
	const std::string active_policy = input.value("active_aa_policy",std::string());
	BalanceAAActions aa_actions(c,active_policy);
	if ((npc_id != 32040 && npc_id != 73057) || duration < 1000 || duration > 900000
		|| !virtual_clock || !c->Connected() || !c->ClientFinishedLoading()) {
		throw std::runtime_error("Unsupported encounter or incomplete runtime client");
	}
	zone->ReloadMaps();
	if (!zone->zonemap || !zone->pathing || !zone->watermap) { throw std::runtime_error("All three native maps are required"); }
	// The native hate-list selector refuses targets during zone startup/shutdown.
	is_zone_loaded = true;
	const auto *type = content_db.LoadNPCTypesData(npc_id);
	if (!type) { throw std::runtime_error("Missing encounter NPC"); }
	const auto p = input.at("npc_position").get<std::vector<float>>();
	if (p.size() != 4 || !std::all_of(p.begin(),p.end(),[](float v) { return std::isfinite(v); })) {
		throw std::runtime_error("Invalid encounter position");
	}
	// Preserve construction order and native RNG behavior when preparation is absent.
	BalanceNPC *npc = input.contains("preparation") ? nullptr : new BalanceNPC(type,nullptr,glm::vec4(p[0],p[1],p[2],p[3]),GravityBehavior::Water);
	c->SetName("BalanceFighter"); c->ChangeSize(6,true);
	c->SetPosition(p[0]+10,p[1],p[2]);
	c->SetHeading(c->CalculateHeadingToTarget(p[0],p[1]));
	c->SetHP(c->GetMaxHP()); c->Mob::SetMana(c->GetMaxMana());
	entity_list.AddClient(c);
	json preparation;
	if (input.contains("preparation")) {
		preparation = PrepareEncounter(c,input.at("preparation"));
		npc = new BalanceNPC(type,nullptr,glm::vec4(p[0],p[1],p[2],p[3]),GravityBehavior::Water);
	}
	const uint32 combat_start = Timer::GetCurrentTime();
	entity_list.AddNPC(npc,false);
	if (!c->CheckLosFN(npc) || !c->CombatRange(npc)) { throw std::runtime_error("Initial position fails native LOS/melee range"); }
	c->SetTarget(npc);
	npc->AddToHateList(c,1);
	const json initial_state = {{"zone_loaded",zone->IsLoaded()},{"npc_ai",npc->IsAIControlled()},{"npc_engaged",npc->IsEngaged()},
		{"player_zoning",c->IsZoning()},{"player_destroying",c->IsDestroying()},
		{"player_dead",c->IsDead()},{"can_combat",zone->CanDoCombat()},
		{"npc_can_attack",npc->IsAttackAllowed(c)},{"player_can_attack",c->IsAttackAllowed(npc)},
		{"npc_has_spells",npc->AI_HasSpells()},{"npc_hate_target",npc->GetHateTop() ? npc->GetHateTop()->GetID() : 0}};
	if (!npc->IsEngaged() || npc->GetHateTop() != c || !npc->IsAttackAllowed(c)) {
		throw std::runtime_error("Native engagement control failed: " + initial_state.dump());
	}
	const uint16 nuke = melee_heal ? 0 : npc_id == 32040 ? 732 : 659;
	const uint16 heal = 9;
	c->GetPP().mem_spells[0] = nuke;
	c->GetPP().mem_spells[1] = heal;
	auto *stream = streams.at(c);
	stream->capture_damage_type = melee_heal;
	stream->capture_messages = !active_policy.empty();
	auto *attack = new EQApplicationPacket(OP_AutoAttack,4);
	attack->pBuffer[0] = 1;
	stream->incoming.push_back(attack);
	json trace = json::array(), attempts = json::array();
	auto sample = [&]() { trace.push_back({{"ms",Timer::GetCurrentTime()},
		{"player_hp",c->GetHP()},{"player_mana",c->GetMana()},{"player_casting",c->CastingSpellID()},
		{"npc_hp",npc->GetHP()},{"npc_mana",npc->GetMana()},{"npc_casting",npc->CastingSpellID()},
		{"feared",c->IsFeared()},{"stunned",c->IsStunned()},
		{"npc_engaged",npc->IsEngaged()},{"npc_target",npc->GetTarget() ? npc->GetTarget()->GetID() : 0},
		{"player_autoattack",c->AutoAttackEnabled()},{"player_ai",c->IsAIControlled()},
		{"player_combat",NightcapBalanceClientCombatState(c)},
		{"player_position",{c->GetX(),c->GetY(),c->GetZ()}},
		{"npc_position",{npc->GetX(),npc->GetY(),npc->GetZ()}}});
		if (!active_policy.empty()) { trace.back()["aa_state"] = AABuffState(c); }
	};
	uint32 next_request = 0;
	uint16 prior_cast = 0;
	BalanceMeleeReturn movement;
	BalanceMonkActions monk_actions;
	sample();
	for (uint32 ms = combat_start + 50; ms <= combat_start + duration && terminal.empty(); ms += 50) {
		Advance(50);
		const bool moving = return_to_melee && movement.Step(c,npc,stream,50);
		if (melee_heal && melee_specials && !moving) { monk_actions.Queue(c,npc,stream); }
		if (!c->Process()) { throw std::runtime_error("Client processing stopped before terminal combat result"); }
		if (melee_heal && melee_specials) { monk_actions.Confirm(c,npc); }
		if (return_to_melee) { movement.Confirm(c); }
		if (!terminal.empty()) { sample(); break; }
		if (!npc->Process()) { throw std::runtime_error("NPC processing stopped before terminal combat result"); }
		if (!terminal.empty()) { sample(); break; }
		MobMovementManager::Get().Process();
		if (prior_cast && !c->IsCasting()) {
			// Explicit conservative client recovery policy; native per-spell timers also apply.
			next_request = ms + spells[prior_cast].recovery_time;
		}
		if (!moving && !c->IsCasting() && !c->IsFeared() && !c->IsStunned() && !c->IsMezzed() && ms >= next_request) {
			c->SetHeading(c->CalculateHeadingToTarget(npc->GetX(),npc->GetY()));
			if (!aa_actions.Step(c,next_request)) {
				const uint16 spell = c->GetHPRatio() < 55 ? heal : nuke;
				auto *timer = c->GetPTimers().Get(pTimerSpellStart+spell);
				if (spell && (!timer || timer->GetRemainingTime() == 0) && c->GetMana() >= spells[spell].mana) {
					const bool accepted = c->CastSpell(spell,spell == heal ? c->GetID() : npc->GetID(),
						static_cast<EQ::spells::CastingSlot>(spell == heal ? 1 : 0));
					attempts.push_back({{"ms",ms},{"spell",spell},{"accepted",accepted}});
				}
				next_request = ms + 250;
			}
		}
		prior_cast = c->CastingSpellID();
		if ((ms-combat_start) % 500 == 0) { sample(); }
	}
	json result = {{"npc_id",npc_id},{"player_entity_id",c->GetID()},{"npc_entity_id",npc->GetID()},
		{"initial_state",initial_state},
		{"result",terminal.count(c) ? "player_death" : terminal.count(npc) ? "npc_death" : "timeout"},
		{"elapsed_ms",Timer::GetCurrentTime()},{"trace",trace},{"attempts",attempts},{"events",stream->events},
		{"scope","Native client/NPC combat prototype with maps; fixed nuke/self-heal controller, no buffs or activated AAs, not certified full BiS or balance evidence"}};
	if (return_to_melee) {
		result["movement"] = {{"policy","native mesh, bounded client updates, stop for healing/casting/control"},
			{"events",movement.events},{"failed_paths",movement.failed_paths},{"history_packets",movement.history_packets}};
	}
	if (!active_policy.empty()) {
		result["activated_aa"] = {{"policy",active_policy},{"actions",aa_actions.events},
			{"scope","One request per owned AA: Twincast then Frenzied Devastation; selected sustain below 80% HP. Native rejection/cost/charges/cooldowns retained; no preparation buffs."}};
		result["scope"] = "Native candidate encounter with explicit purchased-AA activation policy; not certified full BiS or final balance evidence";
	}
	if (input.contains("preparation")) {
		// Keep native clocks continuous; only report timestamps become fight-relative.
		auto relative = [combat_start](json &rows) { for (auto &row : rows) { row["ms"] = row.at("ms").get<uint32>() - combat_start; } };
		for (const char *key : {"trace","attempts","events"}) { relative(result[key]); }
		if (return_to_melee) { relative(result["movement"]["events"]); }
		if (!active_policy.empty()) { relative(result["activated_aa"]["actions"]); }
		result["elapsed_ms"] = Timer::GetCurrentTime()-combat_start;
		result["combat_start_ms"] = combat_start;
		result["preparation"] = preparation;
		result["scope"] = "Native preparation and encounter; continuous buff/resource/cooldown state, fight-relative timestamps; candidate gear and fixed combat policy";
		if (!active_policy.empty()) { result["activated_aa"]["scope"] = "Same once-per-fight activation policy after native preparation; shared cooldowns and costs retained"; }
	}
	if (melee_heal) {
		for (auto &event : monk_actions.events) { event["ms"] = event.at("ms").get<uint32>()-combat_start; }
		result["combat_policy"] = combat_policy;
		result["monk_actions"] = {{"enabled",melee_specials},{"requests",monk_actions.events},
			{"policy","Autoattack and native Flying Kick/Tiger Claw buttons, pause for affordable Superior Healing below55%; each button requested at most every250ms and only with its native timer ready"}};
		result["scope"] = "Native WAR/CLR/MNK melee and self-heal controller; packet combat skills, candidate gear and AA purchases; not final balance certification";
	}
	return result;
}
