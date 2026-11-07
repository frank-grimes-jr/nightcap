// Included inside NightcapDungeon. Native Tasks are the only story ledger.
namespace Lantern {
namespace P=NightcapLantern;
struct Run { std::string id; unsigned instance=0,start=0,scene=0; uint64_t expires=0; };
struct Attempt {
	std::string token;
	int segment=-1;
	unsigned wave=0,guardian=0,leader=0;
	uint64_t expires=0,next=0,brand_at=0;
	glm::vec4 brand{};
	std::set<unsigned> actors,enemies;
};
Run run;
Attempt attempt;
bool owned=false, operational=false;
uint64_t tick=0;
unsigned return_guide=0;
std::set<unsigned> members;
glm::vec4 Position(const P::Point &p) { return {p.x,p.y,p.z,p.h}; }
bool Live(Client *c) { return c && c->Connected() && c->ClientDataLoaded() && !c->IsDead() && !c->IsAIControlled() && !c->IsZoning(); }
uint16_t Completed(Client *c) {
	uint16_t bits=0;
	for (auto row:Query(fmt::format("SELECT taskid FROM completed_tasks WHERE charid={} AND activityid=-1 AND taskid BETWEEN 9500 AND 9515",c->CharacterID()))) {
		const auto task=Strings::ToUnsignedInt(row[0]);
		if (task>=P::FirstTask && task<P::FirstTask+P::TaskCount) { bits|=1u<<(task-P::FirstTask); }
	}
	return bits;
}
void Reconcile(Client *c) {
	const auto completed=Completed(c); auto state=c->GetTaskState();
	if (!state) { return; }
	for (unsigned i=0;i<P::TaskCount;++i) {
		const unsigned task=P::FirstTask+i;
		if ((completed&(1u<<i)) && c->IsTaskActive(task)) { state->RemoveTaskByTaskID(c,task); }
	}
}
bool Enabled() {
	auto r=database.QueryDatabase(fmt::format("SELECT revision FROM nightcap_lantern_control WHERE id=1 AND enabled=1 AND revision={}",P::Revision),false);
	if (!r.Success() || r.RowCount()!=1 || WorldContentService::Instance()->GetCurrentExpansion()!=0 || !RuleB(TaskSystem,RecordCompletedTasks)) { return false; }
	const std::string tables="'nightcap_lantern_control','nightcap_lantern_slots','nightcap_lantern_refits','nightcap_lantern_runs','nightcap_lantern_members','nightcap_lantern_memorials',"
		"'nightcap_epic05_control','nightcap_epic05_state','tasks','task_activities','completed_tasks','character_tasks','character_activities','inventory','character_advloot_claims','instance_list','instance_list_player'";
	auto engines=Query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ("+tables+")");
	auto triggers=Query("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ("+tables+")");
	return engines.RowCount()==1 && triggers.RowCount()==1 && std::string(engines.begin()[0])=="17" && std::string(triggers.begin()[0])=="0";
}
bool Cached() {
	for (unsigned id=P::FirstArmor;id<P::FirstArmor+P::ArmorCount;++id) {
		auto item=database.GetItem(id); if (!item || !P::CacheMatches(*item)) { return false; }
	}
	return database.GetItem(P::Charm)!=nullptr;
}
bool Actor(Mob *n) { return owned && n && n->IsNPC() && !run.id.empty() && n->GetEntityVariable("lantern-run")==run.id; }
bool Friendly(Mob *n) { return Actor(n) && n->GetEntityVariable("lantern-role")!="enemy"; }
bool Enemy(Mob *n) { return Actor(n) && n->GetEntityVariable("lantern-role")=="enemy"; }
void Clear(unsigned dying=0) {
	for (auto id:attempt.actors) {
		auto n=entity_list.GetNPCByID(id);
		if (id!=dying && Actor(n) && n->GetEntityVariable("lantern-token")==attempt.token) { n->Depop(); }
	}
	attempt={};
}
void Say(const char *who,const char *line) { entity_list.Message(0,Chat::Shout,"%s says, '%s'",who,line); }
void Return(Client *c) { c->MovePC(uint32_t(22),uint16_t(0),-215.0f,-1600.0f,3.75f,216.0f); }
bool Eligible(Client *c,unsigned task) {
	return Live(c) && P::CanOffer(task,c->GetLevel(),Completed(c)) && c->IsTaskActive(task);
}
bool Present(Client *c) {
	return owned && Live(c) && c->GetInstanceID()==run.instance && members.count(c->CharacterID());
}
bool Credit(Client *c,unsigned activity,const glm::vec4 &where) {
	if (!operational || run.expires<=Now() || !Enabled()) { return false; }
	const auto task=P::Scenes[run.scene].task;
	P::Credit credit{c && c->Connected(),c && c->ClientDataLoaded(),Live(c),Present(c),
		c && Eligible(c,task),c && c->IsTaskActive(task),c && c->IsTaskActivityActive(task,activity),
		c ? DistanceSquared(c->GetPosition(),where) : -1};
	if (!P::CanCredit(credit)) { return false; }
	c->UpdateTaskActivity(task,activity,1,true);
	if (!c->SaveTaskState()) { c->Message(Chat::Yellow,"Your journal update is waiting for storage. Speak with the company again to retry."); return false; }
	return true;
}
void CreditNearby(unsigned activity,const glm::vec4 &where,Client *killer=nullptr) {
	if (killer) { for (auto c:killer->GetPartyMembers()) { Credit(c,activity,where); } }
	else { for (auto id:members) { Credit(entity_list.GetClientByCharID(id),activity,where); } }
}
unsigned ResumeWave(const P::Segment &segment) {
	if (!segment.per_wave) { return 0; }
	unsigned result=segment.waves;
	for (auto id:members) {
		auto c=entity_list.GetClientByCharID(id); const auto task=P::Scenes[run.scene].task;
		if (!Present(c) || !Eligible(c,task) || !c->IsTaskActivityActive(task,segment.first)) { continue; }
		const int done=c->GetTaskState()->GetTaskActivityDoneCountFromTaskID(task,segment.first);
		if (done<0 || unsigned(done)>=segment.waves) { throw std::runtime_error("Invalid native retreat checkpoint."); }
		result=std::min(result,unsigned(done));
	}
	if (result>=segment.waves) { throw std::runtime_error("No active native retreat checkpoint."); }
	return result;
}
void CreditWave(const P::Segment &segment,const glm::vec4 &where,Client *killer) {
	for (auto c:killer->GetPartyMembers()) {
		if (!Present(c) || !c->GetTaskState()) { continue; }
		const int done=c->GetTaskState()->GetTaskActivityDoneCountFromTaskID(P::Scenes[run.scene].task,segment.first);
		if (done>=0 && P::WaveEligible(segment,attempt.wave,unsigned(done))) { Credit(c,segment.first,where); }
	}
}
NPC *Spawn(unsigned type,const P::Point &p,const char *name,const char *role) {
	auto source=content_db.LoadNPCTypesData(type);
	if (!source) { throw std::runtime_error("A campaign actor is unavailable."); }
	auto data=new NPCType(*source);
	data->npc_id=0; data->loottable_id=0; data->exp_mod=0; data->npc_spells_id=0;
	data->npc_spells_effects_id=0; data->emoteid=0; data->merchanttype=0; data->npc_faction_id=0;
	if (name) { strn0cpy(data->name,name,sizeof(data->name)); } data->special_abilities[0]=0;
	if (type==998919) {
		if (run.scene==1 || run.scene==3 || run.scene==4) { data->gender=1; }
		const auto enemy=content_db.LoadNPCTypesData(P::Scenes[run.scene].npc);
		data->current_hp=data->max_hp=std::max<int64_t>(6000,enemy ? enemy->max_hp/4 : 6000);
		data->hp_regen=0; data->hp_regen_per_second=0;
	}
	auto n=new NPC(data,nullptr,Position(p),GravityBehavior::Water); n->GiveNPCTypeData(data);
	n->SetEntityVariable("lantern-run",run.id); n->SetEntityVariable("lantern-token",attempt.token);
	n->SetEntityVariable("lantern-role",role);
	n->SetSpecialAbility(SpecialAbility::CharmImmunity,1);
	n->SetSpecialAbility(SpecialAbility::FleeingImmunity,1);
	if (std::string(role)!="enemy") {
		n->SetOOCRegen(0); n->SetSpecialAbility(SpecialAbility::DisableMelee,1);
		n->SetSpecialAbility(SpecialAbility::AllowBeneficial,1);
		n->SetSpecialAbility(SpecialAbility::AggroImmunity,1);
		if (std::string(role)!="guardian") { n->SetSpecialAbility(SpecialAbility::NPCDamageImmunity,1); }
	}
	entity_list.AddNPC(n,true,true); attempt.actors.insert(n->GetID()); return n;
}
void SpawnEnemy(unsigned index,Client *leader,bool final=false) {
	const auto &scene=P::Scenes[run.scene];
	unsigned checkpoint=0;
	if (attempt.guardian && attempt.segment>=0 && P::Programs[run.scene].segments[attempt.segment].escort && attempt.wave) { checkpoint=(attempt.wave-1)%3; }
	auto n=Spawn(final ? 998918 : scene.npc,scene.points[(checkpoint+1+index%2)%3],final ? "The_Hollow_Witness" : nullptr,"enemy");
	attempt.enemies.insert(n->GetID());
	auto guardian=entity_list.GetNPCByID(attempt.guardian);
	if (guardian) { n->AddToHateList(guardian,20); }
	if (leader) { n->AddToHateList(leader,100); }
}
void Begin(int phase,Client *leader) {
	Clear(); attempt.segment=phase; attempt.token=NightcapLoot::NewDropID();
	attempt.expires=Now()+600; attempt.leader=leader->CharacterID();
	const auto &scene=P::Scenes[run.scene]; const auto &segment=P::Programs[run.scene].segments[phase];
	if (segment.kind==P::Kind::Records) {
		const char *names[]={"Selene_Marris_remembered","Tovin_remembered","Mera_Vell_remembered"};
		const char *lines[]={"The crates stay. The people come with us. Count them again before we leave.",
			"She counted us twice. She knew somebody was missing. She went back before I could stop her.",
			"The Witness carried the ledger. He wasn't carrying anyone. He sold our names to buy himself another morning."};
		for (unsigned i=0;i<segment.activities;++i) {
			const char *name=run.scene==1 ? "a_wayfarer_with_Meras_satchel" : run.scene==4 ? "a_keeper_of_the_company_roster" : names[i%3];
			auto n=Spawn(i%3==1 ? 998935 : 998934,scene.points[i%3],name,"record");
			n->SetEntityVariable("lantern-activity",std::to_string(segment.first+i));
			n->SetEntityVariable("lantern-line",run.scene==1 ? "Captain Selene tied this satchel shut herself. Tell Mera we kept the seal dry." :
				run.scene==4 ? "The recorder signed their names away. His own line he left blank. Take this roster home." : lines[i%3]);
		}
		Say("Mera Vell","Those are people, not entries in a ledger. Hail each memory and answer it. We will carry their names home.");
	} else if (segment.kind==P::Kind::Battle) {
		for (unsigned i=0;i<std::min(2u,segment.count);++i) { SpawnEnemy(i,leader,run.scene==7); }
		Say("The Hollow Witness","I kept the names you were too frightened to remember. Will you pay their debt as well?");
		attempt.next=Now()+18;
	} else {
		attempt.wave=ResumeWave(segment);
		const char *name=run.scene==0 ? "Tovin_the_Missing_Porter" : run.scene==3 ? "Captain_Selenes_Last_Watch" :
			run.scene==4 || run.scene==1 ? "Mera_Vell" : run.scene==7 ? "a_company_standard_bearer" : "Oren_Lanternwright";
		auto n=Spawn(998919,scene.points[segment.escort ? attempt.wave : 0],name,"guardian"); attempt.guardian=n->GetID();
		Say(name,segment.escort ? "Stay with me. Lead me to each marked checkpoint; keep the pursuers off me. If I fall, hail the memories to try again." :
			"Three waves. Hold the line while I restore the lantern. You can heal me; draw their attacks away from me.");
	}
}
void Tick() {
	if (!owned || Now()==tick) { return; } tick=Now();
	try {
		if (!operational || !Enabled() || run.expires<=Now()) {
			Clear(); for (auto id:members) { auto c=entity_list.GetClientByCharID(id); if (Live(c)) { Return(c); } } return;
		}
		if (!Actor(entity_list.GetNPCByID(return_guide))) {
			auto n=Spawn(998934,P::Scenes[run.scene].arrival,"a_lanternlit_wayfarer","guide");
			return_guide=n->GetID(); attempt.actors.erase(return_guide);
			n->SetEntityVariable("lantern-token","return-guide");
		}
		int phase=-1; Client *leader=nullptr;
		for (auto id:members) {
			auto c=entity_list.GetClientByCharID(id);
			if (!Present(c) || !Eligible(c,P::Scenes[run.scene].task)) { continue; }
			const int p=P::ActiveSegment(P::Programs[run.scene],[&](unsigned a){return c->IsTaskActivityActive(P::Scenes[run.scene].task,a);});
			if (p>=0 && (phase<0 || p<phase)) { phase=p; leader=c; }
		}
		if (phase<0) { Clear(); return; }
		if (phase!=attempt.segment) { Begin(phase,leader); }
		if (Now()>attempt.expires) { Clear(); Say("Mera Vell","Catch your breath. The memory will wait for us to be ready."); return; }
		const auto &segment=P::Programs[run.scene].segments[phase];
		if (segment.kind==P::Kind::Defense) {
			auto guardian=entity_list.GetNPCByID(attempt.guardian);
			if (!Friendly(guardian) || guardian->GetHP()<=0) { Clear(); return; }
			if (!attempt.enemies.empty()) { guardian->SetFollowID(0); guardian->SaveGuardSpot(); guardian->StopNavigation(); return; }
			if (attempt.wave>=segment.waves) { Clear(); return; }
			const auto &p=P::Scenes[run.scene].points[segment.escort ? attempt.wave : 0];
			if (segment.escort && DistanceSquared(guardian->GetPosition(),Position(p))>12.0f*12.0f) {
				guardian->SetFollowID(leader->GetID()); guardian->SetFollowDistance(36); guardian->SetFollowCanRun(true);
				leader->Message(Chat::Yellow,"Lead the company to checkpoint %u: /loc %.0f, %.0f, %.0f.",attempt.wave+1,p.y,p.x,p.z); return;
			}
			guardian->SetFollowID(0); guardian->SaveGuardSpot(); guardian->StopNavigation();
			++attempt.wave; for (unsigned i=0;i<2;++i) { SpawnEnemy(i,leader); }
			Say("A pursuer","The recorder wants no witnesses. Break their lantern!");
		}
		if (run.scene==7 && segment.kind==P::Kind::Battle) {
			auto boss=attempt.enemies.empty() ? nullptr : entity_list.GetNPCByID(*attempt.enemies.begin());
			if (!boss) { return; }
			if (attempt.brand_at && Now()>=attempt.brand_at) {
				if (!boss->IsStunned() && !boss->IsMezzed()) {
					for (auto id:members) { auto c=entity_list.GetClientByCharID(id);
						if (Present(c) && DistanceSquared(c->GetPosition(),attempt.brand)<=10.0f*10.0f) { boss->CastSpell(329,c->GetID(),EQ::spells::CastingSlot::Item,0,0); }
					}
				} attempt.brand_at=0;
			} else if (!attempt.brand_at && Now()>=attempt.next) {
				attempt.brand=leader->GetPosition(); attempt.brand_at=Now()+3; attempt.next=Now()+18;
				Say("The Hollow Witness","Your name burns here! Move from the marked ground, or stun me before the ink takes hold!");
				leader->Message(Chat::Yellow,"The Witness marks your feet. Move at least 10 units within three seconds, or stun the Witness.");
			}
		}
	} catch (const std::exception &e) { operational=false; Clear(); LogError("Last Lantern scene suspended [{}]",e.what()); }
}
bool Death(NPC *n,Mob *killer) {
	if (!Actor(n)) { return true; }
	if (!operational || n->GetEntityVariable("lantern-token")!=attempt.token) { return true; }
	if (n->GetID()==attempt.guardian) { Clear(n->GetID()); return true; }
	if (!attempt.enemies.erase(n->GetID())) { return true; }
	attempt.actors.erase(n->GetID());
	const auto &s=P::Programs[run.scene].segments[attempt.segment];
	if (killer && killer->IsNPC() && killer->CastToNPC()->GetSwarmOwner()) { killer=entity_list.GetMobID(killer->CastToNPC()->GetSwarmOwner()); }
	auto controller=killer ? killer->GetUltimateOwner() : nullptr;
	if (controller && controller->IsClient() && Present(controller->CastToClient())) {
		if (s.kind==P::Kind::Battle) { CreditNearby(s.first,n->GetPosition(),controller->CastToClient()); }
		else if (s.kind==P::Kind::Defense && attempt.enemies.empty() && P::WaveCredit(s,attempt.wave)) { CreditWave(s,n->GetPosition(),controller->CastToClient()); }
	}
	if (s.kind==P::Kind::Battle && attempt.enemies.empty()) {
		// A three-guard scene spawns its last guard only after the first pair.
		bool needs=false;
		for (auto id:members) { auto c=entity_list.GetClientByCharID(id); needs|=Present(c) && Eligible(c,P::Scenes[run.scene].task) && c->IsTaskActivityActive(P::Scenes[run.scene].task,s.first); }
		if (needs) { SpawnEnemy(0,controller && controller->IsClient() ? controller->CastToClient() : nullptr,run.scene==7); }
	}
	return true;
}
void Boot() {
	run={}; attempt={}; members.clear(); owned=false; operational=false; tick=0; return_guide=0;
	if (!zone || zone->GetInstanceVersion()!=P::SceneVersion || !zone->GetInstanceID()) { return; }
	owned=true; // Reserved version fails closed even with corrupt/missing ownership.
	auto rows=Query(fmt::format("SELECT r.run_id,r.instance_start,r.scene,r.expires_at FROM nightcap_lantern_runs r JOIN instance_list i "
		"ON i.id=r.instance_id AND i.start_time=r.instance_start AND i.notes=CONCAT('nc-lantern:',r.run_id) "
		"WHERE r.instance_id={} AND i.zone={} AND i.version={} AND r.revision={}",zone->GetInstanceID(),zone->GetZoneID(),P::SceneVersion,P::Revision));
	if (rows.RowCount()!=1) { return; }
	auto r=rows.begin(); run={r[0],zone->GetInstanceID(),Strings::ToUnsignedInt(r[1]),Strings::ToUnsignedInt(r[2]),std::stoull(r[3])};
	if (!NightcapLoot::ValidDropID(run.id) || run.scene>=8 || P::Scenes[run.scene].zone!=zone->GetZoneID()) { run={}; return; }
	for (auto row:Query("SELECT character_id FROM nightcap_lantern_members WHERE run_id="+Q(run.id))) { members.insert(Strings::ToUnsignedInt(row[0])); }
	operational=Enabled() && Cached() && members.size()<=P::SceneMembers && run.expires>Now();
}
void Connected(Client *c) {
	if (!owned || !Live(c)) { return; }
	try {
		auto member=Query(fmt::format("SELECT m.character_id FROM nightcap_lantern_members m JOIN nightcap_lantern_runs r ON r.run_id=m.run_id "
			"JOIN instance_list i ON i.id=r.instance_id AND i.start_time=r.instance_start AND i.notes=CONCAT('nc-lantern:',r.run_id) "
			"WHERE m.run_id={} AND m.character_id={} AND r.instance_id={} AND r.expires_at>{}",Q(run.id),c->CharacterID(),run.instance,Now()));
		if (member.RowCount()==1) { members.insert(c->CharacterID()); }
		else { members.erase(c->CharacterID()); }
	} catch (...) { c->Disconnect(); return; }
	if (!operational || !members.count(c->CharacterID())) { c->Message(Chat::Yellow,"This memory is unavailable. Your recorded progress is safe."); Return(c); return; }
	c->Message(Chat::White,"%s: protect your companions and follow your Tasks objectives. Say journal leave to the company to return home.",P::Scenes[run.scene].name);
}
void Enter(Client *c) {
	if (!Enabled() || !Cached()) { throw std::runtime_error("The campaign is unavailable."); }
	int selected=-1;
	for (unsigned i=0;i<8;++i) {
		const auto &s=P::Scenes[i];
		if (Eligible(c,s.task) && P::ActiveSegment(P::Programs[i],[&](unsigned a){return c->IsTaskActivityActive(s.task,a);})>=0) { selected=i; break; }
	}
	if (selected<0) { throw std::runtime_error("Finish your current Tasks objectives before entering a company memory."); }
	const auto &scene=P::Scenes[selected];
	auto party=c->IsSSF() ? std::vector<Client *>{c} : c->GetPartyMembers();
	if (party.empty()) { party.push_back(c); }
	if (party.size()>P::SceneMembers) { throw std::runtime_error("A company memory admits at most six people."); }
	for (auto member:party) {
		if (!Live(member) || member->GetLevel()<scene.level || member->IsEngaged() || member->IsCasting() ||
			DistanceSquared(member->GetPosition(),c->GetPosition())>75.0f*75.0f || (member!=c && member->IsSSF())) {
			throw std::runtime_error("Bring living companions of the chapter's level within 75 units, safely out of combat.");
		}
	}
	if (c->GetGroup() && c->GetGroup()->GetLeaderName()!=c->GetName()) { throw std::runtime_error("Your group leader opens the memory."); }
	Transaction tx;
	Query("SELECT id FROM nightcap_dungeon_state WHERE id=1 FOR UPDATE");
	if (Query("SELECT id FROM nightcap_lantern_control WHERE id=1 AND enabled=1 FOR UPDATE").RowCount()!=1) { throw std::runtime_error("The campaign is unavailable."); }
	auto rows=Query(fmt::format("SELECT r.run_id,r.instance_id,r.instance_start,r.expires_at FROM nightcap_lantern_runs r JOIN instance_list i "
		"ON i.id=r.instance_id AND i.start_time=r.instance_start AND i.notes=CONCAT('nc-lantern:',r.run_id) "
		"JOIN nightcap_lantern_members m ON m.run_id=r.run_id WHERE m.character_id={} AND r.scene={} AND r.expires_at>{} FOR UPDATE",c->CharacterID(),selected,Now()));
	Run destination;
	if (rows.RowCount()>1) { throw std::runtime_error("Multiple company memories require operator review."); }
	if (rows.RowCount()) { auto row=rows.begin(); destination={row[0],Strings::ToUnsignedInt(row[1]),Strings::ToUnsignedInt(row[2]),unsigned(selected),std::stoull(row[3])}; }
	else {
		const auto reserved=RuleI(Instances,ReservedInstances);
		if (reserved<0 || reserved>=32000) { throw std::runtime_error("Invalid native instance range."); }
		auto free=Query(fmt::format("SELECT MIN(candidate) FROM (SELECT {} AS candidate UNION SELECT id+1 FROM instance_list WHERE id>={}) ids "
			"WHERE candidate<=32000 AND NOT EXISTS (SELECT 1 FROM instance_list i WHERE i.id=ids.candidate) "
			"AND NOT EXISTS (SELECT 1 FROM character_corpses c WHERE c.instance_id=ids.candidate)",reserved+1,reserved));
		if (!free.RowCount() || !free.begin()[0]) { throw std::runtime_error("No safe instance allocation is available."); }
		destination={NightcapLoot::NewDropID(),Strings::ToUnsignedInt(free.begin()[0]),unsigned(Now()),unsigned(selected),Now()+P::SceneDuration};
		Query(fmt::format("INSERT INTO instance_list(id,zone,version,is_global,start_time,duration,expire_at,never_expires,notes) VALUES ({},{},{},0,{},{},{},0,{})",
			destination.instance,scene.zone,P::SceneVersion,destination.start,P::SceneDuration,destination.expires,Q("nc-lantern:"+destination.id)));
		Query(fmt::format("INSERT INTO nightcap_lantern_runs VALUES ({},{},{},{},{},{},{})",Q(destination.id),destination.instance,destination.start,selected,c->CharacterID(),destination.expires,P::Revision));
	}
	for (auto member:party) {
		Query(fmt::format("INSERT IGNORE INTO nightcap_lantern_members VALUES ({},{})",Q(destination.id),member->CharacterID()));
		Query(fmt::format("INSERT IGNORE INTO instance_list_player(id,charid) VALUES ({},{})",destination.instance,member->CharacterID()));
	}
	auto count=Query("SELECT COUNT(*) FROM nightcap_lantern_members WHERE run_id="+Q(destination.id));
	if (std::stoul(count.begin()[0])>P::SceneMembers) { throw std::runtime_error("This memory already has six participants."); }
	tx.Commit();
	for (auto member:party) { member->MovePC(scene.zone,destination.instance,scene.arrival.x,scene.arrival.y,scene.arrival.z,scene.arrival.h); }
}
void Claim(Client *c,unsigned armor_slot,unsigned fit) {
	if (!Live(c) || c->IsEngaged() || c->IsCasting() || (c->trade && c->trade->With()) || c->GetTradeskillObject() ||
		c->IsLooting() || c->GetMerchantSessionEntityID() || !c->GetInv().CursorEmpty()) {
		throw std::runtime_error("Finish combat, close trades, loot and merchant windows, and empty your cursor before claiming or refitting.");
	}
	if (!c->SaveTaskState()) { throw std::runtime_error("Your Tasks could not be saved."); }
	const auto completed=Completed(c);
	const unsigned target=armor_slot==8 ? P::Charm : P::ArmorID(fit,P::Grade(completed),armor_slot);
	if (armor_slot>8 || (armor_slot<8 && !P::ArmorEarned(target,c->GetLevel(),c->GetClassMask(),completed))) { throw std::runtime_error("That armor fit or chapter has not been earned."); }
	if (armor_slot==8) {
		auto earned=Query(fmt::format("SELECT active_path FROM nightcap_epic05_state WHERE character_id={}",c->CharacterID()));
		if (c->GetLevel()<35 || !P::HasOath(completed) || earned.RowCount()!=1 || !earned.begin()[0] || std::string(earned.begin()[0]).empty()) { throw std::runtime_error("Earn a path and attune it with the Chronicler first."); }
		const std::string path=earned.begin()[0]; bool attuned=false;
		for (const auto &entry:std::vector<std::pair<const char *,unsigned>>{{"guardian",3},{"striker",4},{"arcanist",5},{"warden",6},{"binder",7}}) {
			if (path==entry.first && (completed&(1u<<entry.second))) { attuned=true; }
		}
		if (!attuned) { throw std::runtime_error("Attune a path that you have personally completed."); }
	}
	unsigned item=0; std::string receipt;
	{
		Transaction tx;
		auto gate=Query(fmt::format("SELECT id FROM nightcap_lantern_control WHERE id=1 AND enabled=1 AND revision={} FOR UPDATE",P::Revision));
		if (gate.RowCount()!=1) { throw std::runtime_error("The campaign is unavailable."); }
		auto row=Query(fmt::format("SELECT item_id,drop_id FROM nightcap_lantern_slots WHERE character_id={} AND armor_slot={} FOR UPDATE",c->CharacterID(),armor_slot));
		if (!row.RowCount()) {
			receipt=NightcapLoot::NewDropID(); item=target;
			Query(fmt::format("INSERT INTO nightcap_lantern_slots VALUES ({},{},{},{})",c->CharacterID(),armor_slot,item,Q(receipt)));
		} else { item=Strings::ToUnsignedInt(row.begin()[0]); receipt=row.begin()[1]; }
		tx.Commit();
	}
	if (!NightcapLoot::ValidDropID(receipt) || (armor_slot==8 ? item!=P::Charm : !P::IsArmor(item) || P::Decode(item).slot!=armor_slot)) { throw std::runtime_error("Your armor entitlement needs operator review."); }
	auto delivered=Query("SELECT character_id FROM character_advloot_claims WHERE drop_id="+Q(receipt));
	if (delivered.RowCount()) {
		if (delivered.RowCount()!=1 || Strings::ToUnsignedInt(delivered.begin()[0])!=c->CharacterID()) { throw std::runtime_error("Your delivery receipt needs operator review."); }
		if (armor_slot==8) { c->Message(Chat::White,"Your oath charm has already been delivered. Check your equipment, bags and bank."); return; }
		auto slots=NightcapLoot::ForgeSlots(c); for (auto worn:P::WornSlots) { slots.push_back(worn); }
		int16_t found=-1;
		for (auto slot:slots) { auto inst=c->GetInv().GetItem(slot); if (inst && P::IsArmor(inst->GetID()) && P::Decode(inst->GetID()).slot==armor_slot) {
			if (found!=-1) { throw std::runtime_error("More than one copy needs operator review."); } found=slot;
		} }
		if (found<0) { throw std::runtime_error("Bring your original piece from the bank. Missing earned armor requires operator review; it cannot be duplicated."); }
		if (c->GetInv().GetItem(found)->GetID()==target) { c->Message(Chat::White,"That piece already has this fit and earned grade."); return; }
		if (NightcapLoot::RefitLanternItem(c,found,target,NightcapLoot::NewDropID())==NightcapLoot::TransferResult::Delivered) {
			c->Message(Chat::Yellow,"Oren says, 'New seams, same road. Your augments and personal touches are still here.'");
		} else { c->Message(Chat::Yellow,"The refit is pending. Close other interactions and empty your cursor before trying again."); }
		return;
	}
	if (armor_slot<8 && !P::ArmorEarned(item,c->GetLevel(),c->GetClassMask(),completed)) { throw std::runtime_error("Your reserved fit is no longer legal for your classes. Ask an operator to review the undelivered reservation."); }
	// A missing receipt is never evidence that a physical copy is missing.
	const std::string identity=armor_slot==8 ? "item_id=900501" :
		fmt::format("item_id BETWEEN {} AND {} AND MOD(item_id-{},8)={}",P::FirstArmor,P::FirstArmor+P::ArmorCount-1,P::FirstArmor,armor_slot);
	if (Query(fmt::format("SELECT item_id FROM inventory WHERE character_id={} AND ({}) LIMIT 1",c->CharacterID(),identity)).RowCount()) {
		throw std::runtime_error("An existing copy without a matching receipt needs operator review.");
	}
	for (const auto *table:{"sharedbank","guild_bank","character_parcels","character_parcels_containers","character_pet_inventory","character_pet_armor","nightcap_bazaar_items","trader"}) {
		if (Query("SELECT item_id FROM "+std::string(table)+" WHERE "+identity+" LIMIT 1").RowCount()) { throw std::runtime_error("Conflicting campaign custody needs operator review."); }
	}
	if (Query(fmt::format("SELECT item_id FROM character_corpse_items WHERE corpse_id IN (SELECT id FROM character_corpses WHERE charid={}) AND ({}) LIMIT 1",c->CharacterID(),identity)).RowCount()) { throw std::runtime_error("Retrieve your earned equipment from your corpse before asking again."); }
	if (Query("SELECT itemid FROM object_contents WHERE "+Strings::Replace(identity,"item_id","itemid")+" LIMIT 1").RowCount()) { throw std::runtime_error("Conflicting ground custody needs operator review."); }
	std::unique_ptr<EQ::ItemInstance> instance(database.CreateItem(item,1));
	if (!instance) { throw std::runtime_error("The earned equipment cache is unavailable."); }
	if (NightcapLoot::ReceiveItem(c,*instance,{receipt})==NightcapLoot::TransferResult::Delivered) {
		c->Message(Chat::Yellow,"Oren says, 'I made this to get you home. Wear it somewhere worth remembering.'");
		if (item!=target) { c->Message(Chat::White,"Your original first choice was reserved before delivery. Choose your desired legal fit again to refit this piece."); }
	} else { c->Message(Chat::Yellow,"Your earned piece remains reserved. Make inventory space, then ask again."); }
}
void Menu(Client *c) {
	c->Message(Chat::White,"The Chronicler turns a lantern toward an unfinished ledger. 'The road remembers who came home. Help me recover the rest.'");
	c->Message(Chat::White,"The Last Lantern: twelve chapters from level 20 to 50. Open Tasks for your current objectives.");
	const auto completed=Completed(c);
	for (const auto &task:P::Tasks) {
		if (c->IsTaskActive(task.id)) { c->Message(Chat::White,"Continue: %s. %s",task.name,Saylink::Silent("journal enter","Enter its company memory").c_str()); }
		else if (P::CanOffer(task.id,c->GetLevel(),completed)) {
			c->Message(Chat::White,"%s",Saylink::Silent("journal begin "+std::to_string(task.id),task.name).c_str());
		}
	}
	c->Message(Chat::White,"%s | %s | %s",Saylink::Silent("journal report","Report to this companion").c_str(),Saylink::Silent("journal armor","Earned armor and refits").c_str(),Saylink::Silent("journal forge","Claim Wayfarer's Oath").c_str());
	for (const auto &path:std::vector<std::pair<const char *,unsigned>>{{"guardian",9503},{"striker",9504},{"arcanist",9505},{"warden",9506},{"binder",9507}}) {
		if (c->IsTaskCompleted(path.second)) { c->Message(Chat::White,"%s",Saylink::Silent(std::string("journal attune ")+path.first,std::string("Attune ")+path.first).c_str()); }
	}
}
bool Action(Client *c,NPC *n,const std::string &text) {
	if (!c || !n || !zone) { return false; }
	const auto id=n->GetNPCTypeID();
	const bool public_actor=!zone->GetInstanceID() && (id==999220 || (id>=998900 && id<=998905));
	if (!public_actor && !Actor(n)) { return false; }
	const auto say=Strings::ToLower(text);
	if (say.rfind("journal attune ",0)==0 && id==999220) { return false; }
	if (say.rfind("journal",0)!=0 && say!="hail" && say.rfind("hail,",0)!=0) { return false; }
	// Keep the Chronicler's class/SSF hail intact.
	if (id==999220 && say.rfind("hail",0)==0) { return false; }
	try {
		if (!Live(c) || c->IsEngaged() || c->IsCasting() || c->IsStunned() || c->IsMezzed() ||
			DistanceSquared(c->GetPosition(),n->GetPosition())>50.0f*50.0f) { throw std::runtime_error("Approach safely out of combat to speak with the company."); }
		if (owned && say=="journal leave") { Return(c); return true; }
		if (!Enabled()) { throw std::runtime_error("The Adventure Journal is temporarily unavailable. Your progress is safe."); }
		if (!c->SaveTaskState()) { throw std::runtime_error("Your native Tasks could not be saved. Try again when the journal is available."); }
		Reconcile(c);
		if (Actor(n)) {
			if (!Present(c)) { return true; }
			if (n->GetEntityVariable("lantern-role")=="guide") {
				c->Message(Chat::White,"The company will keep the lantern lit. %s",Saylink::Silent("journal leave","Return to the Commonlands camp").c_str()); return true;
			}
			if (n->GetEntityVariable("lantern-token")!=attempt.token) { return true; }
			if (n->GetEntityVariable("lantern-role")=="record") {
				const auto activity=Strings::ToUnsignedInt(n->GetEntityVariable("lantern-activity"));
				CreditNearby(activity,n->GetPosition());
				Say(n->GetCleanName(),n->GetEntityVariable("lantern-line").c_str());
			} else { c->Message(Chat::White,"Stay together and follow your Tasks. %s",Saylink::Silent("journal leave","Return to the company camp").c_str()); }
			return true;
		}
		if (say=="journal enter") { if (zone->GetZoneID()!=22) { throw std::runtime_error("Ask the company in the Commonlands tunnel to open a memory."); } Enter(c); }
		else if (say=="journal forge") { if (id!=999220) { throw std::runtime_error("The Chronicler keeps the oath charm."); } Claim(c,8,0); }
		else if (say=="journal armor") {
			for (unsigned slot=0;slot<8;++slot) {
				for (unsigned fit=0;fit<4;++fit) {
					const auto target=P::ArmorID(fit,P::Grade(Completed(c)),slot);
					if (!P::ArmorEarned(target,c->GetLevel(),c->GetClassMask(),Completed(c))) { continue; }
					auto item=database.GetItem(target);
					c->Message(Chat::White,"%s",Saylink::Silent(fmt::format("journal fit {} {}",slot,fit),item ? item->Name : "Earned armor").c_str());
				}
			} c->Message(Chat::White,"Choose a legal fit for any earned piece. Oren refits your original; bring it equipped or carried. Refits preserve augments and custom dye.");
		} else if (say.rfind("journal fit ",0)==0) {
			if (id!=998901) { throw std::runtime_error("Ask Oren Lanternwright for armor and refits."); }
			unsigned slot=99,fit=99; char extra=0;
			if (std::sscanf(say.c_str(),"journal fit %u %u %c",&slot,&fit,&extra)!=2 || slot>=8 || fit>=4) { throw std::runtime_error("Choose a listed armor fit."); }
			Claim(c,slot,fit);
		} else if (say.rfind("journal begin ",0)==0) {
			unsigned task=0; char extra=0;
			if (id!=999220 || std::sscanf(say.c_str(),"journal begin %u %c",&task,&extra)!=1 || !P::CanOffer(task,c->GetLevel(),Completed(c))) { throw std::runtime_error("Ask the Chronicler for your next eligible chapter."); }
			c->AssignTask(task,n->GetID(),true);
			if (!c->IsTaskActive(task)) { throw std::runtime_error("Make room in Tasks, then ask again."); }
			c->SaveTaskState(); Menu(c);
		} else if (say=="journal memorial 0" || say=="journal memorial 1") {
			if (id!=999220 || zone->GetZoneID()!=22 || !Eligible(c,9514) || !c->IsTaskActivityActive(9514,3)) { throw std::runtime_error("Hear the company's accounts before choosing its memorial."); }
			const unsigned inscription=say.back()-'0';
			Query(fmt::format("INSERT INTO nightcap_lantern_memorials VALUES ({},{}) ON DUPLICATE KEY UPDATE inscription=VALUES(inscription)",c->CharacterID(),inscription));
			c->UpdateTaskActivity(9514,3,1,true);
			if (!c->SaveTaskState()) { throw std::runtime_error("Your inscription is recorded; native task storage needs a retry. Speak with the company again."); }
			c->Message(Chat::Yellow,"The Chronicler inscribes: %s",inscription ? "No One Walks Forgotten" : "We Carry Their Names"); Menu(c);
		} else if (say=="journal report") {
			for (const auto &goal:P::Goals) {
				if (goal.task==9514 && goal.activity==3) { continue; }
				if (goal.actor!=id || goal.version!=0 || goal.zone!=zone->GetZoneID() || !Eligible(c,goal.task) || !c->IsTaskActivityActive(goal.task,goal.activity)) { continue; }
				c->UpdateTaskActivity(goal.task,goal.activity,1,true);
			}
			if (!c->SaveTaskState()) { throw std::runtime_error("Your report could not be saved."); }
			if (id==999220 && c->IsTaskActivityActive(9514,3)) {
				c->Message(Chat::White,"Choose what we carry into the final expedition: %s | %s",Saylink::Silent("journal memorial 0","We Carry Their Names").c_str(),Saylink::Silent("journal memorial 1","No One Walks Forgotten").c_str());
			}
			if (id==999220 && c->IsTaskCompleted(9515)) {
				c->EnableTitle(995501);
				auto memorial=Query(fmt::format("SELECT inscription FROM nightcap_lantern_memorials WHERE character_id={}",c->CharacterID()));
				c->Message(Chat::Yellow,"The Chronicler closes the ledger. 'Selene Marris. Every porter. Every companion. No names sold, no names left behind. Welcome home, Lanternbearer.'");
				if (memorial.RowCount()==1) { c->Message(Chat::White,"Your company's memorial: %s",std::string(memorial.begin()[0])=="1" ? "No One Walks Forgotten" : "We Carry Their Names"); }
			}
			else if (id==998900) { c->Message(Chat::White,"Mera says, 'Selene went back for the last porter. Someone sold our names before she could return. I want to know who.'"); }
			else if (id==998901) { c->Message(Chat::White,"Oren says, 'A broken buckle tells the truth. That roster didn't. Bring your old pieces; there's more road in them yet.'"); }
			else if (id==998902) { c->Message(Chat::White,"Tovin says, 'I came home, but not all my words did. The missing pages still know how Selene got me out. Help me remember.'"); }
			else { c->Message(Chat::White,"The Chronicler adds your account to the lantern-lit ledger. Ask Oren for any newly earned armor."); }
			Menu(c);
		} else { Menu(c); }
	} catch (const std::exception &e) { c->Message(Chat::Yellow,"%s",e.what()); LogError("Last Lantern action rejected character [{}]: [{}]",c->CharacterID(),e.what()); }
	return true;
}
}
