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

// Exact unmodified native timer methods for the duration boundary fixture.
// Source: retained EQEmu common/ptimer.cpp, inspected 2026-10-17.
// Original file SHA256: e62d800263b87439d094ddbda0975caadc6ffcbcb8fb46dc3b34b9f05defbda5
// Native Start(0) restarts retained duration; expiry does not remove its object.
// When server-mods/code/common/ptimer.cpp exists, the test extracts it instead.

PersistentTimer::PersistentTimer(uint32 char_id, pTimerType type, uint32 in_timer_time) {
	_char_id = char_id;
	_type = type;

	timer_time = in_timer_time;
	start_time = get_current_time();
	if (timer_time == 0) {
		enabled = false;
	} else {
		enabled = true;
	}
#ifdef DEBUG_PTIMERS
	printf("New timer: char %lu of type %u at %lu for %lu seconds.\n", (unsigned long)_char_id, _type, (unsigned long)start_time, (unsigned long)timer_time);
#endif
}

bool PersistentTimer::Expired(Database *db, bool iReset) {
	uint32 current_time = get_current_time();
	if (current_time-start_time >= timer_time) {
		if (enabled && iReset) {
			start_time = current_time; // Reset timer
		} else if(enabled) {
			Clear(db);	//remove it from DB too
		}
		return(true);
	}

	return(false);
}

void PersistentTimer::Start(uint32 set_timer_time) {
	start_time = get_current_time();
	enabled = true;
	if (set_timer_time != 0) {
		timer_time = set_timer_time;
	}
#ifdef DEBUG_PTIMERS
	printf("Starting timer: char %lu of type %u at %lu for %lu seconds.\n", (unsigned long)_char_id, _type, (unsigned long)start_time, (unsigned long)timer_time);
#endif
}

uint32 PersistentTimer::GetRemainingTime() {
	if (enabled) {
		uint32 current_time = get_current_time();
		if (current_time-start_time > timer_time)
			return 0;
		else
			return (start_time + timer_time) - current_time;
	}
	else {
		return 0xFFFFFFFF;
	}
}

void PTimerList::Start(pTimerType type, uint32 duration) {
	if(_list.count(type) == 1 && _list[type] != nullptr) {
		_list[type]->Start(duration);
	} else {
		_list[type] = new PersistentTimer(_char_id, type, duration);
	}
}

void PTimerList::Clear(Database *db, pTimerType type) {
	if(_list.count(type) == 1) {
		if(_list[type] != nullptr) {
			_list[type]->Clear(db);
			delete _list[type];
		}
		_list.erase(type);
	}
}

bool PTimerList::Expired(Database *db, pTimerType type, bool reset) {
	if(_list.count(type) != 1)
		return(true);
	if(_list[type] == nullptr)
		return(true);
	return(_list[type]->Expired(db, reset));
}

uint32 PTimerList::GetRemainingTime(pTimerType type) {
	if(_list.count(type) != 1)
		return(0);
	if(_list[type] == nullptr)
		return(0);
	return(_list[type]->GetRemainingTime());
}

PersistentTimer *PTimerList::Get(pTimerType type) {
	if(_list.count(type) != 1)
		return(nullptr);
	return(_list[type]);
}
