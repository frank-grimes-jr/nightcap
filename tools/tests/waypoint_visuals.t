use strict;
use warnings;
use Test::More;
use FindBin;

our ($npc, $client, $signal, $zonesn);
our (@proximity, @messages, @writes, @effects, @illusions);
our $inserted = 1;
our $found = 1;
our $title_count = 0;
{
    package Marker;
    sub GetX { 35 }
    sub GetY { -82 }
    sub GetZ { 3 }
    sub GetRace { $_[0]->{race} || 1 }
    sub GetGender { $_[0]->{gender} || 0 }
    sub SendIllusionPacket {
        $_[0]->{race} = $_[1]->{race}; $_[0]->{gender} = $_[1]->{gender};
        push @main::illusions, $_[1];
    }
    sub GetNimbusEffect1 { $main::effects[0] || 0 }
    sub GetNimbusEffect2 { $main::effects[1] || 0 }
    sub GetNimbusEffect3 { $main::effects[2] || 0 }
    sub AddNimbusEffect { push @main::effects, $_[1] }
    package Player;
    sub CharacterID { 42 }
    sub Message { push @main::messages, $_[2] }
    package Database;
    sub new { bless {}, shift }
    sub prepare { bless {sql => $_[1]}, 'Statement' }
    package Statement;
    sub execute { push @main::writes, [$_[0]->{sql}, @_[1..$#_]] }
    sub rows_affected { $main::inserted }
    sub fetch_hashref { { found => $main::found, total => 72 } }
    package quest;
    sub set_proximity { @main::proximity = @_ }
    sub enabletitle { $main::title_count++ }
}
$npc = bless {}, 'Marker';
$client = bless {}, 'Player';
$zonesn = 'befallen';
my $file = "$FindBin::Bin/../../server-mods/quests/global/999240.pl";
do $file or die "Load $file: $@ $!";
EVENT_SPAWN();
is_deeply(\@proximity, [10,60,-107,-57,-27,33], 'discovery box unchanged');
is($illusions[0]->{race}, 425, 'waypoint has a persistent crystal mesh');
is($illusions[0]->{gender}, 2, 'crystal uses its neutral model');
is_deeply(\@effects, [178], 'one persistent WizardPortal effect');
if (defined &EVENT_SIGNAL) {
    $signal = 1;
    EVENT_SIGNAL();
    is(scalar @illusions, 1, 'unrelated signal ignored');
    $signal = 20261011;
    EVENT_SIGNAL();
    EVENT_SIGNAL();
    is(scalar @illusions, 1, 'refresh does not rebuild an already correct actor');
    is_deeply(\@effects, [178], 'refresh cannot stack portal effects');
    $npc = bless {}, 'Marker';
    @effects = ();
    EVENT_SIGNAL();
    is($npc->GetRace(), 425, 'live marker refreshed without respawn');
    is_deeply(\@effects, [178], 'live marker receives portal');
    @effects = (450,178);
    EVENT_SIGNAL();
    is_deeply(\@effects, [450,178], 'existing nimbus slots retained without duplicates');
    $npc = bless {race => 127}, 'Marker';
    $signal = 20261022;
    EVENT_SIGNAL();
    is($npc->GetRace(), 425, 'new refresh upgrades an existing invisible marker');
    $npc = bless {race => 425, gender => 0}, 'Marker';
    EVENT_SIGNAL();
    is($npc->GetGender(), 2, 'refresh repairs a crystal with the wrong gender');
} else { fail('waypoint supports refresh of already spawned markers') }
is(scalar @writes, 0, 'visual application never writes discoveries');
EVENT_ENTER();
is_deeply([@{$writes[0]}[1,2]], [42,'befallen'], 'discovery still scoped to player and zone');
like($messages[0], qr/attune/, 'new discovery announced');
is(scalar @messages, 2, 'new discovery reports progress');
$inserted = 0;
@messages = ();
EVENT_ENTER();
is(scalar @messages, 0, 'repeat discovery remains silent');
is($title_count, 0, 'partial discovery gives no title');
$inserted = 1;
$found = 72;
EVENT_ENTER();
is($title_count, 1, 'Explorer completion preserved');
done_testing();
