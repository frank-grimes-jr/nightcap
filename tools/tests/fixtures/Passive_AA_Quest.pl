# QA fixture only: copy into quests/arena/ on an isolated test server, then
# #spawn Passive_AA_Quest 1 1 0 10000 0 1. Never install in production.
use strict;
use warnings;
our ($text, $client, $status);

sub EVENT_SAY {
    return unless $client && $status >= 200;
    if ($text eq 'raw') {
        quest::exp(10000);
    } elsif ($text eq 'percent') {
        $client->AddLevelBasedExp(10);
    } elsif ($text eq 'zero') {
        quest::exp(0);
    } else {
        quest::say('QA only: raw grants 10000 base XP; percent grants 10 percent of this level; zero grants nothing.');
    }
}
