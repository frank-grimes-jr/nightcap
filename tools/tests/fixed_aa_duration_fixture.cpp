// Native methods are inserted below. The test substitutes a clock, inventory of
// buffs, persistence repository, stacking verdicts and packet/fade recipients.
#include <cmath>
#include <cstring>
#include <functional>
using int64 = int64_t;
using uint64 = uint64_t;
constexpr int focusSpellDuration = 1, focusSpellDurByTic = 2;
constexpr int SPELL_BATTLE_CRY = 1, SPELL_WAR_CRY = 2, SPELL_BATTLE_CRY_OF_DRAVEL = 3;
constexpr int SPELL_WAR_CRY_OF_DRAVEL = 4, SPELL_BATTLE_CRY_OF_THE_MASTRUQ = 5;
constexpr int SPELL_ANCIENT_CRY_OF_CHAOS = 6, SPELL_BLOODTHIRST = 7;
constexpr int SPELL_MINOR_ILLUSION = 8, SPELL_ILLUSION_TREE = 9;
constexpr int EVENT_SPELL_BLOCKED = 1;
constexpr uint16 rage = 21773, bloodlust = 30736, short_control = 40501, long_control = 40502;
constexpr int long_slots = 3, song_slots = 3, total_slots = 7;
int64 now_ms = 1'800'000'000'000LL;
bool rule_NightcapTHJBehaviors = true;
constexpr bool rule_IllusionsAlwaysPersist = false, rule_UseLiveBlockedMessage = false;
constexpr bool rule_BotsUseLiveBlockedMessage = false;
#define RuleB(group,key) rule_##key
#define LogSpells(...) ((void)0)
#define safe_delete(value) delete value
#define FCMP(a,b) (std::fabs((a)-(b)) < 0.0001)
namespace fmt { template <class... T> std::string format(T&&...) { return {}; } }
namespace Class { constexpr int Bard = 8; }
namespace Chat { constexpr int Red = 1, SpellFailure = 2; }
namespace SpellEffect { constexpr int Charm = 22, Illusion = 58; }
namespace EQ::versions {
constexpr int maskSoFAndLater = 1, maskSoDAndLater = 2;
enum class ClientVersion { UF, RoF2 };
}
namespace EQ::spells {
struct Limits { int LongBuffs = long_slots; } limits;
inline Limits *StaticLookup(EQ::versions::ClientVersion) { return &limits; }
}
bool IsDiscipline(uint16 id) { return !spells[id].mana && (spells[id].endurance_cost || spells[id].endurance_upkeep); }
bool IsAegolismSpell(uint16) { return false; }
bool AegolismStackingIsSymbolSpell(uint16) { return false; }
bool AegolismStackingIsArmorClassSpell(uint16) { return false; }
int CalculateCounters(uint16) { return 0; }
int CalcBuffDuration_formula(int, int, int);
struct Buffs_Struct {
 uint16 spellid = SPELL_UNKNOWN;
 int ticsremaining = 0, casterlevel = 0, casterid = 0, counters = 0, hit_number = 0;
 int caston_x = 0, caston_y = 0, caston_z = 0, melee_rune = 0, magic_rune = 0, dot_rune = 0;
 int ExtraDIChance = 0, RootBreakChance = 0, virus_spread_time = 0, instrument_mod = 0;
 char caster_name[64]{};
 bool UpdateClient = false, client = false, persistant_buff = false;
};
struct Mob;
struct Client;
struct EntityList {
 Mob *GetMob(int) { return nullptr; }
 Mob *GetMobID(int) { return nullptr; }
 Client *GetClientByName(const char*) { return nullptr; }
 template <typename... T> void QueueClientsByTarget(T&&...) {}
} entity_list;
struct Parser { template <typename... T> void EventMob(T&&...) {} } parser, *parse = &parser;
constexpr int OP_Buff = 1;
struct SpellBuffPacket_Struct {
 int entityid = 0, slotid = 0, bufffade = 0;
 struct { int effect_type, level, bard_modifier, spellid, duration, counters, player_id, num_hits; float x, y, z; } buff{};
};
struct EQApplicationPacket {
 SpellBuffPacket_Struct packet;
 void *pBuffer = &packet;
 EQApplicationPacket() = default;
 EQApplicationPacket(int, size_t) {}
};
struct Mob {
 bool player = false, blocked = false;
 int percent = 0, extra = 0, fades = 0, tics = 0, focus_reads = 0;
 struct Bonuses { bool IllusionPersistence = false; } aabonuses, itembonuses, spellbonuses;
 Buffs_Struct buffs[total_slots];
 bool IsClient() const { return player; }
 bool IsNPC() const { return !player; }
 bool IsPetOwnerClient() const { return false; }
 bool IsBot() const { return false; }
 bool IsMerc() const { return false; }
 bool IsPet() const { return false; }
 bool IsAura() const { return false; }
 bool IsActiveBardSong(uint16) const { return false; }
 int GetClass() const { return 1; }
 int GetLevel() const { return 50; }
 int GetID() const { return 1; }
 int GetCasterLevel(uint16) const { return 50; }
 int GetInstrumentMod(uint16) const { return 10; }
 const char *GetName() const { return "Fixture"; }
 const char *GetCleanName() const { return GetName(); }
 Mob *GetOwner() { return nullptr; }
 Mob *GetTarget() { return nullptr; }
 Client *CastToClient();
 int GetMaxTotalSlots() const { return total_slots; }
 int GetMaxBuffSlots() const { return long_slots; }
 int GetCurrentBuffSlots() const { return long_slots; }
 int GetMaxSongSlots() const { return song_slots; }
 int GetCurrentSongSlots() const { return song_slots; }
 int GetCurrentDiscSlots() const { return 1; }
 virtual uint32 GetFirstBuffSlot(bool, bool);
 virtual uint32 GetLastBuffSlot(bool, bool);
 int GetFocusEffect(int type, uint16) { ++focus_reads; return type == focusSpellDuration ? percent : extra; }
 int CheckStackConflict(uint16 existing, int, uint16 incoming, int, Mob*, Mob*, int) {
  return blocked ? -1 : (existing == incoming ? 1 : 0);
 }
 template <typename... T> void Message(T&&...) {}
 void BuffFadeBySlot(int i, bool = true) { buffs[i].spellid = SPELL_UNKNOWN; ++fades; }
 void DoBuffTic(const Buffs_Struct&, int, Mob*) { ++tics; }
 void SendPetBuffsToClient() {}
 EQApplicationPacket *MakeBuffsPacket() { return new EQApplicationPacket; }
 void CalcBonuses() {}
 Buffs_Struct *GetBuffs() { return buffs; }
 int AddBuff(Mob*, uint16, int = 0, int32 = -1, bool = false);
 int CalcBuffDuration(Mob*, Mob*, uint16, int32 = -1);
 int32 GetActSpellDuration(uint16, int32);
 int32 GetBuffDurationForTarget(uint16, int32) const;
 void BuffProcess();
 void BuffModifyDurationBySpellID(uint16, int32);
 void SetBuffDuration(int, int, int);
 void SpellOnTarget(uint16 id, Mob* dest, int, bool, int, bool, int level, int duration, bool overwrite) {
  dest->AddBuff(this, id, duration, level, overwrite);
 }
};
struct Client : Mob {
 Client() { player = true; }
 bool GetPVP() const { return false; }
 int CharacterID() const { return 5; }
 EQ::versions::ClientVersion ClientVersion() const { return EQ::versions::ClientVersion::RoF2; }
 int ClientVersionBit() const { return EQ::versions::maskSoFAndLater; }
 void QueuePacket(EQApplicationPacket*) {}
 int restore_packets = 0;
 std::vector<SpellBuffPacket_Struct> packets;
 void FastQueuePacket(EQApplicationPacket **out) {
  packets.push_back((*out)->packet);
  if (packets.back().bufffade == 3) ++restore_packets;
  delete *out;
 }
 int32 BuffEffectDurationForClient(int32 ticks) const { return ticks; }
 void SendBuffDurationPacket(Buffs_Struct&, int, bool restore = false);
 void SendBuffNumHitPacket(const Buffs_Struct&, int) {}
 uint32 GetFirstBuffSlot(bool, bool) override;
 uint32 GetLastBuffSlot(bool, bool) override;
 void RestoreBuffEffects();
 void ProcessFixedAADurations();
};
Client *Mob::CastToClient() { return static_cast<Client*>(this); }
struct ZoneDatabase { void SaveBuffs(Client*); void LoadBuffs(Client*); } database;
struct CharacterBuffsRepository {
 struct CharacterBuffs {
  int character_id = 0, slot_id = 0, spell_id = 0, caster_level = 0, ticsremaining = 0, counters = 0;
  int numhits = 0, melee_rune = 0, magic_rune = 0, persistent = 0, dot_rune = 0;
  int caston_x = 0, caston_y = 0, caston_z = 0, ExtraDIChance = 0, instrument_mod = 0;
  std::string caster_name;
 };
 static inline std::vector<CharacterBuffs> rows;
 static void DeleteWhere(ZoneDatabase&, const std::string&) { rows.clear(); }
 static CharacterBuffs NewEntity() { return {}; }
 static void ReplaceMany(ZoneDatabase&, const std::vector<CharacterBuffs>& data) { rows = data; }
 static auto GetWhere(ZoneDatabase&, const std::string&) { return rows; }
};

// NATIVE_METHODS

void check(bool ok, const char* why) {
 if (!ok) throw std::runtime_error(why);
}
void setup() {
 rank(8303, rage); rank(13484, bloodlust);
 for (auto id : {rage, bloodlust, short_control, long_control}) {
  auto& s = spells[id];
  s.short_buff_box = id == long_control ? 0 : -1;
  s.buff_duration_formula = id == rage ? 3 : 8;
  s.buff_duration = id == rage ? 2 : 3;
  s.suspendable = id != rage;
  std::fill(std::begin(s.effect_id), std::end(s.effect_id), 254);
  s.effect_id[0] = 200;
 }
 spells[rage].endurance_cost = 200; spells[rage].endurance_upkeep = 10;
 spells[rage].base_value[0] = spells[bloodlust].base_value[0] = 10000;
 spells[bloodlust].max_value[0] = 10000;
}
void frame(Client& c, bool tick) {
#if CANDIDATE
 c.ProcessFixedAADurations();
#endif
 if (tick) c.BuffProcess();
}
void measurements() {
 for (auto id : {rage, bloodlust, short_control}) {
  for (auto phase : {1, 3000, 5999}) {
   for (auto focus : {std::pair<int,int>{0,0}, {0,1}, {50,0}, {100,2}}) {
    Client player;
    auto start = now_ms;
    player.percent = focus.first; player.extra = focus.second;
    int slot = player.AddBuff(&player, id);
    check(slot == long_slots, "short/song slot mapping changed");
    int expected_focus_reads = id == rage || (CANDIDATE && id == bloodlust) ? 0 : 2;
    check(player.focus_reads == expected_focus_reads, "unexpected duration focus lookup on application");
    int ticks = player.buffs[slot].ticsremaining;
    int elapsed = 0;
    while (player.buffs[slot].spellid == id && elapsed < 90000) {
     ++elapsed; now_ms = start + elapsed;
     frame(player, elapsed >= phase && (elapsed - phase) % 6000 == 0);
    }
    check(player.fades == 1, "buff failed to fade exactly once");
    int native = (id == rage ? 2 : 3);
    int ordinary_ticks = id == rage ? native : int((native * (100+focus.first))/100.0f) + focus.second;
    if (focus.first == 50 && id != rage) ordinary_ticks = 5;
    int expected = CANDIDATE && id != short_control ? (id == rage ? 12000 : 24000) : phase + ordinary_ticks * 6000;
    check(elapsed == expected, "measured fade did not match expected native phase or deadline");
    std::cout << "phase," << id << ',' << phase << ',' << focus.first << ',' << focus.second << ',' << ticks << ',' << elapsed << '\n';
   }
  }
 }
}
void lifecycle() {
 for (auto id : {rage, bloodlust}) {
  const int duration = id == rage ? 12000 : 24000;
  Client player; const int s = player.AddBuff(&player, id);
  now_ms += 3999; frame(player, false);
  player.blocked = true;
  player.focus_reads = 0;
  check(player.AddBuff(&player, id) == -1, "blocked refresh applied");
  check(player.focus_reads == (CANDIDATE || id == rage ? 0 : 2), "blocked AA attempted to consume focus");
  player.blocked = false;
  now_ms += duration - 4000; frame(player, false);
  check(player.buffs[s].spellid == id, "expired before deadline");
  ++now_ms; frame(player, false);
  check((player.buffs[s].spellid == SPELL_UNKNOWN) == bool(CANDIDATE), "deadline after blocked refresh");
  Client refreshed;
  int r = refreshed.AddBuff(&refreshed,id);
  now_ms += 6000; frame(refreshed,true);
  check(refreshed.AddBuff(&refreshed,id) == r, "refresh did not reuse original slot");
  now_ms += duration - 1; frame(refreshed,false);
  check(refreshed.buffs[r].spellid == id, "old refresh deadline survived");
  ++now_ms; frame(refreshed,false);
  check((refreshed.buffs[r].spellid == SPELL_UNKNOWN) == bool(CANDIDATE), "new refresh deadline");
  Client dispelled; r=dispelled.AddBuff(&dispelled,id);
  now_ms+=1000; dispelled.BuffFadeBySlot(r);
  check(dispelled.AddBuff(&dispelled,short_control)==r,"dispelled slot not reused");
  now_ms += duration; frame(dispelled,false);
  check(dispelled.buffs[r].spellid==short_control && dispelled.fades==1,"stale expiry removed ordinary buff");
  Client departing; int a=departing.AddBuff(&departing,id);
  int ordinary=departing.AddBuff(&departing,long_control);
  departing.buffs[ordinary].caston_x=-145;
  check(ordinary<long_slots && a>=long_slots, "wrong real slot ranges");
  now_ms+=3900; frame(departing,false); database.SaveBuffs(&departing);
  auto saved=CharacterBuffsRepository::rows;
  check(saved.size() == (CANDIDATE ? 2u : 1u), "wrong saved song/long row count");
  now_ms+=100; Client zoned; database.LoadBuffs(&zoned); zoned.RestoreBuffEffects();
  for (const auto& packet : zoned.packets) {
   if (packet.buff.spellid == id) {
    check(packet.buff.x == 0 && packet.buff.y == 0 && packet.buff.z == 0, "encoded deadline leaked in restore packet");
    check(packet.buff.duration == duration/6000 && packet.bufffade == 3, "RoF2 restore duration or install mode");
   } else {
    check(packet.buff.x == -145, "ordinary packet lost real coordinates");
   }
  }
  check(zoned.buffs[ordinary].spellid==long_control && zoned.buffs[ordinary].caston_x==-145,"ordinary saved coordinates changed");
  check(zoned.buffs[ordinary].ticsremaining==PERMANENT_BUFF_DURATION,"ordinary long buff lost permanence");
  check((zoned.buffs[a].spellid==id)==bool(CANDIDATE),"zoning restored wrong fixed effect");
  now_ms+=duration-4001; frame(zoned,false);
  check((zoned.buffs[a].spellid==id)==bool(CANDIDATE),"saved deadline faded early");
  ++now_ms; frame(zoned,false);
  check(zoned.buffs[a].spellid==SPELL_UNKNOWN,"initial deadline extended on zoning");
  Client late; database.LoadBuffs(&late); late.RestoreBuffEffects();
  check(late.buffs[a].spellid==SPELL_UNKNOWN && late.restore_packets==1,"expired buff sent to returning client");
  CharacterBuffsRepository::CharacterBuffs old;
  old.slot_id=0; old.spell_id=id; old.ticsremaining=99;
  CharacterBuffsRepository::rows={old};
  Client legacy; database.LoadBuffs(&legacy);
  check((legacy.buffs[0].spellid==SPELL_UNKNOWN)==bool(CANDIDATE),"legacy deadline handling changed");
  std::cout<<"lifecycle,"<<id<<','<<saved.size()<<','<<zoned.restore_packets<<','<<late.restore_packets<<'\n';
 }
}
void controls() {
 for (auto id : {rage,bloodlust}) {
  const int duration = id == rage ? 12000 : 24000;
  const int native_ticks = id == rage ? 2 : 3;
  Client overridden;
  int slot = overridden.AddBuff(&overridden,id,99,50);
  check(overridden.buffs[slot].ticsremaining == (CANDIDATE ? duration/6000 : 99), "explicit duration override changed fixed expiry");
  now_ms += 4500; frame(overridden,false);
  overridden.BuffModifyDurationBySpellID(id,86);
  check(overridden.buffs[slot].ticsremaining == (CANDIDATE ? duration/6000 : 86), "duration-edit API");
  int ordinary = overridden.AddBuff(&overridden,short_control);
  overridden.SetBuffDuration(-1,77,50);
  check(overridden.buffs[slot].ticsremaining == (CANDIDATE ? duration/6000 : 77), "all-buff rewrite reset AA");
  check(overridden.buffs[ordinary].ticsremaining == 77, "mass duration edit skipped ordinary spell");
  now_ms+=duration-4501; frame(overridden,false);
  check(overridden.buffs[slot].spellid==id, "forced duration shortened window");
  now_ms+=83; frame(overridden,false);
  check((overridden.buffs[slot].spellid==SPELL_UNKNOWN)==bool(CANDIDATE), "first scheduled frame past deadline");
  rule_NightcapTHJBehaviors = false;
  Client disabled;
  int raw = disabled.AddBuff(&disabled,id);
  check(disabled.buffs[raw].ticsremaining == native_ticks, "disabled rule changed original spell");
  now_ms += duration;
  frame(disabled,false);
  check(disabled.buffs[raw].spellid == id, "disabled rule armed deadline");
  rule_NightcapTHJBehaviors = true;
  Mob npc;
  int n = npc.AddBuff(&npc,id);
  check(npc.buffs[n].ticsremaining == native_ticks, "NPC was given player timing");
  std::cout<<"guard,duration_edits_and_gates,"<<id<<'\n';
 }
 // Short-slot persistence must only include managed spells. Seed both at once.
 Client both;
 const int a=both.AddBuff(&both,rage), b=both.AddBuff(&both,bloodlust);
 both.AddBuff(&both,short_control);
 database.SaveBuffs(&both);
 check(CharacterBuffsRepository::rows.size()==(CANDIDATE ? 2u : 0u), "song slot broadening");
 now_ms+=12000; frame(both,false);
 check((both.buffs[a].spellid==SPELL_UNKNOWN)==bool(CANDIDATE) && both.buffs[b].spellid==bloodlust,"independent deadlines");
 now_ms+=12000; frame(both,false);
 check((both.buffs[b].spellid==SPELL_UNKNOWN)==bool(CANDIDATE),"second independent deadline");
 std::cout<<"guard,simultaneous_short_slots,0\n";
 // Suspend an active Bloodlust, cross a logout and resume the saved 19 seconds.
 Client frozen;
 const int bk=frozen.AddBuff(&frozen,bloodlust);
 const int rr=frozen.AddBuff(&frozen,rage);
 now_ms+=5000; zone->suspended=true; frame(frozen,false);
 now_ms+=7000; frame(frozen,true);
 check((frozen.buffs[rr].spellid==SPELL_UNKNOWN)==bool(CANDIDATE),"nonsuspendable Rage paused");
 now_ms+=90000; frame(frozen,true);
 check(frozen.buffs[bk].spellid==bloodlust,"suspended Bloodlust expired");
 database.SaveBuffs(&frozen);
 now_ms+=90000;
 Client returning; zone->suspended=false;
 database.LoadBuffs(&returning); returning.RestoreBuffEffects();
 check((returning.buffs[bk].spellid==bloodlust)==bool(CANDIDATE),"suspended resume");
 now_ms+=18999; frame(returning,false);
 check((returning.buffs[bk].spellid==bloodlust)==bool(CANDIDATE),"resumed Bloodlust expired early");
 ++now_ms; frame(returning,false);
 check(returning.buffs[bk].spellid==SPELL_UNKNOWN,"resumed Bloodlust overran remaining duration");
 std::cout<<"guard,suspension_and_resume,19000\n";
 if (CANDIDATE) {
  Client late; auto s=late.AddBuff(&late,bloodlust);
  now_ms+=23900; database.SaveBuffs(&late);
  Client just_loaded; database.LoadBuffs(&just_loaded);
  now_ms+=100; just_loaded.RestoreBuffEffects();
  check(just_loaded.buffs[s].spellid==SPELL_UNKNOWN && just_loaded.restore_packets==0,"expired between load and icon install");
  for (auto& row : CharacterBuffsRepository::rows) row.caston_y=60001;
  Client corrupt; database.LoadBuffs(&corrupt);
  check(corrupt.buffs[s].spellid==SPELL_UNKNOWN,"corrupt deadline minted time");
  std::cout<<"guard,restore_race_and_invalid_storage,0\n";
  Client repeated;
  int fixed_slot=repeated.AddBuff(&repeated,rage);
  int plain_slot=repeated.AddBuff(&repeated,short_control);
  CharacterBuffsRepository::rows.clear();
  database.LoadBuffs(&repeated);
  check(repeated.buffs[fixed_slot].spellid==SPELL_UNKNOWN && repeated.buffs[plain_slot].spellid==short_control,
        "repeated load retained old deadline or cleared ordinary song");
  rule_NightcapTHJBehaviors=false;
  CharacterBuffsRepository::CharacterBuffs legacy;
  legacy.spell_id=rage; legacy.slot_id=fixed_slot; legacy.ticsremaining=99;
  CharacterBuffsRepository::rows={legacy};
  database.LoadBuffs(&repeated);
  check(repeated.buffs[fixed_slot].spellid==SPELL_UNKNOWN, "rule-off loaded unmarked song row");
  rule_NightcapTHJBehaviors=true;
  Client switching;
  int already=switching.AddBuff(&switching,bloodlust);
  rule_NightcapTHJBehaviors=false;
  now_ms+=8000; database.SaveBuffs(&switching);
  Client active; database.LoadBuffs(&active);
  now_ms+=15999; frame(active,false);
  check(active.buffs[already].spellid==bloodlust,"rule toggle lost existing deadline");
  ++now_ms; frame(active,false);
  check(active.buffs[already].spellid==SPELL_UNKNOWN,"rule toggle stopped deadline");
  rule_NightcapTHJBehaviors=true;
  std::cout<<"guard,repeated_load_and_rule_toggle,0\n";
 }
}
int main() {
 try { setup(); measurements(); lifecycle(); controls(); }
 catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
