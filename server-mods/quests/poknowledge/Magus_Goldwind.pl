# Magus Goldwind — paid buff bot (#29). 100pp buys everything Matron Restora
# gives plus Bottle of Adventure III (21030): +50% XP for 2400 tics (4 hours,
# explicit duration so #31 does not make it permanent).
# Keep the bracket table in sync with Matron_Restora.pl.

my $PRICE_PP = 100;

sub bracket_buffs {
	my $level = shift;
	return (278, 202,  26, 144, 697) if $level < 10;
	return (278, 219, 263, 144, 697) if $level < 20;
	return (278,  89, 421, 144, 174) if $level < 30;
	return (278, 244, 422, 144, 174) if $level < 40;
	return (278, 312, 423, 145, 174);
}

sub EVENT_SAY {
	if ($text =~ /hail/i) {
		quest::say("Greetings, $name. For a mere $PRICE_PP platinum I shall [" . quest::saylink("empower", 1) . "] you: every blessing my colleague offers, plus a scholar's draught that hastens your learning by half for four hours.");
	}
	elsif ($text =~ /empower/i) {
		if ($client->TakePlatinum($PRICE_PP, 1)) {
			foreach my $spell (bracket_buffs($client->GetLevel())) {
				$client->ApplySpellBuff($spell);
			}
			$client->ApplySpellBuff(21030, 2400); # +50% XP, 4h
			quest::say("Gold well spent, $name. Learn quickly — the draught fades in four hours.");
		}
		else {
			quest::say("Alas, your purse is lighter than your ambition. Return with $PRICE_PP platinum.");
		}
	}
}
