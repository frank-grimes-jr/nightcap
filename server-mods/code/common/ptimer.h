/*	EQEMu: Everquest Server Emulator
	Copyright (C) 2001-2005 EQEMu Development Team (http://eqemu.org)

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; version 2 of the License.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY except by those people which sell it, which
	are required to give you total support for your newly bought product;
	without even the implied warranty of MERCHANTABILITY or FITNESS FOR
	A PARTICULAR PURPOSE. See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program; if not, write to the Free Software
	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
*/

#pragma once

#include "common/types.h"

#include <map>
#include <vector>

enum : int {	//values for pTimerType
	pTimerUnlinkedItemStart = 0x200000, // stable item identity; never truncate -item_id
	pTimerStartAdventureTimer = 1,
	pTimerSurnameChange = 2,
	pTimerFeignDeath = 3,
	pTimerSneak = 4,
	pTimerHide = 5,
	pTimerTaunt = 6,
	pTimerInstillDoubt = 7,
	pTimerFishing = 8,
	pTimerForaging = 9,
	pTimerMend = 10,
	pTimerTracking = 11,
	pTimerSenseTraps = 12,
	pTimerDisarmTraps = 13,
	pTimerDisciplineReuseStart = 0x300000,
	pTimerDisciplineReuseEnd = 0x300013, // all 20 native discipline groups, isolated from skills/spells
	pTimerUnlinkedDisciplineStart = 0x400000, // timer_id=-1: one clock per discipline spell
	pTimerUnlinkedDisciplineEnd = 0x40ffff,
	pTimerCombatAbility = 25,
	pTimerCombatAbility2 = 26, // RoF2+ Tiger Claw is unlinked from other monk skills, generic in case other classes ever need it
	pTimerBeggingPickPocket = 27,
	pTimerLinkedSpellReuseStart = 28,
	pTimerLinkedSpellReuseEnd = 48,
	pTimerClearXTarget = 50,

	pTimerShieldAbility = 86,

	pTimerLayHands = 87,		//these IDs are used by client too
	pTimerHarmTouch = 89,		//so dont change them

	pTimerItemStart = 100,
	pTimerItemEnd = 200, //I don't think any items would use one this high but hey, incase.
	// Nightcap: one persistent cooldown per basic Monk skill (start + skill ID).
	// Keep this range outside item, linked-spell, discipline and AA timer IDs.
	pTimerMonkCombatAbilityStart = 500,
	pTimerMonkCombatAbilityEnd = 599,
	pTimerPeqzoneReuse = 900,
	pTimerMercReuse = 901,
	pTimerRaidAugment = 903,
	pTimerMercSuspend = 902,
	pTimerAAStart = 0x100000,		// start + AA ability (family) ID; not a client timer slot
	pTimerAAEnd = 0x1fffff,
	pTimerAAEffectStart = 3001,	//AA effect timers
	pTimerAAEffectEnd	= 4999,

	pTimerSpellStart = 5000 // spell IDs are uint16; positive namespaces above cannot overlap
};

class Database;

// SQL timers.type is MEDIUMINT UNSIGNED. Keep namespaces inside its 24 bits.
typedef uint32 pTimerType;

class PersistentTimer {
public:
	static PersistentTimer *LoadTimer(Database *db, uint32 char_id, pTimerType type);

	PersistentTimer(uint32 char_id, pTimerType type, uint32 duration);
	PersistentTimer(uint32 char_id, pTimerType type, uint32 start_time, uint32 duration, bool enable);

	bool Expired(Database *db, bool iReset = true);
	void Start(uint32 set_timer_time=0);

	void SetTimer(uint32 set_timer_time=0);
	uint32 GetRemainingTime();
	inline void Enable() { enabled = true; }
	inline void Disable() { enabled = false; }
	inline const uint32 GetTimerTime() const { return timer_time; }
	inline const uint32 GetStartTime() const { return start_time; }
	inline const pTimerType GetType() const { return _type; }
	inline const uint32 GetReadyTimestamp() const { return start_time + timer_time; }

	inline bool Enabled() { return enabled; }

	bool Load(Database *db);
	bool Store(Database *db);
	bool Clear(Database *db);

protected:
	uint32 get_current_time();

	uint32	start_time;
	uint32	timer_time;
	bool	enabled;

	uint32 _char_id;
	pTimerType _type;
};

//a list of persistent timers for a specific character
class PTimerList {
public:
	PTimerList(uint32 char_id = 0);

	~PTimerList();

	bool Load(Database *db);
	bool Store(Database *db);
	bool Clear(Database *db);

	void Start(pTimerType type, uint32 duration);
	bool Expired(Database *db, pTimerType type, bool reset = true);
	void Clear(Database *db, pTimerType type);
	void Enable(pTimerType type);
	bool Enabled(pTimerType type);
	void Disable(pTimerType type);
	uint32 GetRemainingTime(pTimerType type);
	PersistentTimer *Get(pTimerType type);

	inline void SetCharID(uint32 char_id) { _char_id = char_id; }

	void ToVector(std::vector< std::pair<pTimerType, PersistentTimer *> > &out);

	//Clear a timer for a char not logged in
	//this is not defined on a char which is logged in!
	static bool ClearOffline(Database *db, uint32 char_id, pTimerType type);

	typedef std::map<pTimerType, PersistentTimer *>::iterator iterator;
	iterator begin() { return(_list.begin()); }
	iterator end() { return(_list.end()); }


	void AddTimer(pTimerType type, uint32 start_time, uint32 duration, bool enable);
protected:
	uint32 _char_id;

	std::map<pTimerType, PersistentTimer *> _list;
};
