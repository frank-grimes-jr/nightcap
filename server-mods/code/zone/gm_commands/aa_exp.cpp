#include "zone/client.h"

// Player-facing AA focus toggle; passive AA does not require enabling it.
// The RoF2 client hides its AA-XP toggle below level 51, so this command is the
// only way to turn AA experience on at low level (the #sellall pattern: a command
// where the client UI can't do it). Server enforces Character:AAExpMinLevel in exp.cpp.
void command_aa_exp(Client *c, const Seperator *sep)
{
	if (sep->argnum < 1) {
		c->Message(Chat::White, "Usage: #aaexp [on|off|0|100]. Off keeps full leveling XP plus passive AA; on focuses XP into AA.");
		c->Message(Chat::White, fmt::format("AA experience is currently {}%.", c->GetAAPercent()).c_str());
		return;
	}

	uint32 percent = 0;
	if (Strings::EqualFold(sep->arg[1], "on")) {
		percent = 100;
	} else if (!Strings::EqualFold(sep->arg[1], "off")) {
		// Validate the complete token before conversion; never wrap a wide input.
		const std::string value = sep->arg[1];
		if (value.empty() || value.size() > 3 || value.find_first_not_of("0123456789") != std::string::npos
			|| (percent = Strings::ToUnsignedInt(value)) > 100) {
			c->Message(Chat::White, "Use #aaexp on (100%) or #aaexp off (0%).");
			return;
		}
	}

	c->SetAAExperiencePercent(percent);
	c->Message(Chat::White, fmt::format("AA experience set to {}%.", c->GetAAPercent()).c_str());
}
