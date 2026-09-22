use strict;
use warnings;
use Test::More;
use JSON::PP;
use File::Spec;
our $root=shift @ARGV or die 'Expected repository root';
my $runtime=shift @ARGV;
our ($travel_data,$travel_plugin,$travel_quest);
if (defined $runtime) {
    # Follow EQEmuConfig and PathManager: nonempty path arrays override scalars.
    # Probe the installed tree, never a repository copy of the plugin.
    open my $config,'<',"$runtime/eqemu_config.json" or die $!;
    my $directories=decode_json(do { local $/; <$config> })->{server}{directories}//{};
    my $locate=sub {
        my ($array,$scalar,$default,$file)=@_;
        my @paths=ref($directories->{$array}) eq 'ARRAY'
            ? grep { defined($_) && !ref($_) } @{$directories->{$array}} : ();
        @paths=($directories->{$scalar}//$default) unless @paths;
        my @matches=grep { -f $_ } map {
            File::Spec->catfile(File::Spec->rel2abs($_,$runtime),$file)
        } @paths;
        die "Expected one loaded $file in configured $array; found ".scalar(@matches)."\n"
            unless @matches==1;
        return $matches[0];
    };
    $travel_data=$locate->('plugin_paths','plugins','plugins/','tunnel_travel_data.pl');
    $travel_plugin=$locate->('plugin_paths','plugins','plugins/','tunnel_travel.pl');
    $travel_quest=$locate->('quest_paths','quests','quests/','ecommons/999810.pl');
    diag("Installed runtime: $travel_plugin; $travel_data; $travel_quest");
} else {
    $travel_data="$root/server-mods/plugins/tunnel_travel_data.pl";
    $travel_plugin="$root/server-mods/plugins/tunnel_travel.pl";
    $travel_quest="$root/server-mods/quests/ecommons/999810.pl";
}
{
    package plugin;
    do $main::travel_data or die $@ || $!;
    do $main::travel_plugin or die $@ || $!;
    package quest;
    our @said;
    sub say { push @said,$_[0]; }
    sub saylink { return '['.$_[0].']'; }
    package TravelNPC;
    sub GetNPCTypeID { $_[0]->{id}//999810 }
    sub GetX { 0 } sub GetY { 0 } sub GetZ { 0 }
    package TravelClient;
    sub GetZoneID { $_[0]->{zone}//22 }
    sub GetInstanceID { $_[0]->{instance}//0 }
    sub GetX { $_[0]->{x}//0 } sub GetY { 0 } sub GetZ { $_[0]->{z}//0 }
    sub GetHP { $_[0]->{hp}//100 }
    sub GetAggroCount { $_[0]->{combat}//0 }
    sub IsCasting { $_[0]->{casting}//0 }
    sub IsStunned { $_[0]->{stunned}//0 }
    sub IsMezzed { $_[0]->{mezzed}//0 }
    sub IsFeared { $_[0]->{feared}//0 }
    sub GetEntityVariable { $_[0]->{cooldown}//0 }
    sub SetEntityVariable { $_[0]->{cooldown}=$_[2] }
    sub MovePC { push @{$_[0]->{moves}},[@_[1..5]] }
    package TravelQuest;
    our($client,$npc,$text);
    do $main::travel_quest or die $@ || $!;
}
my $npc=bless {},'TravelNPC';
my $client=bless {moves=>[]},'TravelClient';
plugin::tunnel_travel_hail($client,$npc,'Hail');
is(scalar(()=join(' ',@quest::said)=~/\[travel /g),10,'hail offers ten destinations');
open my $file,'<',"$root/docs/ecommons-hub/plan.json" or die $!;
my $plan=decode_json(do { local $/; <$file> });
my %zone=(qeynos2=>2,freportw=>9,gfaydark=>54,butcher=>68,everfrost=>30,
          misty=>33,nektulos=>25,feerrott=>47,innothule=>46,tox=>38);
for my $door (grep { $_->{zone} eq 'ecommons' && $_->{id}<40610 } @{$plan->{doors}}) {
    $client->{cooldown}=0;
    plugin::tunnel_travel_hail($client,$npc,'travel '.$door->{dest_zone});
    is_deeply($client->{moves}[-1],[$zone{$door->{dest_zone}},map { $door->{'dest_'.$_} } qw(x y z heading)],
              'preserves '.$door->{dest_zone}.' exact landing and heading');
}
my $count=@{$client->{moves}};
plugin::tunnel_travel_hail($client,$npc,'travel qeynos2');
is(scalar @{$client->{moves}},$count,'repeat click does not issue another zone request');
$client->{cooldown}=0;
for my $input ('travel poknowledge','travel nexus','travel 2','travel qeynos2 1 2 3',
               'travel qeynos2; DROP TABLE doors','travel commonlands','travel qeynos2 extra') {
    plugin::tunnel_travel_hail($client,$npc,$input);
}
is(scalar @{$client->{moves}},$count,'forged and unsupported destinations never move player');
for my $state ({x=>51},{z=>51},{zone=>202},{instance=>1},{hp=>0},{combat=>1},
               {casting=>1},{stunned=>1},{mezzed=>1},{feared=>1}) {
    my $blocked=bless {moves=>[],%$state},'TravelClient';
    plugin::tunnel_travel_hail($blocked,$npc,'travel qeynos2');
    is(scalar @{$blocked->{moves}},0,'unavailable player state blocks travel');
}
plugin::tunnel_travel_hail($client,bless({id=>999525},'TravelNPC'),'travel qeynos2');
is(scalar @{$client->{moves}},$count,'wrong NPC cannot provide city travel');
($TravelQuest::client,$TravelQuest::npc,$TravelQuest::text)=($client,$npc,'Hail');
@quest::said=();TravelQuest::EVENT_SAY();
like(join(' ',@quest::said),qr/travel qeynos2/,'numeric quest adapter exposes the menu');
done_testing();
