use strict;
use warnings;

sub market_hail {
    my ($client, $npc, $text) = @_;
    return unless $client && $npc && defined $text;
    $client->LivingEconomy($npc->GetID(), $text);
}

sub market_pulse {
    my ($entities,$coordinator) = @_;
    my @clients = $entities->GetClientList();
    return unless @clients && $coordinator;
    # One coordinator owns the zone cadence; other traders have no chat timer.
    my @actors=grep { $entities->GetNPCByNPCTypeID($_) } plugin::tunnel_market_ids();
    my $id=plugin::tunnel_choose($coordinator,'tunnel_last_trader',@actors);
    return unless defined $id;
    my $speaker = $entities->GetNPCByNPCTypeID($id);
    return unless $speaker;
    my $variant = int(rand(600));
    $_->MarketAnnouncement($speaker->GetID(), $variant) for @clients;
}

1;
