sub EVENT_SAY { plugin::market_hail($client, $npc, $text); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
