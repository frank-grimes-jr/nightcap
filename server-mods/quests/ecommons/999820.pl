# The reusable box uses the native tier-dependent Combine handler.
sub EVENT_SAY {
    if ($text =~ /hail|upgrade|normal|base|polished|exalted|ascen/i) {
        my $link = quest::saylink("box", 1, "reforging box");
        quest::say("I am Artisan Veyra. Take a free $link, place three identical eligible Normal (Base) items inside, and press Combine to make one Polished version. Four identical Polished items make one Exalted version. Four identical Exalted items become one Ascended version, or Ascension for zone rewards. The box is reusable, and the upgraded item appears inside it. Remove augments and customization first. Items without a matching next quality and the highest tier cannot be improved. Dungeon rewards use separate qualities and cannot be reforged. You can use the box wherever your travels take you.");
    }
    elsif ($text =~ /^box$/i) {
        if ($client->CountItem(900620) > 0) {
            quest::say("You already have a Reforging Box. Keep it in a main inventory slot, open it, and combine three identical eligible Normal (Base) copies or four identical Polished or Exalted copies inside.");
        } else {
            quest::summonitem(900620);
            quest::say("Your Reforging Box is free and reusable. No fee or tradeskill training is needed. Bags cannot go inside other bags, so the box upgrades equipment and augments.");
        }
    }
}

sub EVENT_ITEM {
    $npc->ReturnHandinItems($client);
}

1;
