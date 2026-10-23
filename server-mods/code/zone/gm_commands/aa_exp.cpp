#include "zone/client.h"

// Player-facing AA allocation; native plus/minus controls use the same setter.
// 0 retains full leveling XP plus passive AA; 100 pauses leveling for AA focus.
void command_aa_exp(Client *c, const Seperator *sep)
{
	if (sep->argnum < 1) {
		c->Message(Chat::White, "Usage: #aaexp [on|off|0-100]. 0 keeps full leveling XP plus passive AA; 100 pauses leveling for AA.");
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
			c->Message(Chat::White, "Use #aaexp on (100%), off (0%), or a percentage from 0 to 100.");
			return;
		}
	}

	c->SetAAExperiencePercent(percent);
	c->Message(Chat::White, fmt::format("AA experience set to {}%.", c->GetAAPercent()).c_str());
}
