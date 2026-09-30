sub EVENT_SAY { plugin::tunnel_spire_hail($client,$npc,$text); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
