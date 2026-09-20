sub EVENT_SAY { plugin::market_hail($client, $npc, $text); }
sub EVENT_SPAWN { quest::settimer("market", 75 + int(rand(46))); }
sub EVENT_TIMER { if ($timer eq "market") { plugin::market_pulse($entity_list); quest::settimer("market", 75 + int(rand(46))); } }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
