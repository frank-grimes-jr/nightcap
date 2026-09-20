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
    my %greetings=(
        999520=>'Crafted plate, two good blades, and enough room to swing. That is all I ask.',
        999521=>'May your road be clear. Ghoulbane has made a few of mine considerably quieter.',
        999522=>'I was standing right here the whole time. Ask anyone who did not see me.',
        999523=>'Fear teaches patience. Bringing back the armor takes a little more than that.',
        999524=>'Level twelve, full bronze, and I still lost my corpse in Butcherblock. A goblin killed me, and I cannot remember where.');
    if ($identity!=999525) { quest::say($greetings{$identity}); return; }
    my $era=quest::get_rule('Expansion:CurrentExpansion');
    unless (defined $era && $era =~ /^\d+$/ && $era<=30) {
        quest::say('The paths are uncertain just now. Please try again later.'); return;
    }
    my @rings=grep { $_->{era}<=$era && $_->{min_level}<=$client->GetLevel() } @{plugin::tunnel_ring_catalog()};
    if ($text =~ /^ring ([a-z]+)$/) {
        my $destination=$1;
        my ($ring)=grep { $_->{zone} eq $destination } @rings;
        unless ($ring) { quest::say('That ring is not available in this era.'); return; }
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

sub tunnel_trift_story {
    my ($entities)=@_;
    my @clients=$entities->GetClientList();
    return unless @clients;
    my @stories=(
        'I was level twelve and feeling invincible in my bronze. Then a goblin in Butcherblock killed me. Still cannot find that corpse.',
        'Has anyone seen a lost corpse in Butcherblock? Mine. Goblin got me. I thought I would remember which hill it was.',
        'The trouble with losing your corpse in Butcherblock is that every tree starts looking like the tree beside that goblin.',
        'Full bronze does not make a level twelve warrior goblin-proof. Learned that in Butcherblock. Still looking for the corpse.');
    quest::ooc($stories[int(rand(@stories))]);
}

1;
