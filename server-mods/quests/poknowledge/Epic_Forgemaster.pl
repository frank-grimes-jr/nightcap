# ==============================================================================
# Epic Forgemaster — "Ascension"
#
# Upgrades a class 1.0 epic weapon to its Ascended version (base id + 800,000).
#
# Mechanic (no-drop safe): the epic stays in the player's INVENTORY and is detected
# + removed via CountItem/RemoveItem (no-drop items can't be handed to an NPC). Only
# droppable currency is handed in: N Essence of Ascension (stack) + platinum.
#
# Hand to the Forgemaster, all at once:
#   - 8x Essence of Ascension (item 900000, ~1% drop from lvl 55+ NPCs)
#   - 100,000 platinum
#   ...while carrying your class epic UNEQUIPPED in your inventory.
#
# Stack quantity is read from $itemN_charges (the parser exports per-slot charges).
# ==============================================================================

my $ESSENCE     = 900000;
my $ESS_NEEDED  = 8;
my $PLAT_COST   = 100000;
my $LEG_OFFSET  = 800000;

# class id => [epic 1.0 item id(s)]  (Ranger has two)
my %CLASS_EPIC = (
    1  => [10908],          # Warrior      - Jagged Blade of War
    2  => [5532],           # Cleric       - Water Sprinkler of Nem Ankh
    3  => [10099],          # Paladin      - Fiery Defender
    4  => [20488, 20487],   # Ranger       - Earthcaller + Swiftwind
    5  => [14383],          # Shadowknight - Innoruuk's Curse
    6  => [20490],          # Druid        - Nature Walkers Scimitar
    7  => [10652],          # Monk         - Celestial Fists
    8  => [20542],          # Bard         - Singing Short Sword
    9  => [11057],          # Rogue        - Ragebringer
    10 => [10651],          # Shaman       - Spear of Fate
    11 => [20544],          # Necromancer  - Scythe of the Shadowed Soul
    12 => [14341],          # Wizard       - Staff of the Four
    13 => [11566],          # Magician     - Staff of Elemental Mastery: Fire
    14 => [10650],          # Enchanter    - Staff of the Serpent
);

sub EVENT_SAY {
    if ($text =~ /hail/i) {
        quest::say(
            "I am the Epic Forgemaster. I can reforge a class epic into an Ascended relic. " .
            "Carry your epic UNEQUIPPED in your pack, then hand me $ESS_NEEDED [Essence of Ascension] " .
            "and 100,000 platinum together. The forge will do the rest."
        );
    }
}

sub EVENT_ITEM {
    my @id = ($item1, $item2, $item3, $item4);
    my @ch = ($item1_charges, $item2_charges, $item3_charges, $item4_charges);

    # count handed-in essences (sum stack charges across slots)
    my $ess = 0;
    for my $i (0..3) {
        next unless $id[$i] && $id[$i] == $ESSENCE;
        $ess += ($ch[$i] > 0 ? $ch[$i] : 1);
    }
    my $plat = $platinum // 0;

    # which of this class's epics does the player carry?
    my $epics = $CLASS_EPIC{$client->GetClass()} || [];
    my @owned = grep { $client->CountItem($_) > 0 } @$epics;

    if (@owned && $ess >= $ESS_NEEDED && $plat >= $PLAT_COST) {
        # success — consume essences + plat (by not returning), remove epic, grant ascended
        for my $epic_id (@owned) {
            $client->RemoveItem($epic_id, 1);
            quest::summonitem($epic_id + $LEG_OFFSET);
        }
        quest::say("The forge blazes white-hot... your epic is reborn. Wield your Ascended relic with honor, " . $client->GetName() . "!");
        return;
    }

    # failure — return everything handed in, explain what's missing
    for my $i (0..3) {
        quest::summonitem($id[$i], $ch[$i]) if $id[$i];
    }
    quest::givecash(0, 0, 0, $plat) if $plat > 0;

    my @need;
    push @need, "your class epic carried (unequipped) in your inventory" unless @owned;
    push @need, "$ESS_NEEDED Essence of Ascension (you gave $ess)"       unless $ess >= $ESS_NEEDED;
    push @need, "100,000 platinum (you gave $plat)"                       unless $plat >= $PLAT_COST;
    quest::say("The forging cannot begin. I require: " . join("; ", @need) . ".");
}

1;
