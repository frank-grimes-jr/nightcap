// Included inside NightcapDungeon. Durable state shares its no-retry transactions.
namespace Highkeep {
namespace Policy=NightcapHighkeep;
struct State {
	bool active=false, alarm=false, rescued=false;
	uint32_t gate=0, prisoner=0, leader=0;
	uint64_t tick=0, retry=0, absent=0;
	unsigned wave=0, cleared=0;
	std::string token;
	std::set<uint32_t> enemies;
	std::map<uint32_t,Policy::Dialogue> dialogue;
} state;
glm::vec4 Position(const Policy::Point &p) { return {p.x,p.y,p.z,p.h}; }
bool Active() { return state.active && current.dungeon && Policy::Eligible(current.dungeon->zone,unsigned(current.mode),true); }
bool Live(Client *c) { return c && c->Connected() && c->ClientDataLoaded() && !c->IsDead() && !c->IsAIControlled(); }
bool Guard(Mob *m) {
	return m && m->IsNPC() && !m->HasOwner() && !m->IsPet() && !m->IsMerc() &&
		!m->CastToNPC()->GetSwarmOwner() && (Policy::Guard(m->GetNPCTypeID()) ||
		(m->GetEntityVariable("highkeep-run")==current.id && m->GetEntityVariable("highkeep-role")=="guard"));
}
bool Prisoner(Mob *m) { return Active() && m && !state.token.empty() && m->GetEntityVariable("highkeep-attempt")==state.token && m->GetEntityVariable("highkeep-role")=="prisoner" && m->GetEntityVariable("highkeep-run")==current.id; }
Mob *Controller(Mob *m) {
	if (!m) { return nullptr; }
	if (m->IsNPC() && m->CastToNPC()->GetSwarmOwner()) { m=entity_list.GetMob(m->CastToNPC()->GetSwarmOwner()); }
	return m ? m->GetUltimateOwner() : nullptr;
}
void Pause(NPC *n) { n->SetFollowID(0); n->SaveGuardSpot(); n->StopNavigation(); }
void Shout(const char *speaker,const char *line) {
	entity_list.Message(0,Chat::Shout,"%s shouts, '%s'",speaker,line);
}
// Called only for High Keep; a missing schema must never downgrade a rescue run.
bool Installed() {
	auto r=Query("SELECT enabled FROM nightcap_highkeep_state WHERE id=1 AND revision=2026102401");
	if (r.RowCount()!=1 || (std::string(r.begin()[0])!="0" && std::string(r.begin()[0])!="1")) {
		throw std::runtime_error("High Keep rescue schema mismatch.");
	}
	auto engines=Query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ('nightcap_highkeep_state','nightcap_highkeep_runs')");
	auto triggers=Query("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ('nightcap_highkeep_state','nightcap_highkeep_runs')");
	if (std::string(engines.begin()[0])!="2" || std::string(triggers.begin()[0])!="0") { throw std::runtime_error("High Keep rescue storage mismatch."); }
	for (const auto &spec:std::vector<std::pair<std::string,std::string>>{
		{"nightcap_highkeep_state","id:tinyint:NO,revision:bigint:NO,enabled:tinyint:NO"},
		{"nightcap_highkeep_runs","run_id:char:NO,alarm:tinyint:NO,rescued_at:bigint:NO"}}) {
		auto columns=Query("SELECT GROUP_CONCAT(CONCAT(column_name,':',data_type,':',is_nullable) ORDER BY ordinal_position SEPARATOR ',') FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name="+Q(spec.first));
		if (columns.RowCount()!=1 || !columns.begin()[0] || std::string(columns.begin()[0])!=spec.second) { throw std::runtime_error("High Keep column drift."); }
		auto key=Query("SELECT GROUP_CONCAT(CONCAT(index_name,':',column_name) ORDER BY index_name,seq_in_index) FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name="+Q(spec.first));
		const auto expected=spec.first=="nightcap_highkeep_state" ? "PRIMARY:id" : "PRIMARY:run_id";
		if (key.RowCount()!=1 || !key.begin()[0] || std::string(key.begin()[0])!=expected) { throw std::runtime_error("High Keep key drift."); }
	}
	auto identity=Query("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='nightcap_highkeep_runs' AND column_name='run_id' AND character_maximum_length=36 AND character_set_name='ascii' AND collation_name='ascii_bin'");
	if (std::string(identity.begin()[0])!="1") { throw std::runtime_error("High Keep UUID storage drift."); }
	return std::string(r.begin()[0])=="1";
}
void Create(const Run &run) {
	if (run.dungeon->zone!=6 || run.mode!=Mode::Raid) { return; }
	if (Installed()) { Query("INSERT INTO nightcap_highkeep_runs(run_id) VALUES ("+Q(run.id)+")"); }
}
void Boot() {
	state={};
	if (!current.dungeon || current.dungeon->zone!=6 || current.mode!=Mode::Raid) { return; }
	Installed();
	auto r=Query("SELECT alarm,rescued_at FROM nightcap_highkeep_runs WHERE run_id="+Q(current.id));
	if (!r.RowCount()) { return; } // old runs keep their original checklist
	if (r.RowCount()!=1 || (std::string(r.begin()[0])!="0" && std::string(r.begin()[0])!="1")) { throw std::runtime_error("Invalid High Keep rescue state."); }
	state.active=true; state.alarm=std::string(r.begin()[0])=="1"; state.rescued=std::stoull(r.begin()[1])>0;
}
void Alarm() {
	if (!Active() || state.alarm) { return; }
	Transaction tx; auto run=ReadRun("r.run_id="+Q(current.id),true);
	if (run.id.empty() || run.expiry<=Now()) { throw std::runtime_error("Inactive prison break."); }
	Query("UPDATE nightcap_highkeep_runs SET alarm=1 WHERE run_id="+Q(run.id)); tx.Commit(); state.alarm=true;
	Shout("Gate Sergeant","That is no relief detail! Seal the keep! These intruders are here for Osargen!");
	Shout("Osargen","I'm in the prison below! Break their command, then get me to the entrance alive!");
}
void Status(Client *c) {
	if (!Active() || !c) { return; }
	const char *next=state.rescued ? "Osargen is safe. Earned rewards remain with the Keeper." :
		!state.alarm ? "Hail the Gate Sergeant just inside the entrance. Follow his dialogue to begin the break-in." :
		!objectives.count(2) ? "Defeat Captain Boshinko on the ground-floor entrance passage (/loc -11, -108, 4)." :
		!objectives.count(1) ? "Take the prison stairs down to Captain Bosec (/loc 31, -306, -10). Stay above the goblin mines." :
		!objectives.count(3) ? "Find Dyrna Nlith in the same prison block (/loc 96, -316, -11)." :
		!objectives.count(4) ? "McCabe is coming to the cell-block approach (/loc -3, -513, -10). Defeat him there." :
		state.leader ? "Protect Osargen through the three escape checkpoints. Hail him to take over; return to the entrance (/loc -16, 88, 4)." :
		"Hail Osargen in his cell (/loc -52, -546, -10) and choose Lead the way. Protect him back to the entrance.";
	c->Message(Chat::Yellow,"Prison Break: %s",next);
}
NPC *Actor(uint32_t type,const Policy::Point &p,const char *name,const std::string &token) {
	const auto source=content_db.LoadNPCTypesData(type);
	if (!source) { throw std::runtime_error("High Keep actor definition unavailable."); }
	auto data=new NPCType(*source);
	strn0cpy(data->name,name,sizeof(data->name)); data->loottable_id=0; data->exp_mod=0;
	data->npc_id=0; // no stock NPC quests, faction hits, hunt credit or loot generation
	data->npc_spells_id=0; data->npc_spells_effects_id=0; data->emoteid=0;
	data->merchanttype=0; data->npc_faction_id=0; data->special_abilities[0]=0;
	if (type==6051) { data->current_hp=6000; data->max_hp=6000; data->hp_regen=0; data->hp_regen_per_second=0; }
	auto n=new NPC(data,nullptr,Position(p),GravityBehavior::Water); n->GiveNPCTypeData(data);
	n->SetEntityVariable("highkeep-run",current.id); n->SetEntityVariable("highkeep-attempt",token);
	n->SetEntityVariable("highkeep-role",type==6051 ? "prisoner" : "guard");
	n->SetSpecialAbility(SpecialAbility::CharmImmunity,1);
	n->SetSpecialAbility(SpecialAbility::FleeingImmunity,1);
	if (type==6051) {
		n->SetOOCRegen(0);
		n->SetSpecialAbility(SpecialAbility::AllowBeneficial,1);
		n->SetSpecialAbility(SpecialAbility::NPCDamageImmunity,1);
		n->SetSpecialAbility(SpecialAbility::DisableMelee,1);
		n->SetSpecialAbility(SpecialAbility::AggroImmunity,1);
	}
	entity_list.AddNPC(n,true,true); return n;
}
void ClearAttempt(uint32_t dying=0) {
	for (auto id:state.enemies) {
		auto n=entity_list.GetNPCByID(id);
		if (n && id!=dying && n->GetEntityVariable("highkeep-attempt")==state.token) { n->Depop(); }
	}
	auto n=entity_list.GetNPCByID(state.prisoner);
	if (Prisoner(n)) {
		entity_list.RemoveFromHateLists(n); entity_list.RemoveFromTargets(n);
		if (n->GetID()!=dying) { n->Depop(); }
	}
	state.enemies.clear(); state.prisoner=0; state.leader=0; state.wave=0; state.cleared=0;
	state.absent=0; state.token.clear(); state.retry=Now()+20;
}
void Fail(uint32_t dying=0) {
	ClearAttempt(dying);
	Shout("Jail Clerk Maryl","The escape has failed! Osargen is being returned to his cell. You can reach him again in twenty seconds.");
}
bool Death(NPC *n) {
	if (!Active()) { return true; }
	try { if (Guard(n)) { Alarm(); } }
	catch (const std::exception &e) { healthy=false; LogError("High Keep alarm persistence failed [{}]",e.what()); return false; }
	if (Prisoner(n)) { Fail(n->GetID()); return true; }
	if (n->GetEntityVariable("highkeep-attempt")==state.token && state.enemies.erase(n->GetID())) {
		if (state.enemies.empty()) { state.cleared=state.wave; Shout("Osargen","They're down! Stay close; let's keep moving toward the entrance!"); }
	}
	return true;
}
void BossDeath(const Boss *b) {
	if (!Active() || !b) { return; }
	if (b->objective==2) { Shout("Captain Bosec","Boshinko has fallen! Hold the prison stairs below the main floor!"); }
	else if (b->objective==1) { Shout("Dyrna Nlith","You may have the stairs, but this prison block is mine!"); }
	else if (b->objective==3) { Shout("Carson McCabe","Enough! I'll meet these intruders at the cells myself. Nobody takes my prisoner!"); }
	else if (b->objective==4) { Shout("Osargen","McCabe is down! Over here, in the cell! Hail me and I'll follow you out!"); }
	for (const auto &entry:entity_list.GetClientList()) { Status(entry.second); }
}
void Layout(std::vector<Spawn2Repository::Spawn2> &spawns) {
	if (!Active()) { return; }
	spawns.erase(std::remove_if(spawns.begin(),spawns.end(),[](const auto &s) {
		return s.id==10109 || s.id==10210 || s.id==10132 || s.id==10156;
	}),spawns.end());
	for (auto &s:spawns) {
		const Policy::Point *p=s.id==10145 ? &Policy::Boshinko : s.id==10117 ? &Policy::McCabe : nullptr;
		if (p) { s.x=p->x; s.y=p->y; s.z=p->z; s.heading=p->h; s.pathgrid=0; }
	}
}
void Complete(NPC *prisoner) {
	std::vector<Client *> completed;
	Transaction tx; auto run=ReadRun("r.run_id="+Q(current.id),true);
	if (run.id.empty() || run.expiry<=Now()) { throw std::runtime_error("Inactive rescue completion."); }
	for (const auto &entry:entity_list.GetClientList()) {
		auto c=entry.second;
		if (!Live(c) || DistanceSquared(c->GetPosition(),prisoner->GetPosition())>100.0f*100.0f) { continue; }
		auto r=Query(fmt::format("UPDATE nightcap_dungeon_members m SET completed_at={} WHERE run_id={} AND character_id={} AND completed_at=0 AND "
			"(SELECT COUNT(*) FROM nightcap_dungeon_kills k WHERE k.run_id=m.run_id AND k.character_id=m.character_id)=4",Now(),Q(run.id),c->CharacterID()));
		if (r.RowsAffected()==1) { completed.push_back(c); }
	}
	Query("UPDATE nightcap_highkeep_runs SET rescued_at="+std::to_string(Now())+" WHERE run_id="+Q(run.id));
	tx.Commit(); state.rescued=true;
	Shout("Osargen","Fresh air! You came for a prisoner and stood with me all the way. I won't forget this. We made it!");
	for (auto c:completed) {
		Journal(c); c->Message(Chat::Yellow,"Prison Break complete: Osargen is safe. Your personal dungeon reward is earned.");
		try { Claim(c,true); } catch (const std::exception &e) { LogError("High Keep reward remains pending [{}]",e.what()); }
	}
	ClearAttempt();
}
bool Action(Client *c,NPC *n,const std::string &text) {
	if (!Active() || !n || n->GetEntityVariable("highkeep-run")!=current.id || (n->GetID()!=state.gate && !Prisoner(n))) { return false; }
	if (!healthy || current.expiry<=Now() || !Live(c) || DistanceSquared(c->GetPosition(),n->GetPosition())>50.0f*50.0f) { return true; }
	try {
		if (!Vigil::Member(current,c)) { return true; }
		if (n->GetID()==state.gate && n->GetEntityVariable("highkeep-run")==current.id) {
			if (state.alarm) { Status(c); return true; }
			auto &d=state.dialogue[c->CharacterID()];
			if (Policy::Converse(d,text,Now())) { Alarm(); n->AddToHateList(c,100); }
			else if (d.step==2) { c->Message(Chat::White,"Gate Sergeant says, 'Relief? Your names aren't on my roster. Whose orders?' %s",Saylink::Silent("see osargen","We're here to see Osargen").c_str()); }
			else {
				if (!d.step) { Policy::Converse(d,"hail",Now()); }
				c->Message(Chat::White,"Gate Sergeant says, 'Halt. The prison is closed. State your business.' %s",Saylink::Silent("relief detail","We're the relief detail").c_str());
			}
			return true;
		}
		if (state.rescued || objectives.size()!=4 || !state.alarm) { Status(c); return true; }
		if (text!="lead the way") {
			c->Message(Chat::White,"Osargen says, 'Get me back to the entrance. I can follow you, but you'll have to protect me. Stay close and clear each guard wave. If we become separated, hail me again.' %s",Saylink::Silent("lead the way","Lead the way").c_str()); return true;
		}
		if (c->IsEngaged() || c->IsCasting()) { c->Message(Chat::Yellow,"Clear the guards before taking the lead."); return true; }
		state.leader=c->CharacterID(); state.absent=0; n->SetFollowID(c->GetID()); n->SetFollowDistance(100); n->SetFollowCanRun(true);
		n->SetSpecialAbility(SpecialAbility::NPCDamageImmunity,0);
		Shout("Osargen","I'm with you! Through the cell-block approach, past Bosec's stairs, and back to the gate. Keep the guards off me!");
		return true;
	} catch (const std::exception &e) { healthy=false; LogError("High Keep action suspended [{}]",e.what()); c->Message(Chat::Yellow,"The prison break is suspended because its state could not be saved."); return true; }
}
void Tick() {
	if (!Active() || state.tick>=Now()) { return; } state.tick=Now();
	if (!healthy || current.expiry<=Now()) { ClearAttempt(); return; }
	try {
		auto gate=entity_list.GetNPCByID(state.gate);
		if (!state.alarm && (!gate || gate->GetEntityVariable("highkeep-run")!=current.id)) { state.gate=Actor(6005,Policy::Gate,"Gate_Sergeant","")->GetID(); }
		if (!state.rescued && !state.prisoner && state.retry<=Now()) {
			state.token=NightcapLoot::NewDropID(); state.prisoner=Actor(6051,Policy::Cell,"Osargen",state.token)->GetID();
		}
		auto prisoner=entity_list.GetNPCByID(state.prisoner);
		if (state.prisoner && (!Prisoner(prisoner) || prisoner->GetHP()<=0)) { Fail(); return; }
		for (const auto &entry:entity_list.GetNPCList()) {
			auto n=entry.second;
			if (!Guard(n) || !n->IsEngaged()) { continue; }
			auto owner=Controller(n->GetTarget());
			if (owner && owner->IsClient()) { Alarm(); }
			if (n->GetEntityVariable("highkeep-called")!=current.id) {
				n->SetEntityVariable("highkeep-called",current.id);
				if (n->GetNPCTypeID()==6034) { Shout("Captain Bosec","Intruders at the prison stairs! Protect the cell block!"); }
				else if (n->GetNPCTypeID()==6047) { Shout("Dyrna Nlith","You will not free my prisoners!"); }
				else if (n->GetNPCTypeID()==6181) { Shout("Carson McCabe","Osargen knows too much. Kill the intruders before they open that cell!"); }
				else if (n->GetNPCTypeID()==6042) { Shout("Captain Boshinko","Sound the alarm! Nobody gets past the entrance passage!"); }
			}
		}
		if (!state.leader) { return; }
		if (!Prisoner(prisoner) || prisoner->GetHP()<=0) { Fail(); return; }
		auto leader=entity_list.GetClientByCharID(state.leader);
		const bool together=Live(leader) && DistanceSquared(leader->GetPosition(),prisoner->GetPosition())<=100.0f*100.0f;
		if (!together) {
			Pause(prisoner);
			if (!state.absent) { state.absent=Now(); Shout("Osargen","Wait! I can't follow you from here. Come back, or have a companion hail me to lead!"); }
			if (Now()-state.absent>=90) { Fail(); return; }
		} else { state.absent=0; prisoner->SetFollowID(leader->GetID()); }
		for (auto id:state.enemies) {
			auto n=entity_list.GetNPCByID(id);
			if (!n || n->GetEntityVariable("highkeep-attempt")!=state.token) { Fail(); return; }
		}
		if (!together) { return; }
		// Stop at each ambush until it is defeated. Never teleport through terrain.
		if (!state.enemies.empty()) { Pause(prisoner); }
		else if (state.wave<3 && DistanceSquared(prisoner->GetPosition(),Position(Policy::Checkpoints[state.wave]))<=60.0f*60.0f) {
			const auto p=Policy::Checkpoints[state.wave]; ++state.wave;
			Shout("Keep Pursuer","There! The prisoner is escaping! Cut him down!");
			for (unsigned i=0;i<2;++i) {
				auto n=Actor(6034,p,"Keep_Pursuer",state.token); state.enemies.insert(n->GetID()); n->AddToHateList(prisoner,100);
			}
			Pause(prisoner);
		}
		bool safe=state.enemies.empty();
		for (const auto &entry:entity_list.GetNPCList()) {
			auto n=entry.second;
			if (!Guard(n) || n->GetHP()<=0 || DistanceSquared(n->GetPosition(),prisoner->GetPosition())>70.0f*70.0f || !n->CheckLosFN(prisoner)) { continue; }
			if (!n->IsEngaged()) { n->AddToHateList(prisoner,50); }
			if (n->IsEngaged()) { safe=false; }
		}
		if (Policy::CanExtract(state.cleared,DistanceSquared(prisoner->GetPosition(),Position(Policy::Entrance))<=25.0f*25.0f,together,safe)) { Complete(prisoner); }
	} catch (const std::exception &e) { healthy=false; ClearAttempt(); LogError("High Keep rescue suspended [{}]",e.what()); }
}
}

bool HighkeepSay(Client *c,NPC *n,const std::string &text) { return Highkeep::Action(c,n,Strings::ToLower(text)); }
int HighkeepFaction(Mob *subject,Mob *observer) {
	if (!Highkeep::Active() || !subject || !observer) { return -1; }
	if (subject->IsClient() && Highkeep::Prisoner(observer)) { return FACTION_ALLY; }
	const auto owner=Highkeep::Controller(subject);
	if (Highkeep::Guard(observer) && ((owner && owner->IsClient()) || Highkeep::Prisoner(subject))) {
		if (Highkeep::Prisoner(subject) && !Highkeep::state.leader) { return FACTION_INDIFFERENTLY; }
		return Highkeep::state.alarm ? FACTION_SCOWLS : FACTION_INDIFFERENTLY;
	}
	return -1;
}
bool HighkeepProtected(Mob *attacker,Mob *target) {
	const auto owner=Highkeep::Controller(attacker);
	return Highkeep::Prisoner(target) && owner && owner->IsClient();
}
bool HighkeepNoFaction(Mob *npc) { return Highkeep::Active() && Highkeep::Guard(npc); }
bool HighkeepHealTarget(Mob *npc) { return Highkeep::Prisoner(npc); }
bool HighkeepTransient(Mob *npc) {
	return Highkeep::Active() && npc && npc->GetEntityVariable("highkeep-run")==current.id &&
		(npc->GetEntityVariable("highkeep-role")=="guard" || npc->GetEntityVariable("highkeep-role")=="prisoner");
}
