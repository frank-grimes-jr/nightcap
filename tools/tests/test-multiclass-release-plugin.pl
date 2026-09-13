use strict;
use warnings;
use Test::More;
our ($second, $third, $calls, $result, $throws) = (2, 12, 0, 1, 0);
{
    package Database;
    sub new { bless {}, shift }
    sub prepare {
        die 'Quest attempted a separate database write' unless $_[1] =~ /^SELECT class2, class3 FROM character_multiclass/;
        bless {}, 'Statement';
    }
    package Statement;
    sub execute { 1 }
    sub fetch_hashref { {class2=>$main::second, class3=>$main::third} }
    package Client;
    sub new { bless {}, shift }
    sub CharacterID { 1 }
    sub ReleaseMulticlassSlot {
        ++$main::calls;
        die 'Native failure' if $main::throws;
        return $main::result;
    }
    package OldClient;
    sub new { bless {}, shift }
    sub CharacterID { die 'Missing binding must fail before reading state' }
    package plugin;
    my $loaded = do $ARGV[0];
    die $@ || $! unless $loaded;
}
my $c=Client->new;
for my $slot (undef, -1, 0, 1, 4, 258, '2x') {
    my ($ok)=plugin::mc_revoke_slot($c,$slot);
    ok(!$ok,'Invalid slot refused');
}
is($calls,0,'Invalid values never invoke native release');
my ($ok,$message)=plugin::mc_revoke_slot(OldClient->new,2);
ok(!$ok && $message =~ /unavailable/,'Missing native binding fails closed');
($ok,$message)=plugin::mc_revoke_slot($c,3);
ok($ok && $message =~ /Wizard/ && $message =~ /eligible AA/,'Native success reports the selected class and eligible refund');
is($calls,1,'Success performs exactly one native release');
$result=0;
($ok,$message)=plugin::mc_revoke_slot($c,2);
ok(!$ok && $message =~ /reconnect/,'Native rejection is not reported as success');
$throws=1;
($ok,$message)=plugin::mc_revoke_slot($c,2);
ok(!$ok && $message =~ /reconnect/,'Native exception is not reported as success');
$second=0;
my $previous=$calls;
($ok,$message)=plugin::mc_revoke_slot($c,2);
ok(!$ok && $message =~ /empty/,'Empty slot is refused');
is($calls,$previous,'Empty slot does not invoke native release');
done_testing();
