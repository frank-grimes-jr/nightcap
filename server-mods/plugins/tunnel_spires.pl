use strict;
use warnings;

sub tunnel_spire_hail {
    my ($client,$npc,$text)=@_;
    return unless $client && $npc && defined $text && $npc->GetNPCTypeID()==999527;
    return unless $client->GetZoneID()==22 && $client->GetInstanceID()==0;
    my $distance=($client->GetX()-$npc->GetX())**2+($client->GetY()-$npc->GetY())**2+($client->GetZ()-$npc->GetZ())**2;
    return if $distance>10000;
    my $era=quest::get_rule('Expansion:CurrentExpansion');
    unless (defined $era && $era =~ /\A\d+\z/ && $era<=30) {
        quest::say('The paths are uncertain just now. Please try again later.'); return;
    }
    my @routes=grep { $_->{era}<=$era && $_->{min_level}<=$client->GetLevel() } @{plugin::tunnel_spire_catalog()};
    if ($text =~ /\Aspire ([a-z0-9]+)\z/) {
        my $destination=$1;
        my ($route)=grep { $_->{zone} eq $destination } @routes;
        unless ($route) { quest::say('That destination is not available. Hail me and choose an offered spire.'); return; }
        if ($client->GetHP()<=0 || $client->GetAggroCount() || $client->IsCasting() ||
            $client->IsStunned() || $client->IsMezzed() || $client->IsFeared()) {
            quest::say('Finish your fight or spell and recover, then we can travel.'); return;
        }
        my $last=$client->GetEntityVariable('nightcap_spire_departure') || 0;
        return if $last && time()-$last<5;
        $client->SetEntityVariable('nightcap_spire_departure',time());
        quest::say('Mind your arrival. The spires do not promise a friendly welcome.');
        $client->MovePC($route->{zone_id},$route->{x},$route->{y},$route->{z},$route->{heading});
        return;
    }
    if ($text =~ /\Aspire\b/i) { quest::say('Hail me again and choose one of the spires I offer.'); return; }
    quest::say('I am Khaleid. I open paths to the wizard spires. Cazic Thule leads into a dangerous temple; choose your destination with care.');
    while (@routes) {
        my @line=splice(@routes,0,3);
        quest::say(join(' - ',map { quest::saylink('spire '.$_->{zone},1,$_->{label}) } @line));
    }
}
1;
