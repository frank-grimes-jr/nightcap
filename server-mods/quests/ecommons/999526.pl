sub EVENT_SPAWN { plugin::tunnel_social_schedule($npc,0); }
sub EVENT_TIMER { plugin::tunnel_social_idle($npc,$entity_list,$timer); }
sub EVENT_SAY {
    if ($text =~ /hail/i) {
        plugin::tunnel_social_schedule($npc,1);
        quest::say('Good company makes even a long wait worthwhile. There is room here if you would like to join us.');
    }
}
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
