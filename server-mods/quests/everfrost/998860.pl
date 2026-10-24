# Exact NPC binding preserves the global Waypoint and Instance Keeper scripts.
sub EVENT_SAY {
    $client->DungeonAction($npc->GetID(),lc($text)) if $client->can('DungeonAction');
}
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
