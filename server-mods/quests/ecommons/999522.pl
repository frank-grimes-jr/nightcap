sub EVENT_SAY { plugin::tunnel_resident_hail($client,$npc,$text); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
