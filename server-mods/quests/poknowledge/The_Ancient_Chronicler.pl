# ==============================================================================
# The Ancient Chronicler (999220) — multiclass selection front-end (v2, ADR 0003)
#
# Pure dialog. Every mutation goes through plugin::multiclass (quests/plugins/
# multiclass.pl); this script owns only presentation:
#
#   Hail                 → status + archetype-grouped class saylinks
#   <class name>         → preview (live spell/skill/AA counts) + embrace link
#   embrace <class name> → confirmation popup; the popup's Yes commits
#   release second|third → confirmation popup; Yes releases the slot
#
# Popup IDs: 300+class_id = adopt confirm, 402/403 = release slot 2/3.
# ==============================================================================

my $POPUP_RELEASE_2 = 402;
my $POPUP_RELEASE_3 = 403;

my %ARCHETYPES = (
    'Guardians of the Line' => [1, 3, 5],        # War Pal SK
    'Menders and Zealots'   => [2, 6, 10],       # Clr Dru Shm
    'Blades and Fists'      => [4, 7, 8, 9, 16], # Rng Mnk Brd Rog Ber
    'Wielders of the Weave' => [11, 12, 13, 14, 15], # Nec Wiz Mag Enc Bst
);
my @ARCHETYPE_ORDER = ('Guardians of the Line', 'Menders and Zealots',
                       'Blades and Fists', 'Wielders of the Weave');

sub _status_line {
    my ($base, $c2, $c3) = @_;
    my $s = 'You walk the path of the ' . plugin::mc_class_name($base);
    $s .= $c2 ? ', joined by the ' . plugin::mc_class_name($c2) : '';
    $s .= $c3 ? ' and the ' . plugin::mc_class_name($c3) : '';
    return $s . '.';
}

sub _show_menu {
    my ($base, $c2, $c3) = @_;
    my $name = $client->GetName();

    quest::say(_status_line($base, $c2, $c3));

    if ($c2 && $c3) {
        quest::say(
            'Your soul already holds three disciplines, ' . $name . '. Say [' .
            quest::saylink('release second') . '] or [' . quest::saylink('release third') .
            '] to unbind one.'
        );
        return;
    }

    quest::say(
        'Speak the name of any discipline and I shall reveal what it would awaken in you' .
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
    my $p     = plugin::mc_preview($base, $class_id, $client->GetLevel());

    quest::say(
        "The $cname - " . plugin::mc_flavor($class_id) . '. Embracing it would open ' .
        "$p->{spells_total} spells to your spellbook ($p->{spells_now} within your reach today), " .
        "$p->{skills_new} skills your training never touched, and $p->{aa_lines} lines of " .
        'alternate advancement in your Class tab, usable from this very moment.'
    );
    quest::say(
        'If this is your path, say [' . quest::saylink("embrace $cname", 0, 'embrace it') . '].'
    );
}

sub EVENT_SAY {
    my $say     = lc($text);
    my $char_id = $client->CharacterID();
    my $base    = $client->GetClass();
    my ($c2, $c3) = plugin::mc_get_classes($char_id);

    if ($say =~ /hail/) {
        quest::say(
            'Ah, ' . $client->GetName() . '. Every soul in this library is a book with pages ' .
            'left blank. I am the quill.'
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
            'Its alternate abilities become dormant (purchases are kept and return if you ' .
            're-embrace it). Spells already scribed and skills already trained remain.',
            $slot == 2 ? $POPUP_RELEASE_2 : $POPUP_RELEASE_3, 1, 0
        );
        return;
    }

    if ($say =~ /^embrace (.+)$/) {
        my $class_id = plugin::mc_class_id_by_name($1);
        if (!$class_id) { quest::say('No tome bears that name.'); return; }
        my $cname = plugin::mc_class_name($class_id);
        quest::popup(
            "Embrace the $cname",
            "Bind the $cname discipline to your soul?<br><br>" .
            'You gain its spells (purchase tomes at the Loremasters), its skills trained to ' .
            'your level, and its alternate advancement lines - permanent until released here.',
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
        return;
    }

    if ($popupid > 300 && $popupid <= 316) {
        my ($ok, $msg) = plugin::mc_apply_class($client, $popupid - 300);
        $client->Message($ok ? 15 : 13, $msg);
        return;
    }
}

1;
