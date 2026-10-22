use strict;
use warnings;
use Test::More;
use FindBin;
our ($npc,$signal,$zonesn);
our @moves;
{
 package Keeper;
 sub GetNPCTypeID { $_[0]->{type} // 999227 }
 sub GetRace { 108 }
 sub GetX { $_[0]->{x} // 35 }
 sub GetY { $_[0]->{y} // -67 }
 sub GetZ { $_[0]->{z} // 3.1 }
 sub GetHeading { $_[0]->{h} // 256 }
 sub GMMove { my ($self,@pose)=@_; @{$self}{qw(x y z h)}=@pose[0..3]; push @main::moves,[@pose] }
}
$zonesn='befallen'; $npc=bless {},'Keeper';
do "$FindBin::Bin/Instance_Keeper.recovery.pl" or die "$@ $!";
EVENT_SPAWN();
is_deeply($moves[-1],[35,-82,3.1,0,1],'saved relocated eye returns to original pose and guard');
$signal=20261022; EVENT_SIGNAL();
is(scalar @moves,1,'repeated recovery does not move the restored eye');
$npc=bless {},'Keeper'; EVENT_SIGNAL();
is(scalar @moves,2,'loaded relocated eye recovers without respawn');
$npc=bless {type=>999228},'Keeper'; EVENT_SIGNAL();
is(scalar @moves,2,'another Keeper cannot move');
$zonesn='unrest'; $npc=bless {},'Keeper'; EVENT_SPAWN();
is(scalar @moves,2,'another zone cannot move');
$zonesn='befallen'; $signal=1; EVENT_SIGNAL();
is(scalar @moves,2,'unrelated signal cannot move');
done_testing();
