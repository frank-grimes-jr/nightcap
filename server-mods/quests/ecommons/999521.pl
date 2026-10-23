sub EVENT_SPAWN { plugin::tunnel_social_schedule($npc,0); }
sub EVENT_TIMER { plugin::tunnel_social_idle($npc,$entity_list,$timer); }
sub EVENT_SAY {
    plugin::tunnel_social_schedule($npc,1);
    if ($text =~ /^hail/i) {
        plugin::tunnel_resident_hail($client,$npc,$text);
        $client->DungeonAction($npc->GetID(),lc($text)) if $client->can('DungeonAction');
        return;
    }
    return if $client->can('DungeonAction') && $client->DungeonAction($npc->GetID(),lc($text));
    plugin::tunnel_resident_hail($client,$npc,$text);
}
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
