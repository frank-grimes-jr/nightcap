# ==============================================================================
# The Ancient Chronicler (999220) — multiclass selection front-end (ADR 0003 / 0024)
#
# Pure dialog. Every mutation goes through plugin::multiclass (quests/plugins/
# multiclass.pl); this script owns only presentation:
#
#   Hail                 → status + archetype-grouped class saylinks
#   <class name>         → preview (role and progression) + embrace link
#   embrace <class name> → confirmation popup; the popup's Yes commits
#   release second|third → confirmation popup; Yes releases the slot
#
# Popup IDs: 300+class_id = adopt confirm, 402/403 = release slot 2/3.
# ==============================================================================

my $POPUP_RELEASE_2 = 402;
my $POPUP_RELEASE_3 = 403;

my %ARCHETYPES = (
    'Tanks' => [1, 3, 5],        # War Pal SK
    'Healers'   => [2, 6, 10],       # Clr Dru Shm
    'Melee and songs'      => [4, 7, 8, 9, 16], # Rng Mnk Brd Rog Ber
    'Casters and pets' => [11, 12, 13, 14, 15], # Nec Wiz Mag Enc Bst
);
my @ARCHETYPE_ORDER = ('Tanks', 'Healers',
                       'Melee and songs', 'Casters and pets');

sub _status_line {
    my ($base, $c2, $c3) = @_;
    return 'Your classes: ' . plugin::mc_class_name($base) . ' (Primary) | ' .
        ($c2 ? plugin::mc_class_name($c2) : 'Not selected') . ' (Second) | ' .
        ($c3 ? plugin::mc_class_name($c3) : 'Not selected') . ' (Third)';
}

sub _show_menu {
    my ($base, $c2, $c3) = @_;
    my $name = $client->GetName();

    $client->Message(15, _status_line($base, $c2, $c3));
    $client->Message(15, 'Use #classes anytime to see your choices. Your Primary class stays the same.');

    if ($c2 && $c3) {
        quest::say(
            'All three class slots are filled, ' . $name . '. Say [' .
            quest::saylink('release second') . '] or [' . quest::saylink('release third') .
            '] to unbind one.'
        );
        return;
    }

    quest::say(
        'Choose a class below to review it. Nothing changes until you confirm your choice' .
        ($c2 ? ' — or [' . quest::saylink('release second') . '] your ' . plugin::mc_class_name($c2) . ' binding.' : '.')
    );
    for my $arch (@ARCHETYPE_ORDER) {
        my @links;
        for my $id (@{$ARCHETYPES{$arch}}) {
            next if $id == $base || ($c2 && $id == $c2) || ($c3 && $id == $c3);
            push @links, '[' . quest::saylink(plugin::mc_class_name($id)) . ']';
        }
        $client->Message(335, "$arch: " . join(' ', @links)) if @links;
    }
}

sub _show_preview {
    my ($base, $class_id) = @_;
    my $cname = plugin::mc_class_name($class_id);
    quest::say($cname . ': ' . plugin::mc_flavor($class_id) . '.');
    $client->Message(15,
        'Choosing this class opens its eligible spells, skills, and alternate abilities. ' .
        'Level and expansion requirements still apply. Purchase spells from the spell merchants; ' .
        'skills improve through use and training. Your Primary class will remain ' . plugin::mc_class_name($base) . '.');
    quest::say('Ready to add ' . $cname . '? [' . quest::saylink("embrace $cname", 0, 'Choose this class') . ']');
}

sub EVENT_SAY {
    my $say     = lc($text);
    my $char_id = $client->CharacterID();
    my $base    = $client->GetClass();
    my ($c2, $c3) = plugin::mc_get_classes($char_id);

    if ($say =~ /hail/ || $say eq 'classes' || $say eq 'my classes') {
        quest::say(
            'Welcome, ' . $client->GetName() . '. I can help you choose two additional classes.'
        );
        _show_menu($base, $c2, $c3);
        return;
    }

    if ($say eq 'release second' || $say eq 'release third') {
        my $slot  = $say eq 'release second' ? 2 : 3;
        my $class = $slot == 2 ? $c2 : $c3;
        if (!$class) {
            quest::say('That binding is already empty.');
            return;
        }
        quest::popup(
            'Release Discipline',
            'Unbind the ' . plugin::mc_class_name($class) . ' discipline?<br><br>' .
            'AAs that require only this class are removed and eligible spent AA points are refunded. ' .
            'Shared AAs remain. Skills are limited to your retained classes. Already scribed spells remain.',
            $slot == 2 ? $POPUP_RELEASE_2 : $POPUP_RELEASE_3, 1, 0
        );
        return;
    }

    if ($say =~ /^embrace (.+)$/) {
        my $class_id = plugin::mc_class_id_by_name($1);
        if (!$class_id) { quest::say('No tome bears that name.'); return; }
        my $cname = plugin::mc_class_name($class_id);
        quest::popup(
            "Choose $cname",
            "Add $cname to your next open class slot?<br><br>" .
            'Your Primary class stays the same. Spell, skill, and AA access follows level and expansion requirements. ' .
            'Spells must be purchased and skills developed. Choose Yes to save, or No to keep your current classes.',
            300 + $class_id, 1, 0
        );
        return;
    }

    # Bare class name → preview
    my $class_id = plugin::mc_class_id_by_name($say);
    if ($class_id) {
        if ($class_id == $base)                       { quest::say('That page of your book was written at birth.'); return; }
        if (($c2 && $class_id == $c2) || ($c3 && $class_id == $c3)) { quest::say('You already carry that discipline.'); return; }
        if ($c2 && $c3)                               { quest::say('Your soul is full, ' . $client->GetName() . '. Release a discipline first.'); return; }
        _show_preview($base, $class_id);
        return;
    }
}

sub EVENT_POPUPRESPONSE {
    my $char_id = $client->CharacterID();

    if ($popupid == $POPUP_RELEASE_2 || $popupid == $POPUP_RELEASE_3) {
        my ($ok, $msg) = plugin::mc_revoke_slot($client, $popupid == $POPUP_RELEASE_2 ? 2 : 3);
        $client->Message($ok ? 15 : 13, $msg);
        my ($c2, $c3) = plugin::mc_get_classes($char_id);
        _show_menu($client->GetClass(), $c2, $c3);
        return;
    }

    if ($popupid > 300 && $popupid <= 316) {
        my ($ok, $msg) = plugin::mc_apply_class($client, $popupid - 300);
        $client->Message($ok ? 15 : 13, $msg);
        my ($c2, $c3) = plugin::mc_get_classes($char_id);
        _show_menu($client->GetClass(), $c2, $c3);
        return;
    }
}

1;
