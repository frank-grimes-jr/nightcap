// Pinned unchanged upstream helpers from retained source:
// /tmp/nightcap-chapterhouse-v1/source/zone, authenticated 2026-10-24.
// entity.cpp SHA-256 dbb2a48464f7038996a4f7f9c282ceb7c6a5ee31ba27708279156805b8b5ee4e
// mob_ai.cpp SHA-256 54d4810d70bfcb3b207a3c7f7bd6c147762a4b7f4a3caace401f3fd1fd747e47
// Both full files matched the retained source and local upstream byte-for-byte.
// These helpers are not tracked in server-mods. Lifecycle and feign mutators
// are always extracted from current tracked source by the Python test.
void EntityList::RemoveFromTargets(Mob *mob, bool RemoveFromXTargets)
{
	auto it = mob_list.begin();
	while (it != mob_list.end()) {
		Mob *m = it->second;
		++it;

		if (!m) {
			continue;
		}

		if (RemoveFromXTargets && mob) {
			if (m->IsClient() && (mob->CheckAggro(m) || mob->IsOnFeignMemory(m))) {
				m->CastToClient()->RemoveXTarget(mob, false);
			// FadingMemories calls this function passing the client.
			} else if (mob->IsClient() && (m->CheckAggro(mob) || m->IsOnFeignMemory(mob))) {
				mob->CastToClient()->RemoveXTarget(m, false);
			}
		}

		m->RemoveFromHateList(mob);
		m->RemoveFromRampageList(mob);
	}
}

void EntityList::ClearZoneFeignAggro(Mob *targ)
{
	auto it = npc_list.begin();
	while (it != npc_list.end()) {
		it->second->RemoveFromFeignMemory(targ);
		if (targ && targ->IsClient()) {
			targ->CastToClient()->RemoveXTarget(it->second, false);
		}
		++it;
	}
}

void Mob::Replay() {
if (zone->CanDoCombat() && AI_feign_remember_timer->Check()) {
			// 6/14/06
			// Improved Feign Death Memory
			// check to see if any of our previous feigned targets have gotten up.
			std::set<uint32>::iterator remembered_feigned_mobid;
			remembered_feigned_mobid = feign_memory_list.begin();
			while (remembered_feigned_mobid != feign_memory_list.end()) {
				Mob *remembered_mob = entity_list.GetMob(*remembered_feigned_mobid);
				if (remembered_mob == nullptr || remembered_mob->IsCorpse()) {
					//they are gone now...
					remembered_feigned_mobid = feign_memory_list.erase(remembered_feigned_mobid);
				}
				else if (!remembered_mob->GetFeigned()) {
					AddToHateList(remembered_mob, 1);
					remembered_feigned_mobid = feign_memory_list.erase(remembered_feigned_mobid);
					break;
				}
				else {
					//they are still feigned, carry on...
					++remembered_feigned_mobid;
				}
			}
		}
}

// xtargetautohaters.cpp SHA-256 1a7ddf7276dff38825f4f9c2d53566b3014d3325f9fcfbb2462ff888a0b685cd
void XTargetAutoHaters::decrement_count(Mob *in)
{
	assert(in != nullptr);
	auto it = std::find_if(m_haters.begin(), m_haters.end(),
			       [&in](const HatersCount &c) { return c.spawn_id == in->GetID(); });

	// we are not on the list ... shouldn't happen
	if (it == m_haters.end())
		return;
	it->count--;
	if (it->count == 0) {
		m_haters.erase(it);
		if (m_client)
			m_client->SetDirtyAutoHaters();
		else if (m_group)
			m_group->SetDirtyAutoHaters();
		else if (m_raid)
			m_raid->SetDirtyAutoHaters();
	}
}
