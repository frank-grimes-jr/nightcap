#pragma once

#include "advanced_loot_protocol.h"
#include <algorithm>
#include <map>
#include <stdexcept>
#include <vector>

namespace NightcapLoot {
enum class Choice { None, Need, Greed, Pass };
enum class Distribution { Personal, Shared, Rolling, Awarded, FreeGrab, Left, Consumed, Quarantined, Expired };
enum class TransferResult { Declined, Delivered, Uncertain };

// One instance belongs to one physical corpse item, never merely to an item ID
// or reusable spawn ID. The adapter owns its lifetime and must recheck native
// corpse, range, inventory and quest restrictions in the transfer callback.
class DropPolicy {
	uint32_t master_ = 0, recipient_ = 0;
	uint64_t deadline_ = 0;
	Distribution state_ = Distribution::Shared;
	std::map<uint32_t, Choice> choices_;
	std::map<uint32_t, Filter> filters_;
	bool transferring_ = false;

	bool Terminal() const {
		return state_ == Distribution::Left || state_ == Distribution::Consumed ||
			state_ == Distribution::Quarantined || state_ == Distribution::Expired;
	}
	bool Eligible(uint32_t character) const {
		const auto it = filters_.find(character);
		return it != filters_.end() && it->second != Filter::Never;
	}
public:
	struct Checkpoint {
		uint32_t master = 0, recipient = 0;
		uint64_t remaining = 0;
		Distribution state = Distribution::Shared;
		std::map<uint32_t, Choice> choices;
		std::map<uint32_t, Filter> filters;
	};
	Checkpoint Save(uint64_t now) const {
		return {master_, recipient_, deadline_ > now ? deadline_ - now : 0, state_, choices_, filters_};
	}
	static DropPolicy Restore(const Checkpoint &s, uint64_t now) {
		DropPolicy policy(s.master, s.filters, s.state == Distribution::Personal);
		if (static_cast<unsigned>(s.state) > static_cast<unsigned>(Distribution::Expired) ||
			s.remaining > 60000 || now > UINT64_MAX - s.remaining || s.choices.size() != s.filters.size()) {
			throw std::invalid_argument("invalid loot checkpoint");
		}
		for (const auto &[id, choice] : s.choices) {
			if (!s.filters.count(id) || static_cast<unsigned>(choice) > static_cast<unsigned>(Choice::Pass)) {
				throw std::invalid_argument("invalid loot choice");
			}
		}
		if ((s.state == Distribution::Personal || s.state == Distribution::Awarded) ?
			!s.filters.count(s.recipient) : s.recipient != 0 && s.state != Distribution::Consumed && s.state != Distribution::Quarantined) {
			throw std::invalid_argument("invalid loot recipient");
		}
		if (s.state != Distribution::Rolling && s.remaining) { throw std::invalid_argument("invalid roll timer"); }
		policy.state_ = s.state; policy.recipient_ = s.recipient; policy.choices_ = s.choices;
		policy.deadline_ = s.state == Distribution::Rolling ? now + s.remaining : 0;
		return policy;
	}
	DropPolicy(uint32_t master, const std::map<uint32_t, Filter> &participants, bool personal)
		: master_(master), filters_(participants)
	{
		if (!master || !participants.count(master) || participants.empty() || participants.size() > 72 ||
			(personal && participants.size() != 1)) { throw std::invalid_argument("invalid loot roster"); }
		for (const auto &[character, filter] : participants) {
			if (!character || static_cast<uint32_t>(filter) > 4) { throw std::invalid_argument("invalid loot participant"); }
			choices_[character] = Choice::None;
		}
		state_ = personal ? Distribution::Personal : Distribution::Shared;
		recipient_ = personal ? master : 0;
	}
	Distribution State() const { return state_; }
	uint32_t Recipient() const { return recipient_; }
	uint32_t Master() const { return master_; }
	uint64_t Deadline() const { return deadline_; }
	bool HasParticipant(uint32_t character) const { return filters_.count(character) != 0; }
	Choice Selected(uint32_t character) const {
		const auto found = choices_.find(character);
		return found == choices_.end() ? Choice::None : found->second;
	}
	bool SetMaster(uint32_t character) {
		if (transferring_ || Terminal() || state_ == Distribution::Personal || !HasParticipant(character)) { return false; }
		// Native adapter alone chooses the replacement from current corpse rights.
		// Pending choices, deadlines and an existing award remain unchanged.
		master_ = character;
		return true;
	}

	bool UpdateFilter(uint32_t character, Filter filter) {
		if (transferring_ || Terminal() || !HasParticipant(character) || static_cast<uint32_t>(filter) > 4) { return false; }
		if (filters_.at(character) == filter) { return true; }
		filters_[character] = filter;
		if (state_ == Distribution::Rolling) {
			choices_[character] = filter == Filter::Never ? Choice::Pass : filter == Filter::AlwaysNeed ? Choice::Need :
				filter == Filter::AlwaysGreed ? Choice::Greed : Choice::None;
		}
		return true;
	}
	bool Assign(uint32_t actor, uint32_t character) {
		if (transferring_ || Terminal() || state_ == Distribution::Personal || actor != master_ || !Eligible(character)) { return false; }
		state_ = Distribution::Awarded; recipient_ = character; deadline_ = 0;
		return true;
	}
	bool OpenFreeGrab(uint32_t actor) {
		if (transferring_ || Terminal() || state_ == Distribution::Personal || actor != master_) { return false; }
		state_ = Distribution::FreeGrab; recipient_ = 0; deadline_ = 0;
		return true;
	}
	bool Leave(uint32_t actor) {
		if (transferring_ || Terminal()) { return false; }
		if (actor != master_ && !(state_ == Distribution::Awarded && actor == recipient_)) { return false; }
		// A declined shared award returns to the master's list, not to another
		// player's inventory. Leaving unassigned/shared loot is the master's act.
		state_ = state_ == Distribution::Awarded ? Distribution::Shared : Distribution::Left;
		recipient_ = 0; deadline_ = 0;
		return true;
	}
	bool StartRoll(uint32_t actor, uint64_t now) {
		if (transferring_ || Terminal() || state_ == Distribution::Personal || actor != master_ ||
			now > UINT64_MAX - 60000) { return false; }
		state_ = Distribution::Rolling; recipient_ = 0; deadline_ = now + 60000;
		for (auto &[character, choice] : choices_) {
			const auto filter = filters_.at(character);
			choice = filter == Filter::Never ? Choice::Pass : filter == Filter::AlwaysNeed ? Choice::Need :
				filter == Filter::AlwaysGreed ? Choice::Greed : Choice::None;
		}
		return true;
	}
	bool Choose(uint32_t character, Choice choice, uint64_t now) {
		if (transferring_ || state_ != Distribution::Rolling || now >= deadline_ || !HasParticipant(character) ||
			(choice != Choice::Need && choice != Choice::Greed && choice != Choice::Pass) ||
			(!Eligible(character) && choice != Choice::Pass)) { return false; }
		choices_[character] = choice;
		return true;
	}
	// current_rights excludes members who lost corpse access. random_index must
	// supply a uniform index in [0,count); no modulo reduction of random numbers.
	template<class Rights, class RandomIndex>
	bool Resolve(uint64_t now, Rights current_rights, RandomIndex random_index) {
		if (transferring_ || state_ != Distribution::Rolling || now < deadline_) { return false; }
		std::vector<uint32_t> need, greed;
		for (const auto &[character, choice] : choices_) {
			if (!Eligible(character) || !current_rights(character)) { continue; }
			if (choice == Choice::Need) { need.push_back(character); }
			if (choice == Choice::Greed) { greed.push_back(character); }
		}
		const auto &pool = need.empty() ? greed : need;
		if (pool.empty()) { state_ = Distribution::Left; recipient_ = 0; deadline_ = 0; return true; }
		const std::size_t index = random_index(pool.size());
		if (index >= pool.size()) { return false; }
		recipient_ = pool[index]; state_ = Distribution::Awarded; deadline_ = 0;
		return true;
	}
	bool CanTake(uint32_t character) const {
		if (transferring_ || !Eligible(character)) { return false; }
		return state_ == Distribution::FreeGrab ||
			((state_ == Distribution::Personal || state_ == Distribution::Awarded) && recipient_ == character);
	}
	bool ShouldAutoTake(uint32_t character, bool enabled, bool apply_filters, bool auto_all) const {
		if (!enabled || !CanTake(character) || state_ == Distribution::FreeGrab) { return false; }
		const auto filter = filters_.at(character);
		return auto_all || (apply_filters && (filter == Filter::AlwaysTake || filter == Filter::AlwaysNeed || filter == Filter::AlwaysGreed));
	}
	template<class Transfer>
	TransferResult Take(uint32_t character, Transfer transfer) {
		if (!CanTake(character)) { return TransferResult::Declined; }
		transferring_ = true;
		TransferResult result = TransferResult::Uncertain;
		try { result = transfer(); }
		catch (...) { state_ = Distribution::Quarantined; transferring_ = false; throw; }
		transferring_ = false;
		if (result == TransferResult::Delivered) { state_ = Distribution::Consumed; }
		else if (result != TransferResult::Declined) { state_ = Distribution::Quarantined; result = TransferResult::Uncertain; }
		return result;
	}
	void Invalidate() {
		if (!transferring_ && state_ != Distribution::Consumed && state_ != Distribution::Quarantined) { state_ = Distribution::Expired; }
	}
};
}
