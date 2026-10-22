use strict;use warnings;use Test::More;use FindBin;
our($npc,$zonesn,$signal);our @moves;
{ package Keeper;
sub GetRace {108} sub GetNPCTypeID {$_[0]->{id}}
sub GetX {$_[0]->{x}} sub GetY {$_[0]->{y}} sub GetZ {$_[0]->{z}} sub GetHeading {$_[0]->{heading}}
sub GMMove {my($self,@pose)=@_;@{$self}{qw(x y z heading)}=@pose[0..3];push @main::moves,[@pose];}
}
do "$FindBin::Bin/Instance_Keeper.recovery.pl" or die "$@ $!";
$zonesn='befallen';$npc=bless {id=>999227,x=>35,y=>-67,z=>3.1,heading=>256},'Keeper';$signal=20261022;EVENT_SIGNAL();
is(scalar @moves,0,'Befallen prior correction retained');
my $countbefallen=scalar @moves;EVENT_SIGNAL();is(scalar @moves,$countbefallen,'befallen recovery idempotent');
$zonesn='unrest';$npc=bless {id=>999228,x=>67,y=>-38,z=>3.1,heading=>384},'Keeper';$signal=20261022;EVENT_SIGNAL();
is_deeply($moves[-1],[52,-38,3.1,0,1],'unrest inverse position and guard');
my $countunrest=scalar @moves;EVENT_SIGNAL();is(scalar @moves,$countunrest,'unrest recovery idempotent');
$zonesn='najena';$npc=bless {id=>999230,x=>858,y=>-61,z=>4.1,heading=>256},'Keeper';$signal=20261022;EVENT_SIGNAL();
is_deeply($moves[-1],[858,-76,4.1,0,1],'najena inverse position and guard');
my $countnajena=scalar @moves;EVENT_SIGNAL();is(scalar @moves,$countnajena,'najena recovery idempotent');
$zonesn='permafrost';$npc=bless {id=>999232,x=>46,y=>-121,z=>2.1,heading=>128},'Keeper';$signal=20261022;EVENT_SIGNAL();
is_deeply($moves[-1],[61,-121,2.1,0,1],'permafrost inverse position and guard');
my $countpermafrost=scalar @moves;EVENT_SIGNAL();is(scalar @moves,$countpermafrost,'permafrost recovery idempotent');
$zonesn='soldungb';$npc=bless {id=>999233,x=>-248,y=>-424,z=>-108,heading=>384},'Keeper';$signal=20261022;EVENT_SIGNAL();
is_deeply($moves[-1],[-263,-424,-107.9,0,1],'soldungb inverse position and guard');
my $countsoldungb=scalar @moves;EVENT_SIGNAL();is(scalar @moves,$countsoldungb,'soldungb recovery idempotent');
done_testing();
