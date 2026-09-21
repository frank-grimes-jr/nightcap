sub EVENT_SAY { plugin::tunnel_travel_hail($client,$npc,$text); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
1;
