use strict;
use warnings;
use Test::More;
my ($second,$third)=(0,0);
my @messages;
my $reconciled=0;
{
    package Database;
    sub new { bless {},shift }
    sub prepare { bless {query=>$_[1]},'Statement' }
    package Statement;
    sub execute {
        my ($self,@args)=@_;
        $second=$args[1] if $self->{query}=~/INSERT INTO character_multiclass/;
        return 1;
    }
    sub fetch_hashref { return {class2=>$second,class3=>$third} }
    package MockClient;
    sub new { bless {},shift }
    sub GetClass { 1 }
    sub CharacterID { 100 }
    sub ReconcileMulticlassSkills { $reconciled++ }
    sub Message { push @messages,$_[2] }
    package plugin;
    my $loaded=do $ARGV[0];
    die $@ || $! unless $loaded;
}
my $client=MockClient->new();
my ($ok,$message)=plugin::mc_apply_class($client,2);
ok($ok,'existing class selection succeeds');
is($second,2,'selected class remains saved through the existing plugin');
is($reconciled,1,'native class and skill reconciliation remains invoked');
like($message,qr/class merchant near the PoK arrival point/,'player is directed to the new hub');
like($message,qr/Camp to the character screen/,'client refresh guidance stays visible');
unlike(join(' ',@messages,$message),qr/Operator note|\.ps1|Loremasters/,'player dialogue contains no operator commands or retired directions');
($ok,$message)=plugin::mc_apply_class($client,2);
ok(!$ok,'duplicate class remains rejected');
done_testing();
