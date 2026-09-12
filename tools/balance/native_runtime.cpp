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
bool NightcapBalanceIsTerminal(Mob *mob) { return terminal.count(mob); }
bool NightcapBalanceRecordDeath(Mob *mob)
{
	if (!virtual_clock) { throw std::runtime_error("Unexpected death outside runtime mode"); }
	terminal.insert(mob);
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
	bool Death(Mob *, int64, uint16, EQ::skills::SkillType, KilledByTypes, bool) override
	{ return NightcapBalanceRecordDeath(this); }
	void Damage(Mob *from, int64 damage, uint16 spell, EQ::skills::SkillType skill,
		bool avoidable, int8 slot, bool tick, eSpecialAttacks special) override
	{
		if (!NightcapBalanceIsTerminal(this)) { NPC::Damage(from,damage,spell,skill,avoidable,slot,tick,special); }
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
	bool Step(Client *c, NPC *npc, BalanceStream *stream, uint32 pulse_ms)
	{
		const bool controlled = c->IsAIControlled() || c->IsFeared() || c->IsStunned() || c->IsMezzed();
		const bool healing = c->GetHPRatio() < 55 && c->GetMana() >= spells[9].mana;
		const int speed = c->GetRunspeed();
		const auto from = glm::vec3(c->GetPosition());
		const bool in_range = c->CombatRange(npc) && c->CheckLosFN(npc);
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

static json PreparationState(Client *c)
{
	auto state = AABuffState(c);
	state["max_mana"] = c->GetMaxMana();
	state["mr"] = c->GetMR(); state["fr"] = c->GetFR(); state["cr"] = c->GetCR();
	state["sitting"] = c->IsSitting();
	return state;
}

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
	const uint16 nuke = npc_id == 32040 ? 732 : 659;
	const uint16 heal = 9;
	c->GetPP().mem_spells[0] = nuke;
	c->GetPP().mem_spells[1] = heal;
	auto *stream = streams.at(c);
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
	sample();
	for (uint32 ms = combat_start + 50; ms <= combat_start + duration && terminal.empty(); ms += 50) {
		Advance(50);
		const bool moving = return_to_melee && movement.Step(c,npc,stream,50);
		if (!c->Process()) { throw std::runtime_error("Client processing stopped before terminal combat result"); }
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
				if ((!timer || timer->GetRemainingTime() == 0) && c->GetMana() >= spells[spell].mana) {
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
	return result;
}
