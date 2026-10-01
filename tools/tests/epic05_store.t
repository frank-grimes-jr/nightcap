# Run only against a disposable schema created by rehearse_epic05.py.
use strict;
use warnings;
use Test::More;
use DBI;
our $schema=$ENV{NIGHTCAP_EPIC05_QA_DB}//'';
die 'Disposable Epic 0.5 schema required' unless $schema =~ /^nightcap_epic05_qa_[a-f0-9]{12}$/;
our $source=shift @ARGV or die 'Store source required';
our $ack_failure=0;
our $execute_failure=0;
{
    package Database;
    sub new {
        my $db=DBI->connect("DBI:mysql:database=$main::schema;host=mariadb",'eqemu','eqemu',
            {RaiseError=>1,PrintError=>0,AutoCommit=>1});
        return bless {db=>$db},shift;
    }
    sub prepare { bless {db=>$_[0]{db},statement=>$_[0]{db}->prepare($_[1]),sql=>$_[1]},'Statement'; }
    package Statement;
    sub execute {
        die 'injected execution failure' if $main::execute_failure;
        $_[0]{statement}->execute(@_[1..$#_]);
        die 'injected lost acknowledgement' if $main::ack_failure && $_[0]{sql}=~/^UPDATE/;
        return; # Match native void execute.
    }
    sub fetch_hashref { $_[0]{statement}->fetchrow_hashref() }
    sub rows_affected { $_[0]{statement}->rows() }
    package plugin;
    do $main::source or die $@ || $!;
}
my $db=Database->new()->{db};
ok(!plugin::epic05_store_enabled(),'release starts disabled');
ok(!plugin::epic05_store_attune(777,'guardian'),'disabled release blocks first attunement');
$db->do('UPDATE nightcap_epic05_control SET enabled=1 WHERE id=1');
ok(plugin::epic05_store_enabled(),'enabled candidate recognized');
ok(plugin::epic05_store_attune(777,'guardian'),'first attunement persisted');
is(plugin::epic05_store_state(777)->{active_path},'guardian','read returns persisted attunement');
ok(plugin::epic05_store_attune(777,'warden'),'earned caller can switch ready state');
ok(!plugin::epic05_store_reserve(777,'guardian'),'stale path cannot reserve');
ok(plugin::epic05_store_reserve(777,'warden'),'one activation reserves cooldown');
ok(!plugin::epic05_store_reserve(777,'warden'),'repeated activation refused');
ok(!plugin::epic05_store_attune(777,'binder'),'switch cannot reset cooldown');
cmp_ok(plugin::epic05_store_state(777)->{remaining},'>=',595,'new DB connection sees durable cooldown');
$db->do('UPDATE nightcap_epic05_state SET ready_at=0 WHERE character_id=777');
$execute_failure=1;
ok(!plugin::epic05_store_reserve(777,'warden'),'SQL exception fails closed');
$execute_failure=0;
is(plugin::epic05_store_state(777)->{remaining},0,'failed execution writes no timer');
$ack_failure=1;
ok(!plugin::epic05_store_reserve(777,'warden'),'uncertain acknowledgement fails closed');
$ack_failure=0;
ok(!plugin::epic05_store_reserve(777,'warden'),'lost acknowledgement never authorizes free retry');
$db->do('UPDATE nightcap_epic05_state SET ready_at=0,uses=0 WHERE character_id=777');
my @children;
for (1..4) {
    my $pid=fork(); die 'fork failed' unless defined $pid;
    if (!$pid) {
        $db->{InactiveDestroy}=1;
        exit(plugin::epic05_store_reserve(777,'warden') ? 11 : 12);
    }
    push @children,$pid;
}
my $winners=0;
for my $pid (@children) { waitpid($pid,0); $winners++ if ($? >> 8)==11; }
is($winners,1,'four concurrent connections grant exactly one activation');
is($db->selectrow_array('SELECT uses FROM nightcap_epic05_state WHERE character_id=777'),1,'one committed use after concurrent attempts');
$db->do('UPDATE nightcap_epic05_state SET ready_at=0 WHERE character_id=777');
$db->do('UPDATE nightcap_epic05_control SET enabled=0 WHERE id=1');
ok(!plugin::epic05_store_reserve(777,'warden'),'disable races cannot grant power');
ok(!plugin::epic05_store_attune(777,'binder'),'disable races cannot switch path');
is(plugin::epic05_store_state(777)->{active_path},'warden','disable retains attunement');
done_testing();
