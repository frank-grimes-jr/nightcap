use strict;
use warnings;

sub tunnel_social_resident {
    my ($id)=@_;
    return scalar grep { $_==$id } (999520..999524,999526);
}

sub tunnel_social_schedule {
    my ($npc,$talking)=@_;
    return unless $npc && tunnel_social_resident($npc->GetNPCTypeID());
    quest::settimer('tunnel_social_idle',($talking ? 90 : 35)+int(rand(46)));
}

sub tunnel_social_distance {
    my ($a,$b)=@_;
    return ($a->GetX()-$b->GetX())**2+($a->GetY()-$b->GetY())**2+($a->GetZ()-$b->GetZ())**2;
}

sub tunnel_social_idle {
    my ($npc,$entities,$timer)=@_;
    return unless $npc && $entities && defined($timer) && $timer eq 'tunnel_social_idle';
    return unless tunnel_social_resident($npc->GetNPCTypeID());
    tunnel_social_schedule($npc,0);
    return if $npc->IsEngaged();
    my @nearby=grep { tunnel_social_distance($npc,$_)<=10000 } $entities->GetClientList();
    return unless @nearby;
    return if grep { tunnel_social_distance($npc,$_)<400 } @nearby;
    my $last=$npc->GetEntityVariable('tunnel_social_partner') || 0;
    my @peers=grep { $_ && $_->GetNPCTypeID()!=$npc->GetNPCTypeID() &&
        $_->GetNPCTypeID()!=$last && !$_->IsEngaged() && tunnel_social_distance($npc,$_)<=4900 }
        map { $entities->GetNPCByNPCTypeID($_) } (999520..999524,999526);
    return unless @peers;
    my $peer=$peers[int(rand(@peers))];
    $npc->FaceTarget($peer);
    $npc->SetEntityVariable('tunnel_social_partner',$peer->GetNPCTypeID());
    # Classic gestures from zone/dialogue_window.h: 48 = nod, 29 = wave.
    # Silent, staggered gestures; existing OOC coordination is unchanged.
    $npc->DoAnim(rand()<0.85 ? 48 : 29) if rand()<0.65;
}

1;
