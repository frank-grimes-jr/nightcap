# Halvyr's half-health call creates two zero-XP, zero-loot shades. Identity
# markers prevent wipe/death cleanup from touching Elowen's defense encounter.
sub clear_watch {
    for my $id (split /,/, $npc->GetEntityVariable('vigil-watch-adds')) {
        next unless $id =~ /^\d+$/;
        my $add=$entity_list->GetNPCByID($id);
        $add->Depop() if $add && $add->GetEntityVariable('vigil-watch-owner') eq $npc->GetID();
    }
    $npc->SetEntityVariable('vigil-watch-adds','');
}
sub EVENT_SPAWN { quest::setnexthpevent(50); }
sub EVENT_COMBAT {
    unless ($combat_state) { clear_watch(); quest::setnexthpevent(50); }
}
sub EVENT_HP {
    return unless $hpevent==50;
    $npc->Emote('calls the unbroken watch to his side. Release the shades or hold them at bay!');
    my $target=$npc->GetTarget(); return unless $target;
    my @adds;
    for my $side (-1,1) {
        my $id=quest::spawn2(998836,0,0,$npc->GetX()+8*$side,$npc->GetY(),$npc->GetZ(),0);
        my $add=$entity_list->GetNPCByID($id); next unless $add;
        $add->SetEntityVariable('vigil-watch-owner',$npc->GetID());
        $add->AddToHateList($target,1); push @adds,$id;
    }
    $npc->SetEntityVariable('vigil-watch-adds',join(',',@adds));
}
sub EVENT_DEATH_COMPLETE { clear_watch(); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
