# Matron Restora — free buff bot (#29). Hail for SoW + HP + AC + HP-regen +
# mana-regen; spell rank scales with your level bracket, so re-hail every 10
# levels. ApplySpellBuff self-applies, so #31 makes these permanent until
# clicked off, overwritten, or death.
# Keep the bracket table in sync with Magus_Goldwind.pl.

sub bracket_buffs {
	my $level = shift;
	# SoW, HP line, AC line, HP regen, mana regen — classic ranks per bracket
	return (278, 202,  26, 144, 697) if $level < 10;   # Courage / Skin like Wood / Regeneration / Breeze
	return (278, 219, 263, 144, 697) if $level < 20;   # Center / Skin like Rock
	return (278,  89, 421, 144, 174) if $level < 30;   # Daring / Skin like Steel / Clarity
	return (278, 244, 422, 144, 174) if $level < 40;   # Bravery / Skin like Diamond
	return (278, 312, 423, 145, 174);                  # Valor / Skin like Nature / Chloroplast
}

sub EVENT_SAY {
	if ($text =~ /hail/i) {
		foreach my $spell (bracket_buffs($client->GetLevel())) {
			$client->ApplySpellBuff($spell);
		}
		quest::say("There you are, $name — swift feet and a stout heart. Return to me every ten seasons of your journey and I shall renew you with stronger blessings.");
	}
}
