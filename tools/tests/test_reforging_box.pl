use strict;
use warnings;
use Test::More;
use FindBin;

our ($text, $client, $npc, @awards, @said, $owned, $returned);
{
    package quest;
    sub say { push @main::said, $_[0]; }
    sub saylink { return $_[2]; }
    sub summonitem { push @main::awards, $_[0]; }
    package TestClient;
    sub CountItem { die 'wrong container ID' unless $_[1] == 900620; return $main::owned; }
    package TestNPC;
    sub ReturnHandinItems { ++$main::returned; }
}
$client = bless {}, 'TestClient';
$npc = bless {}, 'TestNPC';
$owned = 0;
my $script = "$FindBin::Bin/../../server-mods/quests/ecommons/999820.pl";
do $script or die "$script: $@ $!";
$text = 'Hail'; EVENT_SAY();
like($said[-1], qr/four identical Polished/, 'hail explains four-for-one');
like($said[-1], qr/reusable/, 'hail explains reusable container');
is(scalar @awards, 0, 'hail does not fill cursor');
$text = 'box'; EVENT_SAY();
is_deeply(\@awards, [900620], 'box request awards the specific free container');
$owned = 1; EVENT_SAY();
is(scalar @awards, 1, 'existing owner is not given another box');
$returned = 0; EVENT_ITEM();
is($returned, 1, 'NPC returns unintended hand-ins through native instance return');
done_testing();
