use strict;
use warnings;

sub tunnel_travel_hail {
    my ($client,$npc,$text)=@_;
    return unless $client && $npc && defined $text && $npc->GetNPCTypeID()==999810;
    return unless $client->GetZoneID()==22 && $client->GetInstanceID()==0;
    my $distance=($client->GetX()-$npc->GetX())**2+($client->GetY()-$npc->GetY())**2+($client->GetZ()-$npc->GetZ())**2;
    return if $distance>2500;
    my @routes=@{plugin::tunnel_travel_catalog()};
    if ($text =~ /^travel ([a-z0-9]+)$/) {
        my $destination=$1;
        my ($route)=grep { $_->{zone} eq $destination } @routes;
        unless ($route) { quest::say('Hail me and choose one of the destinations I offer.'); return; }
        if ($client->GetHP()<=0 || $client->GetAggroCount() || $client->IsCasting() ||
            $client->IsStunned() || $client->IsMezzed() || $client->IsFeared()) {
            quest::say('Take a moment to recover and finish your fight or spell, then we can travel.'); return;
        }
        my $last=$client->GetEntityVariable('nightcap_city_departure') || 0;
        return if $last && time()-$last<5;
        $client->SetEntityVariable('nightcap_city_departure',time());
        $client->MovePC($route->{zone_id},$route->{x},$route->{y},$route->{z},$route->{heading});
        return;
    }
    quest::say('Welcome, traveler. Choose your destination. The nearby return book will bring you back to this tunnel.');
    while (@routes) {
        my @line=splice(@routes,0,3);
        quest::say(join(' - ',map { quest::saylink('travel '.$_->{zone},1,$_->{label}) } @line));
    }
}

1;
