sub EVENT_SAY {
    if ($text =~ /hail/i) {
        quest::say("Hand me one piece of visible equipment and I will turn it into an ornament. This consumes the item and all its stats and powers. Remove augments and existing ornaments first. Leave a space in your pack. I charge no coin.");
    }
}
# The paired native handler consumes a successful exchange before quest delivery.
# A worker running older code simply returns the originals and all coin.
sub EVENT_ITEM {
    $npc->ReturnHandinItems($client);
}
1;
