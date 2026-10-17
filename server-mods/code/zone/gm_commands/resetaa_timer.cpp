#include "zone/client.h"

void command_resetaa_timer(Client *c, const Seperator *sep)
{
	if (!sep->argnum) {
		c->Message(Chat::White, "Usage: #resetaa_timer all - Reset all Alternate Advancement timers");
		c->Message(Chat::White, "Usage: #resetaa_timer [AA Rank ID] - Reset only that AA family's timer");
		return;
	}
	auto *target = c->GetTarget() && c->GetTarget()->IsClient() ? c->GetTarget()->CastToClient() : c;
	if (!strcasecmp(sep->arg[1], "all")) {
		target->ResetAlternateAdvancementTimers();
		c->Message(Chat::White, "Reset all Alternate Advancement timers.");
	} else if (sep->IsNumber(1)) {
		const int rank_id = Strings::ToInt(sep->arg[1]);
		auto *rank = zone->GetAlternateAdvancementRank(rank_id);
		if (!rank || !rank->base_ability) {
			c->Message(Chat::Red, "Unknown AA rank ID.");
			return;
		}
		target->ResetAlternateAdvancementTimer(rank_id);
		c->Message(Chat::White, "Reset cooldown for AA rank %d's family.", rank_id);
	}
}
