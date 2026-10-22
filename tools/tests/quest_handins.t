use strict;
use warnings;
use Test::More;
our (%itemcount, $item1, $item2, $item3, $item4, $platinum, $gold, $silver, $copper, @rewards, $npc, $name);
my %tiered = map { $_ => 1 } (2332,2352,2353,2356,2360,2361,2362,2363,2367,2368,3140,3141,3145,5103,6048,6337,6338,6340,7331,10529,10546,10547,10550);
my @refunds;
sub quest::say {} sub quest::faction {} sub quest::exp {}
sub quest::givecash { push @refunds, [@_]; }
sub quest::summonitem { push @rewards, $_[0]; }
sub plugin::return_items {}
# Native allocator is exercised separately by compiled test_quest_handins.py.
# Here the adapter verifies each legacy script delegates its exact recipe/reward.
sub plugin::check_handin {
    my ($items, %needed) = @_;
    my %left = %$items;
    @left{qw(copper silver gold platinum)} = ($copper, $silver, $gold, $platinum);
    for my $currency (qw(copper silver gold platinum)) {
        return 0 if ($left{$currency} || 0) != ($needed{$currency} || 0);
    }
    for my $id (keys %needed) {
        for my $actual ($id, map { $id + $_ } ($tiered{$id} ? (200000,400000,600000) : ())) {
            my $used = ($left{$actual} || 0) < $needed{$id} ? ($left{$actual} || 0) : $needed{$id};
            $left{$actual} -= $used;
            $needed{$id} -= $used;
        }
        return 0 if $needed{$id};
    }
    %$items = %left;
    return 1;
}
my %cases = (
    Gardern => [[6342,{10548=>1,10549=>1,10550=>1,6048=>1}], [6341,{10551=>1,6338=>1,10557=>1,14364=>1}], [10119,{10034=>2,10000=>1}]],
    Joyce => [[2358,{10545=>1,10547=>1,10034=>1,10546=>1}], [2359,{10539=>1,10542=>1,10540=>1,10541=>1}], [2357,{10543=>1,10026=>1,10544=>1,2363=>1}], [1356,{2361=>1,2362=>1,15109=>1,2360=>1}]],
    Sultin => [[6329,{10087=>1,6337=>1}], [6334,{12240=>1,6340=>1}], [2351,{2353=>1,2354=>1,2355=>1,2356=>1}], [2350,{2352=>1,10530=>1,10531=>1,10532=>1}]],
    Vilissia => [[2366,{2352=>1,2368=>1,10558=>1,2367=>1}], [2364,{2332=>1,10553=>1,10554=>1,10555=>1}], [10118,{10035=>2,10000=>1}], [19048,{16507=>1}]],
    Vurgo => [[5316,{10538=>1,10031=>1,7331=>1,5103=>1}], [10527,{10536=>1,10537=>1,10529=>1}]],
);
for my $npc (sort keys %cases) {
    { no warnings 'redefine'; $! = 0; do "./server-mods/quests/soltemple/$npc.pl"; die $@ if $@; die $! if $!; }
    for my $case (@{$cases{$npc}}) {
        my ($reward,$required)=@$case;
        for my $offset (0,200000,400000,600000) {
            %itemcount=map { ($_ + ($tiered{$_} ? $offset : 0)) => $required->{$_} } keys %$required;
            $itemcount{999998}=1;
            @rewards=(); ($item1,$item2,$item3,$item4)=(0,0,0,0);
            ($platinum,$gold,$silver,$copper)=(0,0,0,0);
            EVENT_ITEM();
            is_deeply(\@rewards,[$reward],"$npc reward $reward tier $offset");
            is($itemcount{999998},1,'extra item retained');
            @rewards=(); EVENT_ITEM(); is(scalar @rewards,0,'cannot reward twice');
        }
        %itemcount=%$required; delete $itemcount{(sort {$a <=> $b} keys %$required)[0]};
        @rewards=(); EVENT_ITEM(); is(scalar @rewards,0,"$npc missing ingredient rejected");
    }
}

# Current class-armor candidate delegates selected IDs to the same native helper.
# These callback controls are paired with actual native Darkforge allocation tests.
{ no warnings 'redefine'; $! = 0; do './server-mods/quests/overthere/Kurron_Ni.pl'; die $@ if $@; die $! if $!; }
my @letters;
sub HandinNPC::AddItem { push @letters, $_[1]; }
$npc = bless {}, 'HandinNPC'; $name = 'Test';
for my $helm (0,200000,400000,600000) {
    for my $breast (0,200000,400000,600000) {
        for my $legs (0,200000,400000,600000) {
            EVENT_SPAWN(); @letters=(); @refunds=(); $platinum=900;
            %itemcount=(3140+$helm=>1,3141+$breast=>1,3145+$legs=>1);
            EVENT_ITEM();
            is_deeply(\@letters,[18099],'Kurron accepts complete mixed ordinary qualities');
            is_deeply(\@refunds,[[0,0,0,900]],'Kurron explicitly refunds once after success');
        }
    }
}
for my $case ([899,{203140=>1,403141=>1,603145=>1}], [900,{203140=>1,603145=>1}], [900,{803140=>1,403141=>1,603145=>1}]) {
    EVENT_SPAWN(); @letters=(); @refunds=(); ($platinum,my $given)=@$case; %itemcount=%$given;
    EVENT_ITEM(); is_deeply(\@letters,[],'Kurron rejects missing currency/piece or epic identity');
    is_deeply(\@refunds,[],'failed Kurron callback leaves returns to native lifecycle');
}
EVENT_SPAWN(); @letters=(); @refunds=(); ($copper,$silver,$gold,$platinum)=(3,2,1,901);
%itemcount=(203140=>1,403141=>1,603145=>1,999998=>1);
EVENT_ITEM();
is_deeply(\@refunds,[[3,2,1,901]],'mixed denominations and excess are refunded exactly once');
is($itemcount{999998},1,'Kurron unrelated extra remains for native return');
done_testing();
