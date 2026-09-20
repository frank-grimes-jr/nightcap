use strict;
use warnings;
use Test::More;

our $root = shift @ARGV or die 'Expected server-mods directory';
{
    package plugin;
    do "$main::root/plugins/living_economy.pl" or die $@ || $!;
}
{
    package MarketNPC;
    sub GetID { return 42; }
    sub ReturnHandinItems { $_[0]->{returned}++; }
    package MarketClient;
    sub LivingEconomy { push @{$_[0]->{hails}}, [@_[1,2]]; }
    sub MarketAnnouncement { push @{$_[0]->{announcements}}, [@_[1,2]]; }
    package MarketEntities;
    sub GetClientList { return @{$_[0]->{clients}}; }
    sub GetNPCByNPCTypeID {
        die 'Bad trader identity' if $_[1] < 999500 || $_[1] > 999509;
        $_[0]->{lookups}++;
        return $_[0]->{npc};
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
plugin::market_pulse($entities);
is($entities->{lookups},0,'empty zone never broadcasts');
plugin::market_hail($clients[0],$npc,'Hail');
is_deeply($clients[0]->{hails},[[42,'Hail']],'hail delegates to authoritative native trade API');
$entities->{clients}=\@clients;
srand(20260920);
plugin::market_pulse($entities) for 1..200;
is(scalar @{$clients[0]->{announcements}},200,'one announcement per pulse/client');
is_deeply($clients[0]->{announcements},$clients[1]->{announcements},'clients hear the same speaker and line');
ok(!(grep { $_->[0]!=42 || $_->[1]<0 || $_->[1]>13 } @{$clients[0]->{announcements}}),'bounded speaker and variants');
my $chatter=grep { $_->[1]>=8 } @{$clients[0]->{announcements}};
ok($chatter>10 && $chatter<80,'occasional chatter mixed with auctions');

$MarketController::client=$clients[0];
$MarketController::npc=$npc;
$MarketController::entity_list=$entities;
MarketController::EVENT_ITEM();
is($npc->{returned},1,'ordinary item/cash hand-in explicitly returns without relying on mutable rules');
MarketController::EVENT_SPAWN();
$MarketController::timer='market';
MarketController::EVENT_TIMER() for 1..100;
is(scalar @quest::timers,101,'single coordinator rearms cadence');
ok(!(grep { $_->[0] ne 'market' || $_->[1]<75 || $_->[1]>120 } @quest::timers),'cadence stays between 75 and 120 seconds');
$MarketController::timer='unrelated';
MarketController::EVENT_TIMER();
is(scalar @quest::timers,101,'unrelated timer ignored');
done_testing();
