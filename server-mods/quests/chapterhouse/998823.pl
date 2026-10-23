# The ash brand marks a position, not a pursuing damage aura. Classic Wrath
# (329) uses this authored NPC's explicit spellscale; no new player spell.
sub EVENT_COMBAT {
    if ($combat_state) { quest::settimer('brand',18); }
    else { quest::stoptimer('brand'); quest::stoptimer('resolve_brand'); }
}
sub EVENT_TIMER {
    if ($timer eq 'brand') {
        my $target=$npc->GetTarget(); return unless $target;
        $npc->SetEntityVariable('brand-target',$target->GetID());
        for my $axis ('X','Y','Z') {
            my $method='Get'.$axis;
            $npc->SetEntityVariable('brand-'.$axis,$target->$method());
        }
        $npc->Emote('brands the ground beneath his foe with ash. Move more than ten paces within three seconds, or interrupt him!');
        quest::settimer('resolve_brand',3);
    } elsif ($timer eq 'resolve_brand') {
        quest::stoptimer('resolve_brand');
        return unless $npc->IsEngaged();
        return if $npc->IsStunned() || $npc->IsMezzed();
        my $target=$npc->GetTarget(); return unless $target;
        return unless $target->GetID() eq $npc->GetEntityVariable('brand-target');
        my $distance=0;
        for my $axis ('X','Y','Z') {
            my $method='Get'.$axis;
            $distance+=($target->$method()-$npc->GetEntityVariable('brand-'.$axis))**2;
        }
        $npc->CastSpell(329,$target->GetID(),1,0,0) if $distance<=100;
    }
}
sub EVENT_DEATH_COMPLETE { quest::stoptimer('brand'); quest::stoptimer('resolve_brand'); }
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
