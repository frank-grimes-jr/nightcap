use strict;
use warnings;
use Test::More;
use FindBin;
our ($npc, $client, $signal, $text, $popupid, $zonesn);
our @moves;
our (@illusions, @speech, @lookups, @popups);
our $instance_id = 0;
{
    package Keeper;
    sub GetRace { $_[0]->{race} || 1 }
    sub GetLastName { 'permafrost' }
    sub GetID { 812 }
    sub GetNPCTypeID { $_[0]->{type} || 999232 }
    sub GetX { $_[0]->{x} // 35 }
    sub GetY { $_[0]->{y} // -82 }
    sub GetZ { $_[0]->{z} // 3.1 }
    sub GetHeading { $_[0]->{heading} // 0 }
    sub GMMove {
        my ($self, @pose) = @_;
        @{$self}{qw(x y z heading)} = @pose[0..3];
        push @main::moves, [@pose];
    }
    sub SendIllusionPacket { $_[0]->{race}=$_[1]->{race}; push @main::illusions,$_[1] }
    package Player;
    sub GetName { 'Tester' }
    sub CharacterID { 42 }
    sub GetGroup { undef }
    package quest;
    sub GetInstanceIDByCharID { push @main::lookups, [@_]; return $main::instance_id }
    sub GetInstanceTimerByID { 3660 }
    sub saylink { $_[0] }
    sub say { push @main::speech,$_[0] }
    sub popup { push @main::popups,[@_] }
}
$zonesn='permafrost';
$npc=bless {},'Keeper';
$client=bless {},'Player';
do "$FindBin::Bin/../../server-mods/quests/global/Instance_Keeper.pl" or die "$@ $!";
if (defined &EVENT_SPAWN) {
    EVENT_SPAWN();
    is_deeply($illusions[0],{race=>108,gender=>2,texture=>0,helmtexture=>0,size=>3},
        'globally loaded floating eye replaces human');
    is($npc->GetLastName(),'permafrost','destination metadata retained');
} else { fail('keeper applies appearance on spawn') }
if (defined &EVENT_SIGNAL) {
    $signal=1; EVENT_SIGNAL();
    is(scalar @illusions,1,'unrelated signal ignored');
    $signal=20261014; EVENT_SIGNAL(); EVENT_SIGNAL();
    is(scalar @illusions,1,'repeated refresh does not rebuild actor');
    $npc=bless {},'Keeper'; EVENT_SIGNAL();
    is($npc->GetRace(),108,'already spawned human can refresh without respawn');
} else { fail('keeper supports live refresh') }
is(scalar @lookups,0,'appearance does not read or mutate instance state');
$text='hail'; EVENT_SAY();
like($speech[-1],qr/private instance of permafrost/,'hail still offers correct dungeon');
is_deeply($lookups[-1],['permafrost',0,42],'same character and instance version');
$instance_id=123; EVENT_SAY();
like($speech[-1],qr/Welcome back/,'active instance recognized');
$text='status'; EVENT_SAY();
like($speech[-1],qr/1h 1m remaining/,'status preserved');
$text='join'; EVENT_SAY();
like($speech[-1],qr/must be grouped/,'join validation preserved');
$text='reset'; EVENT_SAY();
is($popups[-1]->[2],501,'reset still requires existing confirmation popup');
$instance_id=0; EVENT_SAY();
like($speech[-1],qr/no active instance to reset/,'reset without instance stays harmless');

{
    package NativePlayer;
    our @ISA=('Player');
    sub DungeonAction { push @main::native_actions, [$_[1],$_[2]]; return 1; }
}
our @native_actions;
$client=bless {},'NativePlayer';
my $legacy_lookups=scalar @lookups;
$text='RAID'; EVENT_SAY();
is_deeply($native_actions[-1],[812,'raid'],'managed dialogue reaches native Keeper with normalized action');
is(scalar @lookups,$legacy_lookups,'handled native action never reaches legacy lookup');
$popupid=501; EVENT_POPUPRESPONSE();
is_deeply($native_actions[-1],[812,'confirm reset'],'legacy popup must pass native reset authorization');
is(scalar @lookups,$legacy_lookups,'managed popup never reaches legacy destruction');
$popupid=502; EVENT_POPUPRESPONSE();
is(scalar @native_actions,2,'unrelated popup ignored');

# The live Befallen keeper and portal share XYZ 35,-82,3.1. These checks
# model fresh/saved poses at the quest boundary plus an already-running eye.
# Native saved-state load ordering is reviewed separately, not executed here.
$zonesn = 'befallen';
$npc = bless {type=>999227}, 'Keeper';
EVENT_SPAWN();
is_deeply($moves[-1], [35,-67,3.1,256,1],
    'Befallen spawn separates the eye from the portal and saves its guard spot');
is($npc->GetRace(),108,'Befallen keeps the floating-eye appearance');
my $count = scalar @moves;
$signal=20261022; EVENT_SIGNAL(); EVENT_SIGNAL();
is(scalar @moves,$count,'new refresh is idempotent at the clear position');
$npc=bless {type=>999227,race=>108,z=>3},'Keeper';
EVENT_SIGNAL();
is(scalar @moves,$count+1,'existing eye moves even when illusion is already correct');
is_deeply($moves[-1],[35,-67,3.1,256,1],'live refresh uses the same fixed pose');
$npc=bless {type=>999227,race=>108},'Keeper';
$signal=20261014; EVENT_SIGNAL();
is(scalar @moves,$count+2,'existing visual refresh also corrects the overlap');
$npc=bless {type=>999227,race=>108},'Keeper';
$signal=123; EVENT_SIGNAL();
is(scalar @moves,$count+2,'unrelated signal cannot relocate a keeper');
$signal=20261022;
$npc=bless {type=>999228,race=>108},'Keeper'; EVENT_SIGNAL();
is(scalar @moves,$count+2,'other Keeper NPC types are not relocated');
$zonesn='unrest';
$npc=bless {type=>999227,race=>108},'Keeper'; EVENT_SIGNAL();
is(scalar @moves,$count+2,'wrong zone is not relocated even with the Befallen NPC type');
$zonesn='befallen';
$npc=bless {type=>999227,race=>108,x=>35,y=>-67,z=>3.2,heading=>256},'Keeper';
EVENT_SPAWN();
is(scalar @moves,$count+2,'native ground offset does not cause repeated movement');
is(scalar @lookups,$legacy_lookups,'visual correction never reads or changes dungeon state');
is(scalar @native_actions,2,'visual correction never invokes a dungeon action');

# Every audited overlap gets an absolute pose; already-separate dungeons do not.
my @placements = (
    ['unrest',999228,67,-38,3.1,384],
    ['najena',999230,858,-61,4.1,256],
    ['permafrost',999232,46,-121,2.1,128],
    ['soldungb',999233,-248,-424,-108,384],
);
for my $row (@placements) {
    my ($zone,$type,@pose)=@$row;
    $zonesn=$zone; $npc=bless {type=>$type,race=>108},'Keeper';
    EVENT_SPAWN();
    is_deeply($moves[-1],[@pose,1],"$zone separates an existing eye on spawn");
    my $before=scalar @moves;
    $signal=20261022; EVENT_SIGNAL(); EVENT_SIGNAL();
    is(scalar @moves,$before,"$zone repeat refresh is idempotent");
    $npc=bless {type=>$type},'Keeper'; EVENT_SIGNAL();
    is_deeply($moves[-1],[@pose,1],"$zone loaded Keeper moves to fixed pose");
    $before=scalar @moves;
    $npc=bless {type=>999229,race=>108},'Keeper'; EVENT_SIGNAL();
    is(scalar @moves,$before,"$zone wrong type is never moved");
}
for my $row (['highkeep',999229],['cazicthule',999231]) {
    ($zonesn,my $type)=@$row;
    my $before=scalar @moves;
    $npc=bless {type=>$type},'Keeper'; EVENT_SPAWN();
    $signal=20261022; EVENT_SIGNAL();
    is(scalar @moves,$before,"$zonesn separate placement preserved");
    is($npc->GetRace(),108,"$zonesn shared appearance retained");
}
is(scalar @lookups,$legacy_lookups,'all-zone placement never reads dungeon state');
is(scalar @native_actions,2,'all-zone placement never invokes dungeon actions');

done_testing();
