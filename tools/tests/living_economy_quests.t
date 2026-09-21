use strict;
use warnings;
use Test::More;

our $root = shift @ARGV or die 'Expected server-mods directory';
{
    package plugin;
    do "$main::root/plugins/tunnel_chatter.pl" or die $@ || $!;
    do "$main::root/plugins/living_economy.pl" or die $@ || $!;
}
{
    package MarketNPC;
    sub GetID { return $_[0]->{id}//42; }
    sub GetEntityVariable { return $_[0]->{$_[1]}; }
    sub SetEntityVariable { $_[0]->{$_[1]}=$_[2]; }
    sub ReturnHandinItems { $_[0]->{returned}++; }
    package MarketClient;
    sub LivingEconomy { push @{$_[0]->{hails}}, [@_[1,2]]; }
    sub MarketAnnouncement { push @{$_[0]->{announcements}}, [@_[1,2]]; }
    sub TunnelChatter { push @{$_[0]->{chatter}}, [@_[1,2]]; }
    package MarketEntities;
    sub GetClientList { return @{$_[0]->{clients}}; }
    sub GetNPCByNPCTypeID {
        $_[0]->{lookups}++;
        return bless {id=>$_[1]},'MarketNPC';
    }
    package quest;
    our @timers;
    sub settimer { push @timers, [@_]; }
    package MarketController;
    our ($client,$npc,$text,$timer,$entity_list);
    do "$main::root/quests/ecommons/999500.pl";
    die $@ || $! if $@ || $!;
}

my $npc = bless {}, 'MarketNPC';
my @clients = map { bless {hails=>[],announcements=>[]}, 'MarketClient' } 1..2;
my $entities = bless {clients=>[],npc=>$npc,lookups=>0}, 'MarketEntities';
plugin::market_pulse($entities,$npc);
plugin::tunnel_chatter_pulse($entities,$npc);
is($entities->{lookups},0,'empty zone never broadcasts');
plugin::market_hail($clients[0],$npc,'Hail');
is_deeply($clients[0]->{hails},[[42,'Hail']],'hail delegates to authoritative native trade API');
$entities->{clients}=\@clients;
srand(20260920);
plugin::market_pulse($entities,$npc) for 1..200;
is(scalar @{$clients[0]->{announcements}},200,'one announcement per pulse/client');
is_deeply($clients[0]->{announcements},$clients[1]->{announcements},'clients hear the same speaker and line');
my %actors=map { $_=>1 } plugin::tunnel_market_ids();
is(scalar keys %actors,16,'all sixteen real traders can advertise');
ok(!(grep { !$actors{$_->[0]} || $_->[1]<0 || $_->[1]>=600 } @{$clients[0]->{announcements}}),'bounded speaker and variants');
my %heard=map { $_->[0]=>1 } @{$clients[0]->{announcements}};
is(scalar keys %heard,16,'random sample reaches old and new traders');
plugin::tunnel_chatter_pulse($entities,$npc) for 1..300;
is_deeply($clients[0]->{chatter},$clients[1]->{chatter},'all clients hear the same OOC line');
my (%lines,$last);
my $no_repeat=1;
for my $line (@{$clients[0]->{chatter}}) {
    $no_repeat=0 if defined($last) && $last==$line->[0];
    $no_repeat=0 if exists($lines{$line->[0]}) && $lines{$line->[0]} eq $line->[1];
    $last=$line->[0]; $lines{$line->[0]}=$line->[1];
}
ok($no_repeat,'no consecutive speaker or repeated line for a voice');
is(scalar keys %lines,14,'six residents and eight walkers speak');

$MarketController::client=$clients[0];
$MarketController::npc=$npc;
$MarketController::entity_list=$entities;
MarketController::EVENT_ITEM();
is($npc->{returned},1,'ordinary item/cash hand-in explicitly returns without relying on mutable rules');
MarketController::EVENT_SPAWN();
$MarketController::timer='market';
MarketController::EVENT_TIMER() for 1..100;
is(scalar @quest::timers,102,'single coordinator rearms market and owns one OOC timer');
ok(!(grep { $_->[0] eq 'market' && ($_->[1]<30 || $_->[1]>55) } @quest::timers),'auction cadence stays between 30 and 55 seconds');
$MarketController::timer='tunnel_chatter';
MarketController::EVENT_TIMER() for 1..100;
ok(!(grep { $_->[0] eq 'tunnel_chatter' && ($_->[1]<45 || $_->[1]>80) } @quest::timers),'OOC cadence stays between 45 and 80 seconds');
$MarketController::timer='unrelated';
MarketController::EVENT_TIMER();
is(scalar @quest::timers,202,'unrelated timer ignored');
done_testing();
