#include "zone/client.h"

// #37: player-facing #aaexp -- set the % of combat XP that goes to AA.
// The RoF2 client hides its AA-XP toggle below level 51, so this command is the
// only way to turn AA experience on at low level (the #sellall pattern: a command
// where the client UI can't do it). Server enforces Character:AAExpMinLevel in exp.cpp.
void command_aa_exp(Client *c, const Seperator *sep)
{
	if (sep->argnum < 1 || (!sep->IsNumber(1) && !Strings::EqualFold(sep->arg[1], "off"))) {
		c->Message(Chat::White, "Usage: #aaexp [0-100|off] -- routes that %% of combat XP to AA.");
		c->Message(Chat::White, fmt::format("AA experience is currently {}%.", c->GetAAPercent()).c_str());
		return;
	}

	uint8 percent = Strings::EqualFold(sep->arg[1], "off") ? 0 : (uint8) Strings::ToUnsignedInt(sep->arg[1]);
	if (percent > 100) {
		percent = 100;
	}

	c->SetAAExperiencePercent(percent);
	c->Message(Chat::White, fmt::format("AA experience set to {}%.", percent).c_str());
}
