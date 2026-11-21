# The two parent spells are self-targeted. The pulse's child spell resolves
# resist, hate, damage and death through the native single-target spell path.
use strict;
use warnings;
use Time::HiRes qw(clock_gettime CLOCK_MONOTONIC);

sub cairnwright_spell {
    my ($client, $caster_id, $spell_id, $entities) = @_;
    return 1 unless $client && $client->GetID() == $caster_id
        && $client->IsMulticlassMember(17);

    my $key = 'cairnwright.stone';
    my $now = clock_gettime(CLOCK_MONOTONIC);
    my @hammer = ($client->GetX(), $client->GetY(), $client->GetZ());
    if ($spell_id == 44381) {
        $client->SetEntityVariable($key, join(',', $now + 90, @hammer));
        $client->Message(15, 'You set your cairn into the ground.');
        return 1;
    }
    return 1 unless $spell_id == 44382;
    my $stone = $client->GetEntityVariable($key);
    my ($expires, @anchor) = split /,/, ($stone // '');
    unless (@anchor == 3 && $expires > $now) {
        $client->DeleteEntityVariable($key);
        $client->Message(15, 'Set a cairn before sounding the seam.');
        return 1;
    }
    my @line = map { $anchor[$_] - $hammer[$_] } 0..2;
    my $length2 = $line[0]**2 + $line[1]**2 + $line[2]**2;
    if ($length2 < 1 || $length2 > 60**2 || !$client->CheckLoSToLoc(@anchor)) {
        $client->Message(15, 'You cannot sound a clear seam to your cairn from here.');
        return 1;
    }

    my @party = ($client);
    if (my $group = $client->GetGroup()) {
        push @party, grep { defined } map { $group->GetMember($_) } 0..5;
    }
    my @targets;
    for my $mob ($client->GetCloseMobList(61)) {
        next unless $mob->IsNPC() && !$mob->GetOwnerID() && $client->IsAttackAllowed($mob);
        my @offset = ($mob->GetX() - $hammer[0], $mob->GetY() - $hammer[1], $mob->GetZ() - $hammer[2]);
        my $along = ($offset[0]*$line[0] + $offset[1]*$line[1] + $offset[2]*$line[2]) / $length2;
        next if $along < 0 || $along > 1;
        my $distance2 = 0;
        $distance2 += ($offset[$_] - $along * $line[$_])**2 for 0..2;
        next if $distance2 > 4**2;
        next unless $client->CheckLoS($mob) && $mob->CheckLoSToLoc(@anchor);
        next unless grep { $mob->CheckAggro($_) } @party;
        push @targets, [$along, $mob->GetID()];
    }
    @targets = sort { $a->[0] <=> $b->[0] || $a->[1] <=> $b->[1] } @targets;
    splice @targets, 2 if @targets > 2;
    # Resolve by ID after each hit. A death event can despawn the next mob.
    for my $entry (@targets) {
        my $mob = $entities->GetMobByID($entry->[1]);
        next unless $mob && $mob->IsNPC() && !$mob->GetOwnerID()
            && $client->IsAttackAllowed($mob) && grep { $mob->CheckAggro($_) } @party;
        $client->SpellFinished(44383, $mob, 0);
    }
    $client->Message(15, 'Your hammer finds no foe along the seam.') unless @targets;
    return 1;
}

1;
