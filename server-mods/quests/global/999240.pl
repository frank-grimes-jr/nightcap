# =============================================================================
# Nightcap waypoint marker — NPC 999240 'a waypoint' (#32)
#
# Discovery lives HERE, on the marker NPC, not in global_player.pl. The server
# loads global_player.LUA (Lua is first in _load_precedence, main.cpp), so the
# Perl global_player.pl — where waypoint discovery used to live — never loads and
# never ran. This "global by NPC ID" script (quests/global/999240.pl) loads for
# the marker in every catalog zone regardless of the global_player language.
#
# On spawn the NPC arms a proximity box around itself; when a client enters it,
# we record discovery for the current zone. The Waypoint Master in PoK reads
# nightcap_character_waypoints to offer recall; the full catalog => title 100.
# =============================================================================

sub EVENT_SPAWN {
    waypoint_visual();
    my $x = $npc->GetX();
    my $y = $npc->GetY();
    my $z = $npc->GetZ();
    # 25u horizontal, 30u vertical — matches the old global_player proximity check.
    quest::set_proximity($x - 25, $x + 25, $y - 25, $y + 25, $z - 30, $z + 30);
}

sub waypoint_visual {
    # Requires the paired client: the complete import lists load crs.eqg in both
    # model modes. The mesh is intended to remain recognizable with particles off;
    # verify the native material, scale and nameplate in the release QA matrix.
    # Keep the nameplate and discovery on this same entity, at its existing pose.
    if ($npc->GetRace() != 425 || $npc->GetGender() != 2) {
        $npc->SendIllusionPacket({ race => 425, gender => 2, texture => 0,
            helmtexture => 0, size => 6 });
    }
    # RoF2 spellsnew.eff 178 = WizardPortal. Nimbus state is sent to late joiners
    # by EntityList::SendNimbusEffects; avoid stacking it on live refreshes.
    unless (grep { $_ == 178 } ($npc->GetNimbusEffect1(),
            $npc->GetNimbusEffect2(), $npc->GetNimbusEffect3())) {
        $npc->AddNimbusEffect(178);
    }
}

sub EVENT_SIGNAL {
    return unless $signal == 20261011 || $signal == 20261022;
    waypoint_visual();
}

sub EVENT_ENTER {
    my $char_id = $client->CharacterID();

    my $db  = Database->new();
    my $ins = $db->prepare(
        "INSERT IGNORE INTO nightcap_character_waypoints (character_id, zone) VALUES (?, ?)"
    );
    return unless $ins;
    $ins->execute($char_id, $zonesn);
    return unless $ins->rows_affected();   # already discovered -> stay silent

    $client->Message(15,
        "You attune to the waypoint. The Waypoint Master in the Plane of Knowledge " .
        "can now return you to this spot.");

    my $cnt = $db->prepare(
        "SELECT (SELECT COUNT(*) FROM nightcap_character_waypoints WHERE character_id = ?) AS found,
                (SELECT COUNT(*) FROM nightcap_waypoints) AS total"
    );
    return unless $cnt;
    $cnt->execute($char_id);
    my $row = $cnt->fetch_hashref();
    return unless $row;

    if ($row->{found} >= $row->{total}) {
        quest::enabletitle(100);
        $client->Message(15,
            "You have discovered every waypoint in Norrath! You have earned the title 'the Explorer'.");
    }
    else {
        $client->Message(15, "Waypoints discovered: $row->{found} of $row->{total}.");
    }
}

1;
