#include "zone/client.h"
#include "zone/command.h"
#include "common/seperator.h"

void command_nightcapui(Client *c, const Seperator *sep)
{
	if (sep->argnum == 1 && !strcmp(sep->arg[1], "recommended")) {
		const bool first = c->EnableAARecommendations();
		c->RefreshNightcapUI();
		// A legacy refresh may have just started the throttle. Complete the
		// capability opt-in once; subsequent requests retain the native throttle.
		if (first) { c->SendAlternateAdvancementStats(); }
	} else if (sep->argnum == 1 && !strcmp(sep->arg[1], "refresh")) {
		c->RefreshNightcapUI();
	}
}

void command_nightcappet(Client *c, const Seperator *sep)
{
	c->HandlePetArmor(sep);
}
