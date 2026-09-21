sub EVENT_SAY { plugin::market_hail($client, $npc, $text); }
sub EVENT_SPAWN {
    quest::settimer('market',30+int(rand(26)));
    quest::settimer('tunnel_chatter',45+int(rand(36)));
}
sub EVENT_TIMER {
    if ($timer eq 'market') {
        plugin::market_pulse($entity_list,$npc);
        quest::settimer('market',30+int(rand(26)));
    } elsif ($timer eq 'tunnel_chatter') {
        plugin::tunnel_chatter_pulse($entity_list,$npc);
        quest::settimer('tunnel_chatter',45+int(rand(36)));
    }
}
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
