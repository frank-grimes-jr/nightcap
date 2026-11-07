# Adventure Journal service and equipped Epic 0.5 activation.
use strict;
use warnings;

sub epic05_message { $_[0]->Message(15, $_[1]); }

sub epic05_available {
    my ($client) = @_;
    my $available = eval { $client->Epic05Contract() == 1 && epic05_store_enabled() };
    if (!$available) {
        epic05_message($client, 'The Adventure Journal is not available yet. Your earned progress is safe.');
        return 0;
    }
    return 1;
}

sub epic05_path {
    my ($key) = @_;
    for my $path (@{epic05_catalog()->{paths}}) {
        return $path if $path->{key} eq $key;
    }
    return;
}

sub epic05_earned {
    my ($client, $path) = @_;
    return 0 unless $path;
    for my $chapter (@{epic05_catalog()->{shared}}, $path) {
        return 0 unless $client->IsTaskCompleted($chapter->{task});
    }
    return epic05_store_earned($client->CharacterID(), $path->{task});
}

sub epic05_can_act {
    my ($client) = @_;
    return $client->GetHP() > 0 && !$client->IsCasting() && !$client->IsStunned()
        && !$client->IsMezzed() && !$client->IsFeared() && !$client->GetFeigned()
        && !$client->DivineAura() && !$client->IsSilenced();
}

sub epic05_at_guide {
    my ($client, $npc) = @_;
    my $catalog = epic05_catalog();
    return $npc && $npc->GetNPCTypeID() == $catalog->{guide_npc}
        && $client->GetZoneID() == $catalog->{hub_zone} && $client->GetInstanceID() == 0
        && $client->CalculateDistance($npc) <= 75 && !$client->GetAggroCount()
        && epic05_can_act($client);
}

sub epic05_journal {
    my ($client) = @_;
    my $catalog = epic05_catalog();
    my @offered;
    my $shared_done = 1;
    for my $chapter (@{$catalog->{shared}}) {
        if (!$client->IsTaskCompleted($chapter->{task})) {
            $shared_done = 0;
            if ($client->IsTaskActive($chapter->{task})) {
                epic05_message($client, 'Continue '.$chapter->{title}.' in your Tasks window.');
            } elsif ($client->GetLevel() >= $chapter->{level}) {
                push @offered, $chapter->{task};
            } else {
                epic05_message($client, $chapter->{title}.' opens at level '.$chapter->{level}.'.');
            }
            last;
        }
    }
    if ($shared_done) {
        for my $path (@{$catalog->{paths}}) {
            push @offered, $path->{task} if $client->GetLevel() >= $path->{level}
                && !$client->IsTaskCompleted($path->{task}) && !$client->IsTaskActive($path->{task});
        }
        epic05_message($client, 'Archetype paths open at level 35. Choose the way you fight; your Primary class does not restrict your choice.');
    }
    for my $path (@{$catalog->{paths}}) {
        my $label = ucfirst($path->{key});
        epic05_message($client, $label.': '.$path->{effect_text}.' '
            . (epic05_earned($client,$path) ? '['.quest::saylink('journal attune '.$path->{key},0,'Attune '.$label).']' : '(not yet earned)'));
    }
    my $state = epic05_store_state($client->CharacterID());
    if ($state && $state->{active_path}) {
        epic05_message($client, 'Active attunement: '.ucfirst($state->{active_path}).'. Shared recovery: '
            .$state->{remaining}.' seconds. ['.quest::saylink('journal forge',0,'Claim my oath charm').']');
    } else {
        epic05_message($client, 'After earning a path, choose its attunement and ask me to ['
            .quest::saylink('journal forge',0,'claim your oath charm').'].');
    }
    $client->TaskSelector(\@offered) if @offered;
}

sub epic05_attune {
    my ($client, $key) = @_;
    my $path = epic05_path($key);
    if ($client->GetLevel() < 35 || !epic05_earned($client, $path)) {
        epic05_message($client, 'Earn the shared chapters and this archetype path, and reach level 35, before attuning it.');
        return;
    }
    if (!epic05_store_attune($client->CharacterID(), $key)) {
        epic05_message($client, 'Your attunement could not change. Let the shared recovery finish, then try again.');
        return;
    }
    epic05_message($client, 'Your oath follows the '.ucfirst($key).' path. '.$path->{effect_text}
        .' All paths share a ten-minute recovery. ['.quest::saylink('journal forge',0,'Claim my oath charm').']');
}

sub epic05_forge {
    my ($client) = @_;
    # Permanent first delivery belongs to the native slot entitlement/receipt.
    # A legacy or untargeted Perl route must never mint an unreceipted copy.
    epic05_message($client, 'Target the Ancient Chronicler in the Commonlands tunnel and choose Claim my oath charm. The native journal safely delivers your earned relic.');
}

sub epic05_dialogue {
    my ($client, $npc, $text) = @_;
    my $say = lc($text // '');
    $say =~ s/^\s+|\s+$//g;
    return 0 unless $say =~ /^journal(?:\s|$)/;
    return 1 unless epic05_available($client);
    if (!epic05_at_guide($client, $npc)) {
        epic05_message($client, 'Visit the Ancient Chronicler in the East Commonlands tunnel when you are safely out of combat.');
        return 1;
    }
    if ($say eq 'journal') {
        epic05_journal($client);
    } elsif ($say eq 'journal forge') {
        epic05_forge($client);
    } elsif ($say =~ /^journal attune (guardian|striker|arcanist|warden|binder)$/) {
        epic05_attune($client, $1);
    } else {
        epic05_message($client, 'Say journal to view your adventures and earned attunements.');
    }
    return 1;
}

sub epic05_click {
    my ($client, $slot) = @_;
    # Always return 1: the native invocation spell must never cast as fallback.
    return 1 unless epic05_available($client);
    my $catalog = epic05_catalog();
    if (!defined($slot) || $slot != 0 || $client->GetItemIDAt(0) != $catalog->{item}{id}
        || $client->GetLevel() < 35 || !epic05_can_act($client)) {
        epic05_message($client, 'Equip your Epic 0.5 charm and wait until you can act before awakening it.');
        return 1;
    }
    my $state = epic05_store_state($client->CharacterID());
    my $path = $state ? epic05_path($state->{active_path}) : undef;
    if (!$state || !epic05_earned($client, $path)) {
        epic05_message($client, 'Return to the Chronicler to attune an earned archetype path.');
        return 1;
    }
    if ($state->{remaining}) {
        epic05_message($client, 'Your oath needs '.$state->{remaining}.' more seconds to recover.');
        return 1;
    }
    my $target = $client;
    if ($path->{target} eq 'owned_pet') {
        $target = $client->GetTarget();
        if (!$target || !$target->IsNPC() || $target->GetOwnerID() != $client->GetID()
            || $target->GetHP() <= 0 || $client->CalculateDistance($target) > 100) {
            epic05_message($client, 'Target one of your living pets within 100 units to awaken the Binder oath.');
            return 1;
        }
    }
    if (!epic05_store_reserve($client->CharacterID(), $path->{key})) {
        epic05_message($client, 'Your oath could not awaken. Its shared recovery may still be running.');
        return 1;
    }
    $client->SetItemCooldown($catalog->{item}{id}, $catalog->{cooldown_seconds});
    $client->SpellFinished($path->{spell}, $target);
    return 1;
}

1;
