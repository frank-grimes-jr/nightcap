use strict;
use warnings;

sub market_hail {
    my ($client, $npc, $text) = @_;
    return unless $client && $npc && defined $text;
    $client->LivingEconomy($npc->GetID(), $text);
}

sub market_pulse {
    my ($entities) = @_;
    my @clients = $entities->GetClientList();
    return unless @clients;
    # One coordinator owns the zone cadence; other traders have no chat timer.
    my $speaker = $entities->GetNPCByNPCTypeID(999500 + int(rand(10)));
    return unless $speaker;
    my $variant = rand() < 0.20 ? 8 + int(rand(6)) : int(rand(8));
    $_->MarketAnnouncement($speaker->GetID(), $variant) for @clients;
}

1;
