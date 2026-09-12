// Isolated native runtime adapter. No sockets, production objects, or headers are modified.
#include "native_runtime.h"
#include "zone/client.h"
#include "zone/entity.h"
#include "zone/npc.h"
#include "zone/zone.h"
#include "zone/mob_movement_manager.h"
#include "common/eq_stream_intf.h"
#include "common/ptimer.h"
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
	uint64_t outgoing = 0;
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
	OpcodeManager *GetOpcodeManager() const override { return nullptr; }
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

json NightcapBalanceEncounter(Client *c, const json &input)
{
	const int npc_id = input.at("npc_id").get<int>();
	const int duration = input.value("duration_ms",120000);
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
	auto *npc = new BalanceNPC(type,nullptr,glm::vec4(p[0],p[1],p[2],p[3]),GravityBehavior::Water);
	c->SetName("BalanceFighter"); c->ChangeSize(6,true);
	c->SetPosition(p[0]+10,p[1],p[2]);
	c->SetHeading(c->CalculateHeadingToTarget(p[0],p[1]));
	c->SetHP(c->GetMaxHP()); c->Mob::SetMana(c->GetMaxMana());
	entity_list.AddClient(c);
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
		{"npc_position",{npc->GetX(),npc->GetY(),npc->GetZ()}}}); };
	uint32 next_request = 0;
	uint16 prior_cast = 0;
	sample();
	for (int ms = 50; ms <= duration && terminal.empty(); ms += 50) {
		Advance(50);
		if (!c->Process()) { throw std::runtime_error("Client processing stopped before terminal combat result"); }
		if (!terminal.empty()) { sample(); break; }
		if (!npc->Process()) { throw std::runtime_error("NPC processing stopped before terminal combat result"); }
		if (!terminal.empty()) { sample(); break; }
		MobMovementManager::Get().Process();
		if (prior_cast && !c->IsCasting()) {
			// Explicit conservative client recovery policy; native per-spell timers also apply.
			next_request = ms + spells[prior_cast].recovery_time;
		}
		if (!c->IsCasting() && !c->IsFeared() && !c->IsStunned() && !c->IsMezzed() && ms >= next_request) {
			c->SetHeading(c->CalculateHeadingToTarget(npc->GetX(),npc->GetY()));
			const uint16 spell = c->GetHPRatio() < 55 ? heal : nuke;
			auto *timer = c->GetPTimers().Get(pTimerSpellStart+spell);
			if ((!timer || timer->GetRemainingTime() == 0) && c->GetMana() >= spells[spell].mana) {
				const bool accepted = c->CastSpell(spell,spell == heal ? c->GetID() : npc->GetID(),
					static_cast<EQ::spells::CastingSlot>(spell == heal ? 1 : 0));
				attempts.push_back({{"ms",ms},{"spell",spell},{"accepted",accepted}});
			}
			next_request = ms + 250;
		}
		prior_cast = c->CastingSpellID();
		if (ms % 500 == 0) { sample(); }
	}
	return {{"npc_id",npc_id},{"player_entity_id",c->GetID()},{"npc_entity_id",npc->GetID()},
		{"initial_state",initial_state},
		{"result",terminal.count(c) ? "player_death" : terminal.count(npc) ? "npc_death" : "timeout"},
		{"elapsed_ms",Timer::GetCurrentTime()},{"trace",trace},{"attempts",attempts},{"events",stream->events},
		{"scope","Native client/NPC combat prototype with maps; fixed nuke/self-heal controller, no buffs or activated AAs, not certified full BiS or balance evidence"}};
}
