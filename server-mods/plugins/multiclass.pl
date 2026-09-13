# ==============================================================================
# plugin::multiclass — core of the Nightcap multiclass system (ADR 0003)
#
# NPC scripts (The Ancient Chronicler) call these dialogue-facing operations.
# Release persistence belongs to the native atomic ReleaseMulticlassSlot method.
#
# State: character_multiclass (class2, class3) — the ONLY authority. The zone
# binary's LoadMulticlassMask() reads it on zone-in for AA access. qglobals are
# not used anywhere in this system anymore.
#
# DB API (this build): Database->new(), prepare/execute/fetch_hashref.
# Method names must match perl_*.cpp bindings (CharacterID, not GetCharacterID).
# ==============================================================================

my %MC_CLASS_NAMES = (
    1  => 'Warrior',   2  => 'Cleric',    3  => 'Paladin',      4  => 'Ranger',
    5  => 'Shadow Knight', 6 => 'Druid',  7  => 'Monk',         8  => 'Bard',
    9  => 'Rogue',     10 => 'Shaman',    11 => 'Necromancer',  12 => 'Wizard',
    13 => 'Magician',  14 => 'Enchanter', 15 => 'Beastlord',    16 => 'Berserker',
);

my %MC_FLAVOR = (
    1  => 'the unbreakable wall of steel',
    2  => 'the light that mends and smites',
    3  => 'the oath sworn in radiance',
    4  => 'the arrow loosed from shadowed woods',
    5  => 'the blade that drinks fear',
    6  => 'the wrath and mercy of the wild',
    7  => 'the fist that needs no weapon',
    8  => 'the song that bends the world',
    9  => 'the knife you never saw',
    10 => 'the spirits\' bargain made flesh',
    11 => 'the whisper beyond the grave',
    12 => 'the raw fire of pure intellect',
    13 => 'the maker of servants from nothing',
    14 => 'the mind that unmakes yours',
    15 => 'the beast and its master, one will',
    16 => 'the fury that cannot be caged',
);

sub mc_class_name { my ($id) = @_; return $MC_CLASS_NAMES{$id} // 'Unknown'; }
sub mc_flavor     { my ($id) = @_; return $MC_FLAVOR{$id} // ''; }
sub mc_class_id_by_name {
    my ($name) = @_;
    $name = lc($name // '');
    for my $id (keys %MC_CLASS_NAMES) {
        return $id if lc($MC_CLASS_NAMES{$id}) eq $name;
    }
    return 0;
}

# (class2, class3) for a character — 0 when unset
sub mc_get_classes {
    my ($char_id) = @_;
    my $db  = Database->new();
    my $sth = $db->prepare("SELECT class2, class3 FROM character_multiclass WHERE character_id = ?");
    return (0, 0) unless $sth;
    $sth->execute($char_id);
    my $row = $sth->fetch_hashref();
    return (0, 0) unless $row;
    return ($row->{class2} // 0, $row->{class3} // 0);
}

# What would adopting $class_id grant this character? Live counts for the preview.
# Returns hashref: { spells_total, spells_now, skills_new, aa_lines }
sub mc_preview {
    my ($base_class, $class_id, $level) = @_;
    my $db  = Database->new();
    my $col = "classes$class_id";
    my $col_base = "classes$base_class";
    my %out = (spells_total => 0, spells_now => 0, skills_new => 0, aa_lines => 0);

    my $sth = $db->prepare(
        "SELECT COUNT(*) total, SUM($col <= ?) now
         FROM spells_new WHERE $col > 0 AND $col != 255 AND $col_base = 255"
    );
    if ($sth) {
        $sth->execute($level);
        if (my $r = $sth->fetch_hashref()) {
            $out{spells_total} = $r->{total} // 0;
            $out{spells_now}   = $r->{now}   // 0;
        }
    }

    $sth = $db->prepare(
        "SELECT COUNT(DISTINCT skill_id) c FROM skill_caps
         WHERE class_id = ? AND skill_id NOT IN (SELECT skill_id FROM skill_caps WHERE class_id = ?)"
    );
    if ($sth) {
        $sth->execute($class_id, $base_class);
        if (my $r = $sth->fetch_hashref()) { $out{skills_new} = $r->{c} // 0; }
    }

    my $bit = 1 << ($class_id - 1);
    $sth = $db->prepare(
        "SELECT COUNT(*) c FROM aa_ability WHERE enabled = 1 AND (classes & ?) > 0 AND classes != 65535"
    );
    if ($sth) {
        $sth->execute($bit);
        if (my $r = $sth->fetch_hashref()) { $out{aa_lines} = $r->{c} // 0; }
    }

    return \%out;
}

# Adopt $class_id into the first free slot. Returns (1, msg) or (0, error).
sub mc_apply_class {
    my ($client, $class_id) = @_;
    my $char_id = $client->CharacterID();
    my $base    = $client->GetClass();
    my ($c2, $c3) = plugin::mc_get_classes($char_id);

    return (0, 'That is already your birth discipline.') if $class_id == $base;
    return (0, 'You already carry two additional disciplines. Release one first.') if $c2 && $c3;
    return (0, 'You already carry that discipline.') if $class_id == $c2 || $class_id == $c3;
    return (0, 'No such discipline exists.') unless $MC_CLASS_NAMES{$class_id};

    my $db = Database->new();
    if (!$c2) {
        my $sth = $db->prepare(
            "INSERT INTO character_multiclass (character_id, class2) VALUES (?, ?)
             ON DUPLICATE KEY UPDATE class2 = VALUES(class2), applied_at = CURRENT_TIMESTAMP"
        );
        $sth->execute($char_id, $class_id);
    } else {
        my $sth = $db->prepare(
            "UPDATE character_multiclass SET class3 = ?, applied_at = CURRENT_TIMESTAMP WHERE character_id = ?"
        );
        $sth->execute($class_id, $char_id);
    }

    # RoF2 gates spell memorization client-side by spells_new.classesN, so the base
    # class inherits the secondary's min-levels globally (only where base had none).
    my $col      = "classes$class_id";
    my $col_base = "classes$base";
    my $patch = $db->prepare(
        "UPDATE spells_new SET $col_base = $col WHERE $col_base = 255 AND $col > 0 AND $col != 255"
    );
    $patch->execute();

    # Skills are never written by quest code. The C++ lifecycle reconciler owns
    # value-1 native unlocks after the canonical skill_caps baseline is restored.
    $client->ReconcileMulticlassSkills();

    $client->Message(335,
        'Operator note: run tools/sync-spell-access.ps1 (client closed) so the new ' .
        'discipline\'s scrolls become scribable - it syncs scroll items and the client spell file.'
    );

    return (1, "The $MC_CLASS_NAMES{$class_id} discipline awakens within you - " .
               "$MC_FLAVOR{$class_id}. Purchase tomes at the Loremasters, and camp " .
               "to the character screen for every change to take hold.");
}

# Native release commits slots, earned AA refunds and skill clamps together.
# Requires the matching server binary; never fall back to a separate SQL write.
sub mc_revoke_slot {
    my ($client, $slot) = @_;
    return (0, 'Choose discipline slot 2 or 3.') unless defined($slot) && $slot =~ /\A[23]\z/;
    return (0, 'Discipline release is unavailable. Please contact the server operator.')
        unless $client->can('ReleaseMulticlassSlot');
    my ($c2, $c3) = plugin::mc_get_classes($client->CharacterID());
    my $revoked = $slot == 2 ? $c2 : $c3;
    return (0, 'That discipline slot is already empty.') unless $revoked;
    my $saved = eval { $client->ReleaseMulticlassSlot($slot) };
    return (0, 'The discipline release could not be confirmed. Please reconnect before trying again.') unless $saved;
    return (1, "Your $MC_CLASS_NAMES{$revoked} discipline has been released. " .
               "Class-only alternate abilities were removed and eligible AA points refunded.");
}

1;
