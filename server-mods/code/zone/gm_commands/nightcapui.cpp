#include "zone/client.h"
#include "zone/command.h"
#include "common/seperator.h"

void command_nightcapui(Client *c, const Seperator *sep)
{
	if (sep->argnum == 1 && !strcmp(sep->arg[1], "refresh")) {
		c->RefreshNightcapUI();
	}
}

void command_nightcappet(Client *c, const Seperator *sep)
{
	c->HandlePetArmor(sep);
}
