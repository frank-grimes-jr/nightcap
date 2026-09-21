use strict;
use warnings;

sub tunnel_resident_hail {
    my ($client,$npc,$text)=@_;
    return unless $client && $npc && defined $text;
    my $identity=$npc->GetNPCTypeID();
    return unless $identity>=999520 && $identity<=999525;
    return unless $client->GetZoneID()==22 && $client->GetInstanceID()==0;
    my $distance=($client->GetX()-$npc->GetX())**2+($client->GetY()-$npc->GetY())**2+($client->GetZ()-$npc->GetZ())**2;
    return if $distance>10000;
    if ($identity!=999525) {
        my $lines=plugin::tunnel_dialogue($identity);
        quest::say($lines->[int(rand(@$lines))]); return;
    }
    my $era=quest::get_rule('Expansion:CurrentExpansion');
    unless (defined $era && $era =~ /^\d+$/ && $era<=30) {
        quest::say('The paths are uncertain just now. Please try again later.'); return;
    }
    my $lavastorm_ready=(quest::get_data('nightcap:classic_lavastorm_client_ready') || '') eq '1';
    my @rings=grep {
        $_->{era}<=$era && $_->{min_level}<=$client->GetLevel() &&
        ($_->{zone} ne 'lavastorm' || $lavastorm_ready)
    } @{plugin::tunnel_ring_catalog()};
    if ($text =~ /^ring ([a-z]+)$/) {
        my $destination=$1;
        my ($ring)=grep { $_->{zone} eq $destination } @rings;
        unless ($ring) { quest::say('That ring is not available right now.'); return; }
        if ($client->GetHP()<=0 || $client->GetAggroCount() || $client->IsCasting() ||
            $client->IsStunned() || $client->IsMezzed() || $client->IsFeared()) {
            quest::say('Finish your fight or spell, then we can travel.'); return;
        }
        my $last=$client->GetEntityVariable('nightcap_ring_departure') || 0;
        return if $last && time()-$last<5;
        $client->SetEntityVariable('nightcap_ring_departure',time());
        quest::say('Travel well, and mind the company waiting at the stones.');
        $client->MovePC($ring->{zone_id},$ring->{x},$ring->{y},$ring->{z},$ring->{heading});
        return;
    }
    if ($text =~ /^ring\b/i) { quest::say('Hail me again and choose one of the rings I offer.'); return; }
    quest::say('The rings are open. Where shall I send you?');
    # Short lines remain readable even when later expansion rings are unlocked.
    while (@rings) {
        my @line=splice(@rings,0,4);
        quest::say(join(' - ',map { quest::saylink('ring '.$_->{zone},1,$_->{label}) } @line));
    }
}

1;
