# The paid XP package is retired. Matron Restora retains free ordinary buffs.
sub EVENT_SAY {
	if ($text =~ /hail|empower/i) {
		quest::say("The scholar's draught is no longer offered, $name. Speak with Matron Restora in the Commonlands tunnel for her free blessings.");
	}
}
