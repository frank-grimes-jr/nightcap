sub EVENT_SAY { plugin::tunnel_resident_hail($client,$npc,$text); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
sub EVENT_SPAWN { quest::settimer('trift_story',180+int(rand(121))); }
sub EVENT_TIMER {
    if ($timer eq 'trift_story') {
        plugin::tunnel_trift_story($entity_list);
        quest::settimer('trift_story',180+int(rand(121)));
    }
}
