sub EVENT_SPAWN { plugin::tunnel_social_schedule($npc,0); }
sub EVENT_TIMER { plugin::tunnel_social_idle($npc,$entity_list,$timer); }
sub EVENT_SAY { plugin::tunnel_social_schedule($npc,1); plugin::tunnel_resident_hail($client,$npc,$text); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
