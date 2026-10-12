# The reusable box uses the native four-for-one Combine handler.
sub EVENT_SAY {
    if ($text =~ /hail|upgrade|polished|exalted|ascen/i) {
        my $link = quest::saylink("box", 1, "reforging box");
        quest::say("I am Artisan Veyra. Take a free $link, place four identical Polished items inside, and press Combine to make one Exalted version. Four identical Exalted items become one Ascended version, or Ascension for zone rewards. The box is reusable, and the upgraded item appears inside it. Remove augments and customization first. Base items and the highest tier cannot be improved. You can use the box wherever your travels take you.");
    }
    elsif ($text =~ /^box$/i) {
        if ($client->CountItem(900620) > 0) {
            quest::say("You already have a Reforging Box. Keep it in a main inventory slot, open it, and combine four matching copies inside.");
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
