use strict;
use warnings;
use Test::More;
use FindBin;
our ($npc, $client, $signal, $text, $popupid);
our (@illusions, @speech, @lookups, @popups);
our $instance_id = 0;
{
    package Keeper;
    sub GetRace { $_[0]->{race} || 1 }
    sub GetLastName { 'permafrost' }
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
done_testing();
