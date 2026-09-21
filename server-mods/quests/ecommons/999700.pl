sub EVENT_SAY {
    my $lines=plugin::tunnel_dialogue($npc->GetNPCTypeID());
    quest::say($lines->[int(rand(@$lines))]) if $text =~ /hail/i;
}
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
