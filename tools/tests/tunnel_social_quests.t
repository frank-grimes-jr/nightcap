use strict;
use warnings;
use Test::More;
our $root=shift @ARGV or die 'Expected installed server root';
{
    package plugin;
    our @hails;
    sub tunnel_resident_hail { push @hails,[$_[1]->GetNPCTypeID(),$_[2]]; }
    do "$main::root/plugins/tunnel_social.pl" or die $@ || $!;
    package quest;
    our (@timers,@said,@ooc);
    sub settimer { push @timers,[@_]; }
    sub say { push @said,$_[0]; }
    sub ooc { push @ooc,$_[0]; }
    package Actor;
    sub GetNPCTypeID { $_[0]->{id} }
    sub GetX { $_[0]->{x}//0 } sub GetY { $_[0]->{y}//0 } sub GetZ { 3.75 }
    sub IsEngaged { $_[0]->{engaged}//0 }
    sub GetEntityVariable { $_[0]->{vars}{$_[1]} }
    sub SetEntityVariable { $_[0]->{vars}{$_[1]}=$_[2] }
    sub FaceTarget { push @{$_[0]->{faced}},$_[1]->GetNPCTypeID() }
    sub DoAnim { push @{$_[0]->{animations}},$_[1] }
    sub ReturnHandinItems { $_[0]->{returned}++ }
    package Entities;
    sub GetClientList { @{$_[0]->{clients}} }
    sub GetNPCByNPCTypeID { $_[0]->{npcs}{$_[1]} }
}
srand(1731);
my $npc=bless {id=>999520,faced=>[],animations=>[],vars=>{}},'Actor';
my $client=bless {x=>80},'Actor';
my %peers=map { $_=>bless({id=>$_,x=>20+($_-999520)*4},'Actor') } (999521..999524,999526);
my $entities=bless {clients=>[$client],npcs=>\%peers},'Entities';
for (1..100) { plugin::tunnel_social_idle($npc,$entities,'tunnel_social_idle'); }
is(scalar @{$npc->{faced}},100,'nearby observers see changing social partners');
ok(!(grep { $npc->{faced}[$_]==$npc->{faced}[$_-1] } 1..99),'no consecutive identical partner');
ok((grep { $_==999526 } @{$npc->{faced}}),'Glorphyndel participates in the ring');
ok(@{$npc->{animations}}>0 && @{$npc->{animations}}<100,'gestures are intermittent');
ok(!(grep { $_!=48 && $_!=29 } @{$npc->{animations}}),'only classic nod and wave gestures');
ok(!(grep { $_->[1]<35 || $_->[1]>80 } @quest::timers),'idle cadence stays between 35 and 80 seconds');
my %delays=map { $_->[1]=>1 } @quest::timers;
ok(keys(%delays)>10,'cadence varies instead of synchronized ticks');
is(scalar @quest::ooc,0,'social gestures produce no OOC spam');
my $nalin=bless {id=>999523,faced=>[],animations=>[],vars=>{}},'Actor';
my $before_timers=@quest::timers;
for (1..100) { plugin::tunnel_social_idle($nalin,$entities,'tunnel_social_idle'); }
is(scalar @{$nalin->{faced}},100,'Nalin still turns toward his companions');
is(scalar @{$nalin->{animations}},0,'Nalin never emotes with SoulFire equipped');
is(scalar @quest::timers,$before_timers+100,'Nalin keeps his social cadence');
my $faced=@{$npc->{faced}};
$client->{x}=10;plugin::tunnel_social_idle($npc,$entities,'tunnel_social_idle');
is(scalar @{$npc->{faced}},$faced,'nearby interacting player prevents distraction');
$client->{x}=101;plugin::tunnel_social_idle($npc,$entities,'tunnel_social_idle');
is(scalar @{$npc->{faced}},$faced,'no observer means no animation traffic');
$client->{x}=80;$npc->{engaged}=1;plugin::tunnel_social_idle($npc,$entities,'tunnel_social_idle');
is(scalar @{$npc->{faced}},$faced,'combat prevents idle gestures');
$npc->{engaged}=0;plugin::tunnel_social_idle($npc,$entities,'another_timer');
is(scalar @{$npc->{faced}},$faced,'other quest timers are ignored');
$entities->{npcs}={};plugin::tunnel_social_idle($npc,$entities,'tunnel_social_idle');
is(scalar @{$npc->{faced}},$faced,'missing companions are harmless');
$entities->{npcs}=\%peers;
$_->{x}=100 for values %peers;
plugin::tunnel_social_idle($npc,$entities,'tunnel_social_idle');
is(scalar @{$npc->{faced}},$faced,'off-location companions are not faced');
$_->{x}=25 for values %peers;
plugin::tunnel_social_schedule($npc,1);
ok($quest::timers[-1][1]>=90 && $quest::timers[-1][1]<=135,'hail defers social animation');
my $timers=@quest::timers;
for my $id (999525,999527,997900,999700) {
    plugin::tunnel_social_schedule(bless({id=>$id},'Actor'),0);
}
is(scalar @quest::timers,$timers,'porters, merchants and walkers are outside ring timer scope');
for my $id (999520..999524,999526) {
    my $pkg='Resident'.$id;
    { no strict 'refs'; ${$pkg.'::npc'}=bless({id=>$id,vars=>{},faced=>[],animations=>[]},'Actor');
      ${$pkg.'::client'}=$client;${$pkg.'::entity_list'}=$entities;
      ${$pkg.'::text'}='Hail';${$pkg.'::timer'}='tunnel_social_idle'; }
    $!=0;
    eval "package $pkg; do '$root/quests/ecommons/$id.pl'";
    die $@ || $! if $@ || $!;
    { no strict 'refs';
      &{$pkg.'::EVENT_SPAWN'}();&{$pkg.'::EVENT_SAY'}();&{$pkg.'::EVENT_ITEM'}();
      is(${$pkg.'::npc'}->{returned},1,"$id returns wrong items and money");
      &{$pkg.'::EVENT_TIMER'}(); }
}
is_deeply([map { $_->[0] } @plugin::hails],[999520..999524],'five existing residents retain their hail handler');
like($quest::said[-1],qr/Good company/,'Glorphyndel now greets the player');
is(scalar @quest::ooc,0,'all quest entry points leave OOC coordination unchanged');
done_testing();
