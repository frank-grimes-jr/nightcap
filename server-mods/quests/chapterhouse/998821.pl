# Sered's bell uses the original Classic Stun (216), with a visible warning.
sub EVENT_COMBAT {
    if ($combat_state) { quest::settimer('bell',15); }
    else { quest::stoptimer('bell'); quest::stoptimer('resolve_bell'); }
}
sub EVENT_TIMER {
    if ($timer eq 'bell') {
        $npc->Emote('raises the broken bell. In three seconds its toll will stun anyone holding his attention nearby!');
        quest::settimer('resolve_bell',3);
    } elsif ($timer eq 'resolve_bell') {
        quest::stoptimer('resolve_bell');
        return unless $npc->IsEngaged();
        return if $npc->IsStunned() || $npc->IsMezzed();
        my $target=$npc->GetTarget();
        return unless $target;
        my $distance=($target->GetX()-$npc->GetX())**2+
                     ($target->GetY()-$npc->GetY())**2+($target->GetZ()-$npc->GetZ())**2;
        $npc->CastSpell(216,$target->GetID(),1,0,0) if $distance<=900;
    }
}
sub EVENT_ITEM { $npc->ReturnHandinItems($client); }
