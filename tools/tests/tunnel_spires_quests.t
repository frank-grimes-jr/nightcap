use strict;
use warnings;
use Test::More;
our $root=shift @ARGV or die 'Expected server-mods root';
{
    package plugin;
    do "$main::root/plugins/tunnel_spire_data.pl" or die $@ || $!;
    do "$main::root/plugins/tunnel_spires.pl" or die $@ || $!;
    package quest;
    our $era=0; our @said;
    sub get_rule { return $era; }
    sub say { push @said,$_[0]; }
    sub saylink { return '['.$_[0].']'; }
    package SpireNPC;
    sub GetNPCTypeID { return $_[0]->{id}//999527; }
    sub GetX { 0 } sub GetY { 0 } sub GetZ { 0 }
    sub ReturnHandinItems { $_[0]->{returned}++ }
    package SpireClient;
    sub GetZoneID { $_[0]->{zone}//22 } sub GetInstanceID { $_[0]->{instance}//0 }
    sub GetX { $_[0]->{x}//0 } sub GetY { 0 } sub GetZ { 0 }
    sub GetLevel { $_[0]->{level}//50 } sub GetHP { $_[0]->{hp}//100 }
    sub GetAggroCount { $_[0]->{combat}//0 } sub IsCasting { $_[0]->{casting}//0 }
    sub IsStunned { $_[0]->{stunned}//0 } sub IsMezzed { $_[0]->{mezzed}//0 } sub IsFeared { $_[0]->{feared}//0 }
    sub GetEntityVariable { $_[0]->{cooldown}//0 } sub SetEntityVariable { $_[0]->{cooldown}=$_[2] }
    sub MovePC { push @{$_[0]->{moves}},[@_[1..5]] }
    package KhaleidQuest;
    our ($client,$npc,$text);
    do "$main::root/quests/ecommons/999527.pl";
    die $@ || $! if $@ || $!;
}
my $npc=bless {},'SpireNPC';
my $c=bless {moves=>[]},'SpireClient';
plugin::tunnel_spire_hail($c,$npc,'Hail');
is(scalar(()=join(' ',@quest::said)=~/\[spire /g),9,'nine Classic destinations');
like(join(' ',@quest::said),qr/\[spire airplane\]/,'Plane of Sky offered at 46+');
unlike(join(' ',@quest::said),qr/spire (hateplane|nexus|dreadlands|toxxulia|northro|commonlands)/,'no unlisted planes, later-era or replacement-zone routes');
{
    local @quest::said;my $low=bless {moves=>[],level=>45},'SpireClient';
    plugin::tunnel_spire_hail($low,$npc,'Hail');
    unlike(join(' ',@quest::said),qr/airplane/,'Plane of Sky hidden below 46');
    plugin::tunnel_spire_hail($low,$npc,'spire airplane');
    is(scalar @{$low->{moves}},0,'Plane of Sky refused below 46');
}
like(join(' ',@quest::said),qr/dangerous temple/,'temple landing is clearly labelled');
for my $r (@{plugin::tunnel_spire_catalog()}) {
    $c->{cooldown}=0;plugin::tunnel_spire_hail($c,$npc,'spire '.$r->{zone});
    is_deeply($c->{moves}[-1],[@$r{qw(zone_id x y z heading)}],$r->{zone}.' uses exact catalog landing');
}
my $count=scalar @{$c->{moves}};
plugin::tunnel_spire_hail($c,$npc,'spire tox');is(scalar @{$c->{moves}},$count,'cooldown blocks repeat');
$c->{cooldown}=0;
for my $bad ('spire hateplane','spire nexus','spire dreadlands','spire northro','spire tox 99',"spire tox\n",'spire 38','ring commons') {
    plugin::tunnel_spire_hail($c,$npc,$bad);
}
is(scalar @{$c->{moves}},$count,'forged/stale/malformed commands never travel');
for my $state ({zone=>202},{instance=>1},{x=>101},{hp=>0},{combat=>1},{casting=>1},{stunned=>1},{mezzed=>1},{feared=>1}) {
    my $blocked=bless {moves=>[],%$state},'SpireClient';
    plugin::tunnel_spire_hail($blocked,$npc,'spire tox');
    is(scalar @{$blocked->{moves}},0,'zone/instance/range/recovery guard');
}
for my $era (undef,'',-1,'bad',31,"0\n") {
    $quest::era=$era;plugin::tunnel_spire_hail($c,$npc,'spire tox');
}
is(scalar @{$c->{moves}},$count,'unknown era fails closed');
$quest::era=0;$npc->{id}=999525;plugin::tunnel_spire_hail($c,$npc,'spire tox');
is(scalar @{$c->{moves}},$count,'Khalure cannot dispatch wizard travel');
$KhaleidQuest::client=$c;$KhaleidQuest::npc=$npc;KhaleidQuest::EVENT_ITEM();
is($npc->{returned},1,'items and money return through native API');
$npc->{id}=999527;@quest::said=();$KhaleidQuest::text='Hail';KhaleidQuest::EVENT_SAY();
is(scalar(()=join(' ',@quest::said)=~/\[spire /g),9,'numeric quest adapter exposes the wizard menu');
done_testing();
