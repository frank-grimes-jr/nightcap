# Global item quest: Wayfarer's Oath [Epic 0.5]. Always intercept the dummy spell.
sub EVENT_ITEM_CLICK_CAST {
    my $ok = eval { plugin::epic05_click($client, $slotid); 1; };
    if (!$ok) {
        warn "[Epic05] Activation refused after quest error: $@";
        $client->Message(13, 'Your oath could not awaken. Please try again later.');
    }
    return 1;
}
1;
