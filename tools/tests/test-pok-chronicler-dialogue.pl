use strict;
use warnings;
use Test::More;

our ($client, $text, $popupid);
my @messages;
my @popups;
my ($second, $third) = (0, 0);
my $mutations = 0;
my $reject = 0;
my %classes = (1 => 'Warrior', 2 => 'Cleric', 12 => 'Wizard');
{
    package MockClient;
    sub new { bless {}, shift }
    sub GetName { 'Tester' }
    sub GetClass { 1 }
    sub GetLevel { 50 }
    sub CharacterID { 100 }
    sub Message { push @messages, $_[2] }
}
{
    package quest;
    sub say { push @messages, $_[0] }
    sub saylink { return $_[2] // $_[0] }
    sub popup { push @popups, [@_] }
}
{
    package plugin;
    sub mc_class_name { return $classes{$_[0]} // 'Other' }
    sub mc_class_id_by_name {
        for my $id (keys %classes) { return $id if lc($classes{$id}) eq lc($_[0]) }
        return 0;
    }
    sub mc_flavor { 'a distinct combat role' }
    sub mc_get_classes { return ($second, $third) }
    sub mc_preview { die 'Outdated preview counts must not be used' }
    sub mc_apply_class {
        return (0, 'Selection was not saved') if $reject;
        ++$mutations;
        if (!$second) { $second = $_[1] } else { $third = $_[1] }
        return (1, 'Selection saved');
    }
    sub mc_revoke_slot {
        ++$mutations;
        if ($_[1] == 2) { $second = $third; $third = 0 } else { $third = 0 }
        return (1, 'Class released');
    }
}
$client = MockClient->new();
my $file = shift @ARGV or die 'Pass the Chronicler script path';
do $file or die "Cannot load $file: $@ $!";
$text = 'hail'; EVENT_SAY();
ok(grep($_ eq 'Your classes: Warrior (Primary) | Not selected (Second) | Not selected (Third)', @messages), 'hail shows all slots');
is($mutations, 0, 'hail never selects a class');
@messages = (); $text = 'Cleric'; EVENT_SAY();
ok(grep(/skills improve through use and training/, @messages), 'preview explains earned skill progression');
is($mutations, 0, 'preview never selects a class');
$text = 'embrace Cleric'; EVENT_SAY();
is($popups[-1][2], 302, 'selection opens the expected confirmation');
is($mutations, 0, 'opening confirmation does not mutate classes');
$popupid = 0; EVENT_POPUPRESPONSE();
is($mutations, 0, 'dismissal ID never selects a class');
is($second, 0, 'dismissal leaves the class slot empty');
@messages = (); $popupid = 302; EVENT_POPUPRESPONSE();
is($second, 2, 'confirmed selection uses existing class plugin');
ok(grep($_ eq 'Your classes: Warrior (Primary) | Cleric (Second) | Not selected (Third)', @messages), 'selection response immediately rereads saved slots');
@messages = (); $reject = 1; $popupid = 312; EVENT_POPUPRESPONSE();
is($third, 0, 'failed selection does not fill a slot');
ok(grep(/Selection was not saved/, @messages), 'failure stays visible');
ok(grep(/Not selected \(Third\)/, @messages), 'failure displays the unchanged slots');
$reject = 0; $popupid = 312; EVENT_POPUPRESPONSE();
@messages = (); $text = 'my classes'; EVENT_SAY();
ok(grep(/Warrior \(Primary\).*Cleric \(Second\).*Wizard \(Third\)/, @messages), 'status works with all three slots filled');
$text = 'release second'; EVENT_SAY();
unlike($popups[-1][1], qr/dormant|skills already trained remain/, 'release no longer promises the obsolete retention behavior');
@messages = (); $popupid = 402; EVENT_POPUPRESPONSE();
ok(grep(/Wizard \(Second\).*Not selected \(Third\)/, @messages), 'release immediately shows promoted slot state');
done_testing();
