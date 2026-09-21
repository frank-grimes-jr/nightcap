use strict;
use warnings;
use Test::More;
our $root=shift @ARGV or die 'Expected server-mods root';
{
    package plugin;
    do "$main::root/plugins/tunnel_chatter.pl" or die $@ || $!;
    do "$main::root/plugins/tunnel_resident_data.pl" or die $@ || $!;
    do "$main::root/plugins/tunnel_residents.pl" or die $@ || $!;
    package quest;
    our $era=0;
    our $lavastorm_ready='1';
    our (@said,@ooc,@timers);
    sub get_rule { return $era; }
    sub get_data { return $lavastorm_ready; }
    sub say { push @said,$_[0]; }
    sub saylink { return '['.$_[0].']'; }
    sub ooc { push @ooc,$_[0]; }
    sub settimer { push @timers,[@_]; }
    package ResidentNPC;
    sub GetNPCTypeID { return $_[0]->{id}; }
    sub GetX { return 0; } sub GetY { return 0; } sub GetZ { return 0; }
    sub ReturnHandinItems { $_[0]->{returned}++; }
    package ResidentClient;
    sub GetZoneID { return $_[0]->{zone}//22; }
    sub GetInstanceID { return $_[0]->{instance}//0; }
    sub GetX { return $_[0]->{x}//0; } sub GetY { return 0; } sub GetZ { return 0; }
    sub GetLevel { return 50; }
    sub GetHP { return 100; }
    sub GetAggroCount { return $_[0]->{combat}//0; }
    sub IsCasting { return $_[0]->{casting}//0; }
    sub IsStunned { return 0; } sub IsMezzed { return 0; } sub IsFeared { return 0; }
    sub GetEntityVariable { return $_[0]->{cooldown}//0; }
    sub SetEntityVariable { $_[0]->{cooldown}=$_[2]; }
    sub MovePC { push @{$_[0]->{moves}},[@_[1..5]]; }
    package ResidentEntities;
    sub GetClientList { return @{$_[0]->{clients}}; }
    package TriftQuest;
    our($client,$npc,$text,$entity_list,$timer);
    do "$main::root/quests/ecommons/999524.pl";
    die $@ || $! if $@ || $!;
}
my $npc=bless {id=>999525},'ResidentNPC';
my $client=bless {moves=>[]},'ResidentClient';
plugin::tunnel_resident_hail($client,$npc,'Hail');
my $menu=join(' ',@quest::said);
is(scalar(()=$menu=~/\[ring /g),9,'Classic menu has all nine druid rings');
unlike($menu,qr/dreadlands|qrg|commonlands|toxxulia|mistythicket|southro/,'later and replacement zones absent');
$quest::lavastorm_ready='';@quest::said=();
plugin::tunnel_resident_hail($client,$npc,'Hail');
unlike(join(' ',@quest::said),qr/\[ring lavastorm\]/,'missing Classic client readiness hides Lavastorm');
plugin::tunnel_resident_hail($client,$npc,'ring lavastorm');
is(scalar @{$client->{moves}},0,'unready Classic client blocks a stale Lavastorm link');
$quest::lavastorm_ready='1';
plugin::tunnel_resident_hail($client,$npc,'ring commons');
is_deeply($client->{moves},[[21,1427,478,-48,0]],'classic West Commonlands destination uses correct X/Y');
plugin::tunnel_resident_hail($client,$npc,'ring butcher');
is(scalar @{$client->{moves}},1,'repeated click cooldown prevents double zoning');
$client->{cooldown}=0;
for my $command ('ring dreadlands','ring qrg','ring nexus','ring commons 9999','ring 21','ring commonlands') {
    plugin::tunnel_resident_hail($client,$npc,$command);
}
is(scalar @{$client->{moves}},1,'locked and forged commands never move player');
for my $era (-1,'',undef,'not-an-era') {
    $quest::era=$era;plugin::tunnel_resident_hail($client,$npc,'ring commons');
}
is(scalar @{$client->{moves}},1,'unknown era fails closed');
$quest::era=0;
for my $state ({x=>101},{instance=>1},{zone=>202},{combat=>1},{casting=>1}) {
    my $blocked=bless {moves=>[],%$state},'ResidentClient';
    plugin::tunnel_resident_hail($blocked,$npc,'ring commons');
    is(scalar @{$blocked->{moves}},0,'range/instance/zone/combat/casting guard');
}
$quest::era=1;plugin::tunnel_resident_hail($client,$npc,'ring dreadlands');
is($client->{moves}[-1][0],86,'Kunark unlock permits Dreadlands');
$client->{cooldown}=0;
$quest::era=0;plugin::tunnel_resident_hail($client,$npc,'ring dreadlands');
is(scalar @{$client->{moves}},2,'era is rechecked when a formerly valid link is clicked');
$quest::era=2;plugin::tunnel_resident_hail($client,$npc,'ring qrg');
is($client->{moves}[-1][0],3,'Surefall does not unlock before Velious');
for my $id (999520..999524) {
    $npc->{id}=$id;plugin::tunnel_resident_hail($client,$npc,'Hail');
}
like($quest::said[-1],qr/Butcherblock/,'Trift remembers the requested story');
my $stories=plugin::tunnel_dialogue(999524);
is(scalar @$stories,6,'Trift has six story variations');
ok(!(grep { !/corpse/ || !/Butcherblock/ || !/goblin/i } @$stories),'every variation retains corpse, zone and cause');
$TriftQuest::npc=$npc;$TriftQuest::client=$client;
TriftQuest::EVENT_ITEM();is($npc->{returned},1,'wrong items and money use native return path');
ok(!TriftQuest->can('EVENT_TIMER'),'only the shared coordinator owns OOC cadence');
done_testing();
