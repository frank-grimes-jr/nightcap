// Included inside NightcapDungeon: shares the native run identity, transaction,
// participation and inventory receipt adapters. Never loaded as a quest plugin.
namespace Vigil {
using Event=NightcapVigil::Event;
constexpr unsigned Task=NightcapVigil::Task;
struct Progress { unsigned mask=0, accepted=0, completed=0; std::string receipt; };
bool Installed(bool require_enabled=true) {
	auto r=database.QueryDatabase(std::string("SELECT enabled FROM nightcap_vigil_state WHERE id=1 AND revision=2026102301"),false);
	return r.Success() && r.RowCount()==1 && (!require_enabled || std::string(r.begin()[0])=="1") && StorageReady();
}
Progress Read(uint32_t character, bool lock=false) {
	auto r=Query(fmt::format("SELECT progress,accepted_at,completed_at,helmet_drop_id FROM nightcap_vigil_characters WHERE character_id={}{}",character,lock ? " FOR UPDATE" : ""));
	if (!r.RowCount()) { return {}; }
	auto row=r.begin(); return {Strings::ToUnsignedInt(row[0]),Strings::ToUnsignedInt(row[1]),Strings::ToUnsignedInt(row[2]),row[3]};
}
bool HasRoom(Client *c) {
	auto state=c->GetTaskState(); if (!state) { return false; }
	if (state->IsTaskActive(Task)) { return true; }
	for (int slot=0;slot<MAXACTIVEQUESTS;++slot) { if (!state->GetActiveTaskID(slot)) { return true; } }
	return false;
}
bool Qualifies(Client *c) { return c && NightcapVigil::Eligible(c->GetLevel(),c->GetClassMask()); }
bool HasJournalRoom(Client *c,unsigned dungeon_task) {
	auto state=c->GetTaskState(); if (!state) { return false; }
	const auto p=Read(c->CharacterID());
	unsigned needed=state->IsTaskActive(dungeon_task) ? 0 : 1;
	// completed_at records entitlement; a full inventory can still leave delivery pending.
	const bool delivered=p.completed && Query(fmt::format("SELECT character_id FROM character_advloot_claims WHERE drop_id={} AND character_id={}",Q(p.receipt),c->CharacterID())).RowCount()==1;
	if (p.accepted && !delivered && !state->IsTaskActive(Task)) { ++needed; }
	unsigned free=0;
	for (int slot=0;slot<MAXACTIVEQUESTS;++slot) { if (!state->GetActiveTaskID(slot)) { ++free; } }
	return free>=needed;
}
void Project(Client *c) {
	if (!c || !c->GetTaskState() || !Installed(false)) { return; }
	const auto p=Read(c->CharacterID()); if (!p.accepted) { return; }
	auto state=c->GetTaskState();
	if (p.completed) {
		auto delivered=Query(fmt::format("SELECT character_id FROM character_advloot_claims WHERE drop_id={} AND character_id={}",Q(p.receipt),c->CharacterID()));
		if (delivered.RowCount() && state->RecordCompletedTaskFromLedger(c,Task,p.completed)) {
			if (state->IsTaskActive(Task)) { state->RemoveTaskByTaskID(c,Task); }
			return;
		}
	}
	if (!state->IsTaskActive(Task)) {
		if (!HasRoom(c)) { c->Message(Chat::Yellow,"Make room in Tasks, then ask Camil or a Chapterhouse service for Status. Your Vigil progress is safe."); return; }
		state->AcceptNewTask(c,Task,0,p.accepted);
	}
	for (unsigned i=0;i<13;++i) {
		const int actual=state->GetTaskActivityDoneCountFromTaskID(Task,i);
		if ((p.mask&(1u<<i)) && !actual) { state->UpdateTaskActivity(c,Task,i,1,true); }
		if (!(p.mask&(1u<<i)) && actual>0) { state->ResetTaskActivity(c,Task,i); }
	}
	// Last row is never credited: only the persisted helmet receipt owns completion.
}
bool Member(const Run &run, Client *c) {
	return !run.id.empty() && run.expiry>Now() && Query(fmt::format(
		"SELECT character_id FROM nightcap_dungeon_members WHERE run_id={} AND character_id={}",Q(run.id),c->CharacterID())).RowCount()==1;
}
bool Advance(Client *c, Event event) {
	if (!Qualifies(c)) { return false; }
	auto p=Read(c->CharacterID(),true);
	if (!p.accepted || p.completed || !NightcapVigil::Advance(p.mask,event)) { return false; }
	Query(fmt::format("UPDATE nightcap_vigil_characters SET progress={} WHERE character_id={}",p.mask,c->CharacterID())); return true;
}
void Reconcile(Client *c, const Run &run) {
	if (!Member(run,c)) { return; }
	// Personal recorded kills can precede an interaction. Never give retrospective
	// credit from the run-wide (character 0) checklist or another player's kills.
	auto rows=Query(fmt::format("SELECT boss_id FROM nightcap_dungeon_kills WHERE run_id={} AND character_id={} ORDER BY boss_id",Q(run.id),c->CharacterID()));
	for (auto r:rows) {
		const auto id=Strings::ToUnsignedInt(r[0]);
		if (id>=1 && id<=4) { Advance(c,static_cast<Event>(id==1 ? 1 : id==2 ? 6 : id==3 ? 10 : 11)); }
	}
}
void Connected(Client *c) {
	if (!Installed(false)) { return; }
	try {
		if (Installed() && current.dungeon && current.dungeon->zone==760 && Member(current,c)) {
			Transaction tx; auto run=ReadRun("r.run_id="+Q(current.id),true);
			if (run.id.empty() || run.expiry<=Now()) { return; }
			Advance(c,Event::Enter); Reconcile(c,run); tx.Commit();
		}
		Project(c);
	} catch (const std::exception &e) { LogError("Vigil journal recovery pending [{}]",e.what()); }
}
void Configure(int task_id,TaskInformation &task) {
	if (task_id!=int(Task)) { return; }
	for (int i=0;i<task.activity_count;++i) { task.activity_information[i].goal_method=METHODQUEST; }
}
struct Defense {
	std::string run, token;
	uint32_t guardian=0;
	unsigned wave=0;
	uint64_t expires=0, next_wave=0;
	std::set<uint32_t> enemies, participants;
} defense;
void ClearDefense() {
	for (auto id:defense.enemies) {
		auto n=entity_list.GetNPCByID(id);
		if (n && n->GetEntityVariable("vigil-attempt")==defense.token) { n->Depop(); }
	}
	auto n=entity_list.GetNPCByID(defense.guardian);
	if (n && n->GetEntityVariable("vigil-attempt")==defense.token) { n->Depop(); }
	defense={};
}
NPC *SpawnDefense(uint32_t type,const glm::vec4 &position) {
	const auto definition=content_db.LoadNPCTypesData(type);
	if (!definition) { throw std::runtime_error("Vigil encounter definition unavailable."); }
	auto n=new NPC(definition,nullptr,position,GravityBehavior::Water);
	n->SetEntityVariable("vigil-attempt",defense.token);
	entity_list.AddNPC(n,true,true); return n;
}
void NextWave() {
	auto guardian=entity_list.GetNPCByID(defense.guardian);
	if (!guardian || guardian->GetHP()<=0 || guardian->GetEntityVariable("vigil-attempt")!=defense.token) {
		ClearDefense(); throw std::runtime_error("Elowen's prayer was broken. Begin the vigil again.");
	}
	++defense.wave;
	defense.next_wave=Now()+15;
	for (int side:{-1,1}) {
		auto position=guardian->GetPosition(); position.x+=side*8.0f;
		auto enemy=SpawnDefense(998836,position);
		defense.enemies.insert(enemy->GetID()); enemy->AddToHateList(guardian,100);
	}
	guardian->Say("Hold the light! Wave %u of three approaches.",defense.wave);
}
void Tick() {
	if (defense.run.empty()) { return; }
	auto guardian=entity_list.GetNPCByID(defense.guardian);
	bool present=false;
	if (guardian) {
		for (auto id:defense.participants) {
			auto c=entity_list.GetClientByCharID(id);
			if (c && c->Connected() && !c->IsDead() && DistanceSquared(c->GetPosition(),guardian->GetPosition())<=200.0f*200.0f) { present=true; }
		}
	}
	if (!healthy || defense.expires<Now() || defense.run!=current.id || current.expiry<=Now() ||
		!guardian || guardian->GetHP()<=0 || guardian->GetEntityVariable("vigil-attempt")!=defense.token || !present) { ClearDefense(); return; }
	if (defense.enemies.empty() && defense.wave<3 && Now()>=defense.next_wave) {
		try { NextWave(); } catch (const std::exception &e) { ClearDefense(); LogError("Vigil wave reset [{}]",e.what()); }
	}
}
bool DynamicDeath(NPC *npc, Mob *killer, bool owned) {
	if (defense.run.empty() || npc->GetEntityVariable("vigil-attempt")!=defense.token) { return true; }
	if (defense.expires<Now() || defense.run!=current.id || npc->GetID()==defense.guardian) { ClearDefense(); return true; }
	if (!defense.enemies.count(npc->GetID())) { return true; }
	try {
		auto guardian=entity_list.GetNPCByID(defense.guardian);
		if (owned || !guardian || guardian->GetHP()<=0 || guardian->GetEntityVariable("vigil-attempt")!=defense.token) {
			ClearDefense(); return true;
		}
		const auto credit=Credit(npc,killer);
		bool participant=false;
		for (auto c:credit) { if (defense.participants.count(c->CharacterID()) && !c->IsDead()) { participant=true; } }
		if (!participant) { ClearDefense(); return true; }
		defense.enemies.erase(npc->GetID());
		if (!defense.enemies.empty()) { return true; }
		if (defense.wave<3) { return true; } // Native zone tick enforces the wave cadence.
		Transaction tx; auto run=ReadRun("r.run_id="+Q(current.id),true);
		if (run.id.empty() || run.expiry<=Now()) { throw std::runtime_error("Vigil run expired."); }
		for (auto c:credit) {
			if (defense.participants.count(c->CharacterID()) && !c->IsDead() && Member(run,c)) { Advance(c,Event::Vigil); Reconcile(c,run); }
		}
		tx.Commit(); ClearDefense();
		for (auto c:credit) { Project(c); }
		return true;
	} catch (const std::exception &e) {
		healthy=false; ClearDefense(); LogError("Vigil defense suspended [{}]",e.what()); return false;
	}
}
void Death(const Run &run, const std::vector<Client *> &credit) {
	if (run.dungeon->zone!=760 || !Installed()) { return; }
	for (auto c:credit) { if (!c->IsDead()) { Reconcile(c,run); } }
}
void ClaimHelmet(Client *c) {
	if (!Qualifies(c) || c->IsDead() || c->IsEngaged() || c->IsCasting() || c->IsAIControlled() ||
		(c->trade && c->trade->With()) || c->GetTradeskillObject() || c->IsLooting() ||
		c->GetMerchantSessionEntityID() || !c->GetInv().CursorEmpty()) {
		c->Message(Chat::Yellow,"Finish other interactions, hold Paladin at level 50, and empty your cursor before claiming."); return;
	}
	if (!StorageReady()) { throw std::runtime_error("Reward storage unavailable."); }
	Transaction tx; auto p=Read(c->CharacterID(),true);
	if (!NightcapVigil::Ready(p.mask)) { c->Message(Chat::White,"Finish the Vigil objectives in Tasks before returning for your helm."); return; }
	if (!NightcapLoot::ValidDropID(p.receipt)) { throw std::runtime_error("Invalid Vigil entitlement."); }
	if (!p.completed) { Query(fmt::format("UPDATE nightcap_vigil_characters SET completed_at={} WHERE character_id={}",Now(),c->CharacterID())); }
	tx.Commit();
	auto prior=Query(fmt::format("SELECT character_id FROM character_advloot_claims WHERE drop_id={}",Q(p.receipt)));
	if (prior.RowCount()) {
		if (Strings::ToUnsignedInt(prior.begin()[0])!=c->CharacterID()) { throw std::runtime_error("Vigil receipt ownership mismatch."); }
		c->Message(Chat::White,"You have already received the Winged Helm of the Dawn."); Project(c); return;
	}
	std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(NightcapVigil::Helmet,1));
	if (!item) { throw std::runtime_error("The helm is pending until the matching item cache is available."); }
	const auto delivered=NightcapLoot::ReceiveItem(c,*item,{p.receipt});
	if (delivered==NightcapLoot::TransferResult::Delivered) { c->Message(Chat::White,"Camil entrusts you with the Winged Helm of the Dawn."); Project(c); }
	else if (delivered!=NightcapLoot::TransferResult::Uncertain) { c->Message(Chat::Yellow,"Your helm remains with Camil. Make inventory space and choose Claim Helm again."); }
}
bool Action(Client *c,NPC *npc,const std::string &action) {
	const auto type=npc->GetNPCTypeID();
	const bool camil=type==999521 && zone->GetZoneID()==22 && !zone->GetInstanceID();
	const bool service=type>=998827 && type<=998834;
	if (!camil && !service) { return false; }
	const bool hail=action=="hail" || action.rfind("hail,",0)==0 || action.rfind("hail ",0)==0;
	if (camil && !hail && action!="the vigil" && action!="accept vigil" && action!="vigil status" && action!="claim helm") { return false; }
	if (!c || !c->Connected() || !c->ClientDataLoaded() || c->IsDead() || c->IsAIControlled() ||
		DistanceSquared(c->GetPosition(),npc->GetPosition())>50.0f*50.0f) { return true; }
	try {
		if (!Installed(false)) { if (camil && hail) { return false; } c->Message(Chat::Yellow,"The Vigil expedition is not available yet."); return true; }
		if (camil) {
			if (action=="accept vigil") {
				if (!Installed()) { c->Message(Chat::Yellow,"New Vigil expeditions are paused. Earned helms remain claimable."); return true; }
				if (!Qualifies(c)) { c->Message(Chat::Yellow,"The Vigil requires level 50 and Paladin in any class slot."); return true; }
				if (!HasRoom(c)) { c->Message(Chat::Yellow,"Make room in Tasks before accepting the Vigil."); return true; }
				Transaction tx;
				if (!Read(c->CharacterID()).accepted && !Personal(c->CharacterID(),760).id.empty()) {
					c->Message(Chat::Yellow,"Leave and reset your existing Chapterhouse run before accepting the Vigil. Earlier kills cannot earn campaign credit."); return true;
				}
				Query(fmt::format("INSERT IGNORE INTO nightcap_vigil_characters(character_id,progress,accepted_at,completed_at,helmet_drop_id) VALUES ({},0,{},0,{})",c->CharacterID(),Now(),Q(NightcapLoot::NewDropID())));
				tx.Commit(); Project(c);
			} else if (action=="claim helm") { ClaimHelmet(c); }
			else {
				Project(c);
				c->Message(Chat::White,"I led the civilians to safety. Vaelen stayed, and bound our brothers to a watch that never ends. Take up %s, then meet the Chapterhouse Keeper near Befallen in West Commonlands. %s | %s",
					Saylink::Silent("accept vigil","The Vigil of the Dawn").c_str(),Saylink::Silent("vigil status","Vigil Status").c_str(),Saylink::Silent("claim helm","Claim Helm").c_str());
			}
			return true;
		}
		if (!Installed()) { c->Message(Chat::Yellow,"The Vigil encounter is paused."); return true; }
		if (!current.dungeon || current.dungeon->zone!=760 || !Member(current,c) || !Qualifies(c)) { return true; }
		if (c->IsEngaged() || c->IsCasting()) { c->Message(Chat::Yellow,"Finish combat before tending the sanctuary."); return true; }
		if (type==998827) {
			if (action!="begin vigil") { c->Message(Chat::White,"Read the three memorials, then %s. Protect my prayer from three waves; failure can be retried here.",Saylink::Silent("begin vigil","Begin Vigil").c_str()); Project(c); return true; }
			auto p=Read(c->CharacterID()); unsigned probe=p.mask;
			if (!p.accepted || !NightcapVigil::Advance(probe,Event::Vigil)) { Project(c); return true; }
			auto active_guardian=entity_list.GetNPCByID(defense.guardian);
			if (!defense.run.empty() && defense.expires>=Now() && active_guardian && active_guardian->GetHP()>0 && active_guardian->GetEntityVariable("vigil-attempt")==defense.token) { c->Message(Chat::Yellow,"A vigil is already underway."); return true; }
			ClearDefense(); defense.run=current.id; defense.token=NightcapLoot::NewDropID(); defense.expires=Now()+300;
			for (auto member:c->GetPartyMembers()) {
				if (!member || !Qualifies(member) || member->IsDead() || !Member(current,member) || DistanceSquared(member->GetPosition(),npc->GetPosition())>200.0f*200.0f) { continue; }
				auto progress=Read(member->CharacterID()); unsigned candidate=progress.mask;
				if (progress.accepted && NightcapVigil::Advance(candidate,Event::Vigil)) { defense.participants.insert(member->CharacterID()); }
			}
			defense.guardian=SpawnDefense(998835,npc->GetPosition())->GetID(); NextWave(); return true;
		}
		Event event=type<=998830 ? static_cast<Event>(2+type-998828) : type<=998833 ? static_cast<Event>(7+type-998831) : Event::Chapel;
		if (!hail && action!="tend") { return true; }
		Transaction tx; auto run=ReadRun("r.run_id="+Q(current.id),true);
		if (run.id.empty() || run.expiry<=Now()) { return true; }
		Reconcile(c,run); const bool advanced=Advance(c,event); Reconcile(c,run); tx.Commit();
		c->Message(Chat::White,advanced ? "The sanctuary answers. Your Vigil journal has been updated." : "Consult your Vigil journal; another duty must come first, or this duty is already complete.");
		Project(c); return true;
	} catch (const std::exception &e) { c->Message(Chat::Yellow,"The Vigil operation remains pending: %s",e.what()); LogError("Vigil operation failed [{}]",e.what()); return true; }
}
}
