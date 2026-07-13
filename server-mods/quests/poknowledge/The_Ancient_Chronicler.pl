# ==============================================================================
# The Ancient Chronicler — PoK Multiclass Hub
#
# Allows characters to awaken up to 2 additional class disciplines beyond their
# primary. Gated: 2nd discipline requires level 20, 3rd requires level 50.
#
# qglobals (scope 5 = character-only, permanent):
#   mc_class2  — secondary class ID (0 or absent = none)
#   mc_class3  — tertiary class ID  (0 or absent = none)
#
# Popup ID scheme:
#   200 + class_id  → confirm adding as secondary
#   300 + class_id  → confirm adding as tertiary
#   402             → confirm revoking secondary slot
#   403             → confirm revoking tertiary slot
#
# DB API note: this EQEmu version does not inject $DB. Use Database->new().
#   $db->prepare($sql)         → MySQLPreparedStmt (or undef on failure)
#   $sth->execute(@params)     → runs the query
#   $sth->fetch_hashref()      → next row as hashref (NOT fetchrow_hashref)
#   No $db->do() — use prepare+execute for all writes.
# ==============================================================================

my %CLASS_NAMES = (
    1  => 'Warrior',      2  => 'Cleric',      3  => 'Paladin',
    4  => 'Ranger',       5  => 'Shadow Knight', 6  => 'Druid',
    7  => 'Monk',         8  => 'Bard',         9  => 'Rogue',
    10 => 'Shaman',      11  => 'Necromancer', 12  => 'Wizard',
    13 => 'Magician',    14  => 'Enchanter',   15  => 'Beastlord',
    16 => 'Berserker',
);

my %CLASS_ABBREV = (
    1=>'WAR', 2=>'CLR', 3=>'PAL', 4=>'RNG', 5=>'SHD',
    6=>'DRU', 7=>'MNK', 8=>'BRD', 9=>'ROG', 10=>'SHM',
    11=>'NEC', 12=>'WIZ', 13=>'MAG', 14=>'ENC', 15=>'BST', 16=>'BER',
);

my $MIN_LEVEL_CLASS2 = 1;
my $MIN_LEVEL_CLASS3 = 1;

# ── Helpers ──────────────────────────────────────────────────────────────────

sub _db_current_expansion {
    my ($db) = @_;
    my $sth = $db->prepare(
        "SELECT CAST(rule_value AS UNSIGNED) AS val
         FROM rule_values
         WHERE rule_name = 'Expansion:CurrentExpansion' AND ruleset_id = 1
         LIMIT 1"
    );
    $sth->execute();
    my $row = $sth->fetch_hashref();
    return $row ? $row->{val} : 99;
}

sub _build_class_links {
    my ($base, $c2, $c3) = @_;
    my @links;
    for my $id (1..16) {
        next if $id == $base;
        next if $c2 && $id == $c2;
        next if $c3 && $id == $c3;
        push @links, '[' . quest::saylink($CLASS_NAMES{$id}) . ']';
    }
    return join(' ', @links);
}

sub _apply_class {
    my ($db, $char_id, $base_class, $sec_class, $existing_c2, $existing_c3, $level) = @_;

    my $slot     = !$existing_c2 ? 2 : 3;
    my $slot_key = "mc_class$slot";

    quest::setglobal($slot_key, $sec_class, 5, 'F');

    if ($slot == 2) {
        my $sth = $db->prepare(
            "INSERT INTO character_multiclass (character_id, class2)
             VALUES (?, ?)
             ON DUPLICATE KEY UPDATE class2 = VALUES(class2), applied_at = CURRENT_TIMESTAMP"
        );
        $sth->execute($char_id, $sec_class);
    } else {
        my $sth = $db->prepare(
            "UPDATE character_multiclass SET class3 = ?, applied_at = CURRENT_TIMESTAMP
             WHERE character_id = ?"
        );
        $sth->execute($sec_class, $char_id);
    }

    # Patch spells_new so the character's base class can memorize purchased secondary spells.
    # Sets base class min-level = secondary class min-level where base had no access.
    my $col      = "classes$sec_class";
    my $col_base = "classes$base_class";
    my $patch_sth = $db->prepare(
        "UPDATE spells_new SET $col_base = $col WHERE $col_base = 255 AND $col > 0 AND $col != 255"
    );
    $patch_sth->execute();

    # Expand skill caps: add secondary class skills that base class lacked
    my $skill_sth = $db->prepare(
        "INSERT IGNORE INTO skill_caps (class_id, skill_id, level, cap)
         SELECT ?, skill_id, level, cap
         FROM skill_caps
         WHERE class_id = ?
           AND skill_id NOT IN (SELECT skill_id FROM skill_caps WHERE class_id = ?)"
    );
    $skill_sth->execute($base_class, $sec_class, $base_class);

    # Prefix AA names with [CLR], [NEC], etc. so the Title column shows class origin.
    # Applied before the classes expansion so the WHERE condition is still valid.
    # NOT LIKE guard prevents double-prefix on re-application after revoke.
    my $base_bit = 2 ** ($base_class - 1);
    my $sec_bit  = 2 ** ($sec_class - 1);
    my $prefix   = "[$CLASS_ABBREV{$sec_class}] ";
    my $aa_name_sth = $db->prepare(
        "UPDATE aa_ability SET name = CONCAT(?, name)
         WHERE (classes & ?) > 0 AND (classes & ?) = 0
           AND name NOT LIKE ?"
    );
    $aa_name_sth->execute($prefix, $sec_bit, $base_bit, "$prefix%");

    my $aa_class_sth = $db->prepare(
        "UPDATE aa_ability SET classes = classes | ?
         WHERE (classes & ?) > 0 AND (classes & ?) = 0"
    );
    $aa_class_sth->execute($base_bit, $sec_bit, $base_bit);

    $client->Message(15,
        "The $CLASS_NAMES{$sec_class} discipline awakens within you. " .
        "Visit the spell vendors nearby to purchase tomes for your new discipline. " .
        "Log out and back in for all changes to take full effect."
    );
}

sub _train_skills {
    my ($db, $base, $c2, $c3, $level) = @_;
    my @ids = grep { $_ } ($base, $c2 // 0, $c3 // 0);
    my $ph  = join(',', ('?') x @ids);

    my $sth = $db->prepare(
        "SELECT skill_id, MAX(cap) AS max_cap
         FROM skill_caps
         WHERE class_id IN ($ph) AND level <= ?
         GROUP BY skill_id"
    );
    $sth->execute(@ids, $level);
    while (my $row = $sth->fetch_hashref()) {
        my $current = $client->GetSkill($row->{skill_id});
        $client->SetSkill($row->{skill_id}, $row->{max_cap})
            if $current < $row->{max_cap};
    }
}

sub _revoke_slot {
    my ($db, $char_id, $base_class, $slot, $c2, $c3) = @_;
    my $revoke_class = $slot == 2 ? $c2 : $c3;
    my $keep_class   = $slot == 2 ? $c3 : $c2;
    return unless $revoke_class;

    # When revoking slot 2, promote slot 3 → slot 2 if it exists
    if ($slot == 2 && $keep_class) {
        quest::setglobal('mc_class2', $keep_class, 5, 'F');
        quest::delglobal('mc_class3');
        my $sth = $db->prepare(
            "UPDATE character_multiclass SET class2 = ?, class3 = NULL WHERE character_id = ?"
        );
        $sth->execute($keep_class, $char_id);
    } elsif ($slot == 2) {
        quest::delglobal('mc_class2');
        my $sth = $db->prepare("UPDATE character_multiclass SET class2 = NULL WHERE character_id = ?");
        $sth->execute($char_id);
    } else {
        quest::delglobal('mc_class3');
        my $sth = $db->prepare("UPDATE character_multiclass SET class3 = NULL WHERE character_id = ?");
        $sth->execute($char_id);
    }

    $client->Message(15,
        "Your $CLASS_NAMES{$revoke_class} discipline has been released. " .
        "Log out and back in for all changes to take effect."
    );
}

# ── Events ────────────────────────────────────────────────────────────────────

sub EVENT_SAY {
    my $say      = lc($text);
    my $name     = $client->GetName();
    my $level    = $client->GetLevel();
    my $base     = $client->GetClass();
    my $char_id  = $client->CharacterID();
    my $c2       = $qglobals{mc_class2} // 0;
    my $c3       = $qglobals{mc_class3} // 0;

    if ($say =~ /hail/) {
        my $c2_name = $c2 ? $CLASS_NAMES{$c2} : 'none';
        my $c3_name = $c3 ? $CLASS_NAMES{$c3} : 'none';
        quest::say(
            "Greetings, $name. I am the Ancient Chronicler, keeper of forgotten disciplines. " .
            "Your path: $CLASS_NAMES{$base} | Second: $c2_name | Third: $c3_name. " .
            "Seek [" . quest::saylink('learn disciplines') . "], " .
            "[" . quest::saylink('train skills') . "], " .
            "[" . quest::saylink('release discipline') . "], or " .
            "[" . quest::saylink('my disciplines') . "]."
        );
        return;
    }

    if ($say eq 'my disciplines') {
        my $c2_str = $c2 ? $CLASS_NAMES{$c2} : '(none)';
        my $c3_str = $c3 ? $CLASS_NAMES{$c3} : '(none)';
        quest::say("$name, your disciplines are: Primary: $CLASS_NAMES{$base} | Second: $c2_str | Third: $c3_str.");
        return;
    }

    if ($say eq 'learn disciplines') {
        if ($c2 && $c3) {
            quest::say(
                "$name, you have already awakened two additional disciplines. " .
                "[" . quest::saylink('release discipline') . "] one before choosing another."
            );
            return;
        }
        if (!$c2 && $level < $MIN_LEVEL_CLASS2) {
            quest::say("You must reach level $MIN_LEVEL_CLASS2 to awaken a second discipline, $name.");
            return;
        }
        if ($c2 && !$c3 && $level < $MIN_LEVEL_CLASS3) {
            quest::say("You must reach level $MIN_LEVEL_CLASS3 to awaken a third discipline, $name.");
            return;
        }

        my $slot  = !$c2 ? 'second' : 'third';
        my $links = _build_class_links($base, $c2, $c3);
        quest::say("Choose your $slot discipline, $name. Speak its name: $links");
        return;
    }

    if ($say eq 'train skills') {
        my $db = Database->new();
        _train_skills($db, $base, $c2, $c3, $level);
        quest::say("Your skills have been trained to the highest cap available for all your disciplines, $name.");
        return;
    }

    if ($say eq 'release discipline') {
        if (!$c2 && !$c3) {
            quest::say("You carry no additional disciplines, $name.");
            return;
        }
        my $opts = '';
        $opts .= '[' . quest::saylink("release $CLASS_NAMES{$c2}") . '] ' if $c2;
        $opts .= '[' . quest::saylink("release $CLASS_NAMES{$c3}") . ']'  if $c3;
        quest::say("Which discipline would you release, $name? $opts");
        return;
    }

    # Release a named discipline
    if ($say =~ /^release (.+)$/) {
        my $target = lc($1);
        my $revoke_slot = 0;
        $revoke_slot = 2 if $c2 && lc($CLASS_NAMES{$c2}) eq $target;
        $revoke_slot = 3 if $c3 && lc($CLASS_NAMES{$c3}) eq $target;

        if ($revoke_slot) {
            my $revoke_class = $revoke_slot == 2 ? $c2 : $c3;
            quest::popup(
                "Release Discipline",
                "Release your $CLASS_NAMES{$revoke_class} discipline?\n\n" .
                "This removes all spells granted by that path from your spellbook. " .
                "Your trained skills and expanded AAs remain. " .
                "You may re-awaken this discipline at any time.",
                400 + $revoke_slot, 1, 0
            );
        } else {
            quest::say("You do not carry the $1 discipline, $name.");
        }
        return;
    }

    # Class name selection
    for my $id (1..16) {
        if ($say eq lc($CLASS_NAMES{$id})) {
            if ($id == $base) {
                quest::say("That is already your primary discipline.");
                return;
            }
            if (($c2 && $id == $c2) || ($c3 && $id == $c3)) {
                quest::say("You have already awakened the $CLASS_NAMES{$id} discipline.");
                return;
            }
            if (!$c2 && $level < $MIN_LEVEL_CLASS2) {
                quest::say("You must reach level $MIN_LEVEL_CLASS2 to awaken a second discipline.");
                return;
            }
            if ($c2 && $level < $MIN_LEVEL_CLASS3) {
                quest::say("You must reach level $MIN_LEVEL_CLASS3 to awaken a third discipline.");
                return;
            }

            my $slot_label = !$c2 ? 'second' : 'third';
            my $popup_base = !$c2 ? 200 : 300;

            quest::popup(
                "Awaken $CLASS_NAMES{$id}",
                "Awaken $CLASS_NAMES{$id} as your $slot_label discipline?\n\n" .
                "You will gain:\n" .
                "  - Skills trained to this class's caps\n" .
                "  - Access to $CLASS_NAMES{$id} AA abilities\n\n" .
                "Purchase spells from the vendors nearby.\n" .
                "You may release this discipline at any time.",
                $popup_base + $id, 1, 0
            );
            return;
        }
    }
}

sub EVENT_POPUPRESPONSE {
    my $base    = $client->GetClass();
    my $char_id = $client->CharacterID();
    my $level   = $client->GetLevel();
    my $c2      = $qglobals{mc_class2} // 0;
    my $c3      = $qglobals{mc_class3} // 0;
    my $db      = Database->new();

    # Confirm secondary class (popup 201-216)
    if ($popupid >= 201 && $popupid <= 216) {
        _apply_class($db, $char_id, $base, $popupid - 200, $c2, $c3, $level);
        return;
    }

    # Confirm tertiary class (popup 301-316)
    if ($popupid >= 301 && $popupid <= 316) {
        _apply_class($db, $char_id, $base, $popupid - 300, $c2, $c3, $level);
        return;
    }

    # Confirm revoke secondary (popup 402)
    if ($popupid == 402) {
        _revoke_slot($db, $char_id, $base, 2, $c2, $c3);
        return;
    }

    # Confirm revoke tertiary (popup 403)
    if ($popupid == 403) {
        _revoke_slot($db, $char_id, $base, 3, $c2, $c3);
        return;
    }
}

1;
