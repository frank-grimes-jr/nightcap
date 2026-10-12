# ==============================================================================
# Instance Keeper — Generic per-character instance manager
#
# Place one NPC named "Instance_Keeper" at each dungeon entrance.
# Set the NPC's lastname to the SHORT name of the zone to instance
# (e.g., lastname = "befallen" for the Befallen instance keeper).
#
# Player flow:
#   Hail         → status / available options
#   'enter'      → create instance if needed, assign & move player (+ group)
#   'join'       → join group leader's existing instance
#   'reset'      → popup confirmation, destroy + recreate instance
#   'status'     → show remaining time on active instance
#
# Group behavior:
#   Leader says 'enter' → all online group members are assigned to the same
#   instance and notified. They say 'join' to the nearest Instance Keeper to
#   teleport in.
#
# Instances persist 12 hours. Server restart wipes all instances.
# ==============================================================================

my $INSTANCE_DURATION = 43200;  # 12 hours in seconds
my $INSTANCE_VERSION  = 0;  # version 0 inherits base-zone spawns/doors; v1+ would be EMPTY (spawn2.version)
my $POPUP_RESET       = 501;

# ── Helpers ───────────────────────────────────────────────────────────────────

sub _zone { $npc->GetLastName() }

sub _safe_coords {
    my ($zone_name) = @_;
    my $db  = Database->new();
    my $sth = $db->prepare("SELECT safe_x, safe_y, safe_z FROM zone WHERE short_name = ? LIMIT 1");
    return (0, 0, 0) unless $sth;
    $sth->execute($zone_name);
    my $row = $sth->fetch_hashref();
    return $row ? ($row->{safe_x}, $row->{safe_y}, $row->{safe_z}) : (0, 0, 0);
}

sub _char_id_by_name {
    my ($name) = @_;
    my $db  = Database->new();
    my $sth = $db->prepare("SELECT id FROM character_data WHERE name = ? LIMIT 1");
    return 0 unless $sth;
    $sth->execute($name);
    my $row = $sth->fetch_hashref();
    return $row ? $row->{id} : 0;
}

sub _enter_instance {
    my ($inst_id, $zone_name) = @_;
    my $char_name = $client->GetName();

    quest::AssignToInstance($inst_id);

    # Notify + assign all online group members
    my $group = $client->GetGroup();
    if ($group) {
        for (my $i = 0; $i < $group->GroupCount(); $i++) {
            my $member = $group->GetMember($i);
            next unless $member;
            next if $member->GetName() eq $char_name;
            quest::AssignToInstanceByCharID($inst_id, $member->CharacterID());
            $member->Message(15,
                "$char_name has entered an instance of $zone_name. " .
                "Hail the Instance Keeper here and say 'join' to follow."
            );
        }
    }

    my ($sx, $sy, $sz) = _safe_coords($zone_name);
    quest::MovePCInstance(quest::GetZoneID($zone_name), $inst_id, $sx, $sy, $sz);
}

# ── Events ────────────────────────────────────────────────────────────────────

sub keeper_visual {
    # Eye of Zomm (EYE) is in global_chr: no zone-specific model or client patch.
    # Keep the targetable service NPC and its destination lastname unchanged.
    return if $npc->GetRace() == 108;
    $npc->SendIllusionPacket({ race => 108, gender => 2, texture => 0,
        helmtexture => 0, size => 3 });
}

sub EVENT_SPAWN {
    keeper_visual();
}

sub EVENT_SIGNAL {
    return unless $signal == 20261014;
    keeper_visual();
}

sub EVENT_SAY {
    my $say     = lc($text);
    my $name    = $client->GetName();
    my $char_id = $client->CharacterID();
    my $zone    = _zone();

    if ($say =~ /hail/) {
        my $inst_id = quest::GetInstanceIDByCharID($zone, $INSTANCE_VERSION, $char_id);
        if ($inst_id) {
            quest::say(
                "Welcome back, $name. Your instance of $zone is active. " .
                "Say [" . quest::saylink('enter')  . "] to go in, " .
                "[" . quest::saylink('status') . "] to check remaining time, or " .
                "[" . quest::saylink('reset')  . "] to start fresh."
            );
        } else {
            quest::say(
                "Greetings, $name. I can open a private instance of $zone for you, " .
                "lasting 12 hours. Say [" . quest::saylink('enter') . "] to create and enter. " .
                "If you are grouped, say [" . quest::saylink('join') . "] to follow your leader's instance."
            );
        }
        return;
    }

    if ($say eq 'status') {
        my $inst_id = quest::GetInstanceIDByCharID($zone, $INSTANCE_VERSION, $char_id);
        if ($inst_id) {
            my $remaining = quest::GetInstanceTimerByID($inst_id);
            my $hours = int($remaining / 3600);
            my $mins  = int(($remaining % 3600) / 60);
            quest::say("$name, your $zone instance has approximately ${hours}h ${mins}m remaining.");
        } else {
            quest::say("$name, you have no active instance of $zone.");
        }
        return;
    }

    if ($say eq 'enter') {
        my $inst_id = quest::GetInstanceIDByCharID($zone, $INSTANCE_VERSION, $char_id);
        if (!$inst_id) {
            $inst_id = quest::CreateInstance($zone, $INSTANCE_VERSION, $INSTANCE_DURATION);
            if (!$inst_id) {
                quest::say("I was unable to open an instance right now. Please try again shortly.");
                return;
            }
        }
        _enter_instance($inst_id, $zone);
        return;
    }

    if ($say eq 'join') {
        my $group = $client->GetGroup();
        if (!$group) {
            quest::say("$name, you must be grouped to join another's instance. Say [" . quest::saylink('enter') . "] to create your own.");
            return;
        }
        my $leader_name = $group->GetLeaderName();
        if ($leader_name eq $name) {
            quest::say("$name, you are the group leader. Say [" . quest::saylink('enter') . "] to create and enter your instance.");
            return;
        }
        my $leader_id = _char_id_by_name($leader_name);
        if (!$leader_id) {
            quest::say("Unable to locate your group leader. Are they online?");
            return;
        }
        my $inst_id = quest::GetInstanceIDByCharID($zone, $INSTANCE_VERSION, $leader_id);
        if (!$inst_id) {
            quest::say("$leader_name has no active instance of $zone. Ask them to say [enter] first.");
            return;
        }
        quest::AssignToInstance($inst_id);
        my ($sx, $sy, $sz) = _safe_coords($zone);
        quest::MovePCInstance(quest::GetZoneID($zone), $inst_id, $sx, $sy, $sz);
        return;
    }

    if ($say eq 'reset') {
        my $inst_id = quest::GetInstanceIDByCharID($zone, $INSTANCE_VERSION, $char_id);
        if (!$inst_id) {
            quest::say("$name, you have no active instance to reset.");
            return;
        }
        quest::popup(
            "Reset Instance",
            "Destroy your $zone instance and create a fresh one?\n\n" .
            "All progress and mob kills will be lost. A new instance with full spawns will be created.",
            $POPUP_RESET, 1, 0
        );
        return;
    }
}

sub EVENT_POPUPRESPONSE {
    return unless $popupid == $POPUP_RESET;

    my $zone    = _zone();
    my $char_id = $client->CharacterID();
    my $old_id  = quest::GetInstanceIDByCharID($zone, $INSTANCE_VERSION, $char_id);

    quest::DestroyInstance($old_id) if $old_id;

    my $new_id = quest::CreateInstance($zone, $INSTANCE_VERSION, $INSTANCE_DURATION);
    if (!$new_id) {
        $client->Message(15, "Failed to create a new instance. Please try again.");
        return;
    }

    _enter_instance($new_id, $zone);
}

1;
