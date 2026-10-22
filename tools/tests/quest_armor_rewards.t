use strict;
use warnings;
use Test::More;
use JSON::PP qw(decode_json encode_json);
use File::Spec;

my $root = shift @ARGV or die 'Usage: perl quest_armor_rewards.t REPO_ROOT [--baseline]';
my $baseline_only = grep { $_ eq '--baseline' } @ARGV;
my $epic_only = grep { $_ eq '--epic-only' } @ARGV;
sub read_text {
    my ($path) = @_;
    open my $file, '<:raw', $path or die "$path: $!";
    local $/;
    return <$file>;
}
my $capture = decode_json(read_text("$root/docs/releases/quest-armor-20261022/production-reference.json"));
our ($active_package, $state);

# Execute the captured real plugin helpers. Only the EQEmu variable/native-object
# boundary is faked; exact-count versus >= checks and currency handling are real.
for my $path ('plugins/globals.pl', 'plugins/check_handin.pl') {
    my $source = $capture->{helpers}{$path}{source} // die "Missing production helper $path";
    eval "package plugin; no strict; no warnings; $source";
    die $@ if $@;
}
{
    package plugin;
    no warnings 'redefine';
    sub var {
        my $key = shift;
        $key =~ s/^[\$\@%]//;
        no strict 'refs';
        return \%{"${main::active_package}::$key"} if $key eq 'itemcount';
        return \${"${main::active_package}::$key"};
    }
    sub assocName { return 'Palwar'; }
    sub humanoid { return 1; }
    package ArmorItem;
    sub GetCharges { $_[0]{charges} }
    sub RemoveTaskDeliveredItems { $_[0]{charges} }
    package ArmorClient;
    sub SetEntityVariable { $_[0]{vars}{$_[1]} = $_[2]; }
    sub EntityVariableExists { exists $_[0]{vars}{$_[1]}; }
    sub SummonItem { push @{$main::state->{returned}}, [@_[1 .. $#_]]; }
    sub AddMoneyToPP { $main::state->{money} += $_[1] + 10*$_[2] + 100*$_[3] + 1000*$_[4]; }
    package ArmorNPC;
    sub AddItem { push @{$main::state->{npc_items}}, [@_[1 .. $#_]]; }
    package quest;
    sub summonitem { push @{$main::state->{summons}}, 0 + $_[0]; }
    sub exp { $main::state->{xp} += $_[0]; }
    sub ding { ++$main::state->{dings}; }
    sub faction { push @{$main::state->{factions}}, [@_]; }
    sub say { push @{$main::state->{sayings}}, $_[0]; }
    sub me { push @{$main::state->{sayings}}, $_[0]; }
    sub doanim { push @{$main::state->{animations}}, $_[0]; }
    sub givecash { $main::state->{money} += $_[0] + 10*$_[1] + 100*$_[2] + 1000*$_[3]; }
    sub send_player_handin_event { ++$main::state->{handin_events}; }
}

my $serial = 0;
sub load_quest {
    my ($path, $baseline) = @_;
    my $source = ($baseline || !-f "$root/server-mods/quests/$path")
        ? $capture->{scripts}{$path}{source} : read_text("$root/server-mods/quests/$path");
    die "Missing quest $path" unless defined $source;
    my $package = 'ArmorQuest' . ++$serial;
    eval "package $package; no strict; no warnings; $source";
    die "$path: $@" if $@;
    no strict 'refs';
    die "$path lacks EVENT_ITEM" unless defined &{"${package}::EVENT_ITEM"};
    &{"${package}::EVENT_SPAWN"}() if defined &{"${package}::EVENT_SPAWN"};
    return $package;
}

sub invoke {
    my ($package, $ids, $coin, $faction) = @_;
    die 'Native trade has only four slots' if @$ids > 4;
    local $active_package = $package;
    local $state = {summons=>[], returned=>[], xp=>0, dings=>0, factions=>[], sayings=>[],
                   animations=>[], money=>0, handin_events=>0, npc_items=>[]};
    no strict 'refs';
    %{"${package}::itemcount"} = ();
    ${"${package}::client"} = bless {vars=>{}}, 'ArmorClient';
    ${"${package}::npc"} = bless {}, 'ArmorNPC';
    ${"${package}::name"} = 'Palwar';
    ${"${package}::faction"} = defined($faction) ? $faction : 5;
    my @coin = $coin ? @$coin : (0,0,0,0);
    for my $i (0..3) {
        ${"${package}::" . (qw(copper silver gold platinum))[$i]} = $coin[$i];
        my $slot = $i + 1;
        my $id = $ids->[$i] // 0;
        ${"${package}::item$slot"} = $id;
        ${"${package}::item${slot}_charges"} = 1;
        ${"${package}::item${slot}_attuned"} = 1;
        ${"${package}::item${slot}_inst"} = bless {charges=>1}, 'ArmorItem';
        ++${"${package}::itemcount"}{$id} if $id;
    }
    &{"${package}::EVENT_ITEM"}();
    # The real helper iterates a Perl hash; return order has no game significance.
    @{$state->{returned}} = sort { encode_json($a) cmp encode_json($b) } @{$state->{returned}};
    @{$state->{summons}} = sort {$a <=> $b} @{$state->{summons}};
    return $state;
}
sub expected_upgrade {
    my ($result, $base) = @_;
    my $expected = decode_json(encode_json($result));
    $_ = $base + 600000 for grep { $_ == $base } @{$expected->{summons}};
    @{$expected->{summons}} = sort {$a <=> $b} @{$expected->{summons}};
    return $expected;
}

# Reviewed input/reward expectations are independent of both candidate code and
# the implementation's catalog. A bad catalog edit cannot redefine these tests.
my @quests = (
    ['soltemple/Cryssia_Stardreamer.pl',4156,[10564,10563,10128],0],
    ['soltemple/Cryssia_Stardreamer.pl',4154,[4100,10565,10118],0],
    ['soltemple/Cryssia_Stardreamer.pl',4153,[10559,4099,10117],0],
    ['soltemple/Cryssia_Stardreamer.pl',4155,[4113,10560,10119],0],
    ['soltemple/an_undead_knight.pl',3144,[12292,12291,16507],0],
    ['soltemple/an_undead_knight.pl',3145,[12294,12293,12297,12297],0],
    ['soltemple/an_undead_knight.pl',3146,[12296,12295,12106,12106],0],
    ['soltemple/an_undead_knight_.pl',3140,[12283,12284,13921,13921],0],
    ['soltemple/an_undead_knight_.pl',3141,[12285,12286,16507,16507],0],
    ['soltemple/an_undead_knight_.pl',3142,[12288,12287,9023],0],
    ['soltemple/an_undead_knight_.pl',3143,[12290,12289,19075],0],
    ['kithicor/Gandari.pl',3189,[10569,10546,10033],10000],
    ['kithicor/Gandari.pl',3181,[10566,10570,10034],10000],
    ['kithicor/Gandari.pl',3188,[10548,10568,10032,10032],10000],
    ['kithicor/Gandari.pl',3184,[10571,10567,10035,10035],10000],
    ['kithicor/Leaf_Falldim.pl',3190,[12321,12320],10000],
    ['kithicor/Leaf_Falldim.pl',3192,[12305,12306],10000,[0,0,2000,0]],
    ['kithicor/Leaf_Falldim.pl',3191,[10059,12328],10000],
    ['lakerathe/Vrynn.pl',4941,[3064,10073,19039,19041],200],
    ['lakerathe/Vrynn.pl',4942,[3062,19050,19043,19046],200],
    ['lakerathe/Vrynn.pl',4943,[3060,19051,19038,19045],200],
    ['lakerathe/Vrynn.pl',4944,[3063,19052,19034,19037],200],
    ['lakerathe/Kyralynn.pl',4945,[3061,10073,19031,19033],200],
    ['lakerathe/Kyralynn.pl',4947,[3053,19051,19042,19040],200],
    ['lakerathe/Kyralynn.pl',4948,[3058,19052,19032,19035],200],
    ['lakerathe/Kyralynn.pl',4946,[3056,19050,19036,19044],200],
);

for my $spec ($epic_only ? () : @quests) {
    my ($path,$base,$inputs,$xp,$coin) = @$spec;
    my $candidate = load_quest($path, $baseline_only);
    my $baseline = load_quest($path, 1);
    subtest "$path final reward $base" => sub {
        my $actual = invoke($candidate,$inputs,$coin);
        is_deeply($actual->{summons},[$base+600000],'exact final ordinary Ascended item');
        is($actual->{xp},$xp,'original XP amount');
        is_deeply($actual,expected_upgrade(invoke($baseline,$inputs,$coin),$base),
            'complete event changes only final item; XP, faction, text, returns and currency retained');
        my $empty = invoke($candidate,[]);
        is_deeply($empty->{summons},[],'empty repeated hand-in grants no reward');
        is($empty->{xp},0,'empty repeated hand-in grants no XP');
        is_deeply(invoke($candidate,$inputs,$coin)->{summons},[$base+600000],
            'fresh full hand-in can earn another Ascended item');
        for my $missing (0..$#$inputs) {
            my @partial = @$inputs;
            splice @partial,$missing,1;
            my $partial = invoke($candidate,\@partial,$coin);
            is_deeply($partial,invoke($baseline,\@partial,$coin),"missing input $missing preserves complete return behavior");
            ok(!(grep {$_ == $base || $_ == $base+600000} @{$partial->{summons}}),"missing input $missing cannot award armor");
            is($partial->{xp},0,"missing input $missing cannot award XP");
        }
        my @wrong = @$inputs;
        $wrong[0] = 999;
        is_deeply(invoke($candidate,\@wrong,$coin),invoke($baseline,\@wrong,$coin),
            'wrong item returns retain original IDs, charges and attunement');
        if (@$inputs < 4) {
            my @extra = (@$inputs,999);
            is_deeply(invoke($candidate,\@extra,$coin),expected_upgrade(invoke($baseline,\@extra,$coin),$base),
                'unrelated excess input keeps existing return behavior');
            @extra = (@$inputs,$inputs->[0]);
            is_deeply(invoke($candidate,\@extra,$coin),expected_upgrade(invoke($baseline,\@extra,$coin),$base),
                'excess required input keeps exact-count or takeItems semantics');
        }
        my @extra_coin = $coin ? @$coin : (0,0,0,0);
        $extra_coin[0] += 3;
        is_deeply(invoke($candidate,$inputs,\@extra_coin),expected_upgrade(invoke($baseline,$inputs,\@extra_coin),$base),
            'excess currency behavior unchanged');
        if ($coin) {
            my $short = invoke($candidate,$inputs,[0,0,1999,0]);
            is_deeply($short,invoke($baseline,$inputs,[0,0,1999,0]),'insufficient payment returns unchanged');
            ok(!(grep {$_ == $base || $_ == $base+600000} @{$short->{summons}}),'1999 gold cannot earn paid reward');
            is_deeply(invoke($candidate,$inputs,[0,0,0,200])->{summons},[$base+600000],
                'equivalent payment of 200 platinum still succeeds');
        }
    };
}

my %resize = (
    Timtok_Tonsmith => {4178=>4186,4176=>4184,4173=>4181,4180=>4188},
    Ranvigoz_Tonsmith => {4177=>4185,4179=>4187,4175=>4183,4174=>4182},
);
for my $zone ($epic_only ? () : ('commons','commonlands')) {
    for my $npc (sort keys %resize) {
        my $path = "$zone/$npc.pl";
        my $candidate = load_quest($path,$baseline_only);
        subtest "$path remains an unchanged exclusion" => sub {
            if (-f "$root/server-mods/quests/$path") {
                is(read_text("$root/server-mods/quests/$path"),$capture->{scripts}{$path}{source},
                    'no resizing behavior added to this change');
            }
            for my $base (sort {$a<=>$b} keys %{$resize{$npc}}) {
                my $normal = invoke($candidate,[$base]);
                is_deeply($normal->{summons},[$resize{$npc}{$base}],"legacy Normal $base resizing remains");
                for my $offset (200000,400000,600000) {
                    my $id = $base+$offset;
                    my $result = invoke($candidate,[$id]);
                    is_deeply($result->{summons},[],"quality item $id is not resized/downgraded");
                    is_deeply($result->{returned},[[$id,1,1]],"quality item $id retains ID/charges/attunement on return");
                    is_deeply($result->{factions},[],"rejected item $id grants no faction");
                    is_deeply(invoke($candidate,[$id],undef,6)->{summons},[],"poor faction cannot convert $id");
                }
            }
            note('Legacy poor-faction branch has no return call; this patch does not change or approve that behavior.');
        };
    }
}

my $epic_path = 'overthere/Kurron_Ni.pl';
my @normal_darkforge = (3141,3145,3140);
for my $mask (0..7) {
    my @pieces = map { $normal_darkforge[$_] + (($mask & (1 << $_)) ? 600000 : 0) } 0..2;
    subtest "Kurron Ni Normal/Ascended combination $mask" => sub {
        my $candidate = load_quest($epic_path,$baseline_only);
        my $baseline = load_quest($epic_path,1);
        my $earned = invoke($candidate,\@pieces,[0,0,0,900]);
        is_deeply($earned,invoke($baseline,\@normal_darkforge,[0,0,0,900]),
            'every mixed quality combination has the original successful outcome');
        is_deeply($earned->{factions},[[404,7]],'original Truespirit faction reward');
        is_deeply($earned->{npc_items},[[18099,1]],'one original Letter to Duriek added to NPC inventory');
        is_deeply($earned->{returned},[],'three required pieces consumed');
        is($earned->{money},900000,'retains existing helper coin return after presenting 900pp');
        my $empty = invoke($candidate,[],[0,0,0,900]);
        is_deeply($empty->{factions},[],'coin without another armor set earns no faction');
        is_deeply($empty->{npc_items},[],'empty repeat cannot duplicate letter');
        my $repeat = invoke($candidate,\@pieces,[0,0,0,900]);
        is_deeply($repeat->{factions},[[404,7]],'another full set retains repeat faction behavior');
        is_deeply($repeat->{npc_items},[],'another full set cannot duplicate letter on the same spawn');
        for my $missing (0..2) {
            my @partial = @pieces;
            splice @partial,$missing,1;
            is_deeply(invoke($candidate,\@partial,[0,0,0,900]),invoke($baseline,\@partial,[0,0,0,900]),
                "missing piece $missing preserves rejected-item and money returns");
        }
        is_deeply(invoke($candidate,\@pieces,[0,0,0,899]),invoke($baseline,\@pieces,[0,0,0,899]),
            '899 platinum rejects and returns the complete hand-in');
        is_deeply(invoke($candidate,\@pieces,[0,0,9000,0]),invoke($baseline,\@pieces,[0,0,9000,0]),
            'equivalent gold does not bypass the existing raw-platinum threshold');
        my @wrong = (999,@pieces[1,2]);
        is_deeply(invoke($candidate,\@wrong,[0,0,0,900]),invoke($baseline,\@wrong,[0,0,0,900]),
            'unrelated armor cannot substitute for an epic component');
        my $extra_candidate = load_quest($epic_path,$baseline_only);
        my $extra_baseline = load_quest($epic_path,1);
        is_deeply(invoke($extra_candidate,[@pieces,999],[3,2,1,901]),
            invoke($extra_baseline,[@normal_darkforge,999],[3,2,1,901]),
            'unrelated extra item and excess currency retain successful legacy behavior');
        no strict 'refs';
        &{"${candidate}::EVENT_SPAWN"}();
        is_deeply(invoke($candidate,\@pieces,[0,0,0,900])->{npc_items},[[18099,1]],
            'a new NPC spawn can carry its own single letter');
    };
}
subtest 'Kurron Ni still rejects unaudited quality tiers' => sub {
    for my $offset (200000,400000) {
        for my $slot (0..2) {
            my @pieces = @normal_darkforge;
            $pieces[$slot] += $offset;
            my $candidate = load_quest($epic_path,$baseline_only);
            my $actual = invoke($candidate,\@pieces,[0,0,0,900]);
            is_deeply($actual->{factions},[],"tier $offset slot $slot grants no faction");
            is_deeply($actual->{npc_items},[],"tier $offset slot $slot grants no letter");
            is_deeply($actual,invoke(load_quest($epic_path,1),\@pieces,[0,0,0,900]),
                "tier $offset slot $slot retains original item/currency returns");
        }
    }
};
done_testing();
