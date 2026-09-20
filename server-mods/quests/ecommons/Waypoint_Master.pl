# Waypoint Master (#32) — teleports players to waypoints they have discovered
# (nightcap_character_waypoints, written by global_player.pl proximity checks).
# Hail lists discovered zones as saylinks; saying a zone's long name ports you.

sub EVENT_SAY {
	my $char_id = $client->CharacterID();
	my $db = Database->new();

	if ($text =~ /hail/i) {
		my $sth = $db->prepare(
			"SELECT z.long_name FROM nightcap_character_waypoints c
			 JOIN zone z ON z.short_name = c.zone AND z.version = 0
			 WHERE c.character_id = ? ORDER BY z.long_name");
		return unless $sth;
		$sth->execute($char_id);

		my @links;
		while (my $row = $sth->fetch_hashref()) {
			push @links, quest::saylink($row->{long_name}, 1);
		}

		my $tot = $db->prepare("SELECT COUNT(*) AS total FROM nightcap_waypoints");
		my $total = 0;
		if ($tot) {
			$tot->execute();
			my $t = $tot->fetch_hashref();
			$total = $t->{total} if $t;
		}

		if (!@links) {
			quest::say("Hail, $name. I sense no attunements upon you. Stand upon a waypoint in the wilds or the deep places, and I can return you to it. There are $total waiting to be found — find them all and the world shall name you 'the Explorer'.");
			return;
		}

		quest::say("Welcome back, $name. You have attuned " . scalar(@links) . " of $total waypoints. Speak the name of your destination:");
		# RoF2 chokes on very long say lines -- 8 links per line
		while (@links) {
			quest::say(join(", ", splice(@links, 0, 8)));
		}
	}
	else {
		my $sth = $db->prepare(
			"SELECT w.zone_id, w.x, w.y, w.z, w.heading FROM nightcap_character_waypoints c
			 JOIN nightcap_waypoints w ON w.zone = c.zone
			 JOIN zone z ON z.short_name = w.zone AND z.version = 0
			 WHERE c.character_id = ? AND LOWER(z.long_name) = LOWER(?)");
		return unless $sth;
		$sth->execute($char_id, $text);
		my $row = $sth->fetch_hashref();
		if ($row) {
			quest::say("Safe travels, $name.");
			$client->MovePC($row->{zone_id}, $row->{x}, $row->{y}, $row->{z}, $row->{heading});
		}
	}
}
