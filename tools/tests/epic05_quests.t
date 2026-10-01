use strict;
use warnings;
use Test::More;
our $root = shift @ARGV or die 'Expected repository root';
{
    package plugin;
    do "$main::root/server-mods/plugins/epic05_data.pl" or die $@ || $!;
    do "$main::root/server-mods/plugins/epic05.pl" or die $@ || $!;
    our %states;
    our $enabled = 1;
    our $write_failure = 0;
    # Boundary fake; integration tests execute these SQL statements against MariaDB.
    no warnings 'redefine';
    sub epic05_store_enabled { return $enabled; }
    sub epic05_store_state { return $states{$_[0]} // {active_path=>'',remaining=>0}; }
    sub epic05_store_attune {
        my ($id,$path)=@_;
        return 0 if $write_failure || ($states{$id} && $states{$id}{remaining});
        $states{$id}={active_path=>$path,remaining=>0}; return 1;
    }
    sub epic05_store_reserve {
        my ($id,$path)=@_;
        return 0 if $write_failure || !$states{$id} || $states{$id}{remaining}
            || $states{$id}{active_path} ne $path;
        $states{$id}{remaining}=600; return 1;
    }
    package quest;
    sub saylink { '['.$_[0].']' }
    package EpicNPC;
    sub GetNPCTypeID { 999220 }
    package EpicClient;
    sub CharacterID { $_[0]{id} }
    sub Epic05Contract { $_[0]{contract}//1 }
    sub GetLevel { $_[0]{level}//35 }
    sub GetZoneID { $_[0]{zone}//22 }
    sub GetInstanceID { $_[0]{instance}//0 }
    sub CalculateDistance { $_[0]{distance}//5 }
    sub GetHP { $_[0]{hp}//1000 }
    sub GetAggroCount { $_[0]{aggro}//0 }
    sub IsCasting { $_[0]{casting}//0 }
    sub IsStunned { $_[0]{stunned}//0 }
    sub IsMezzed { 0 } sub IsFeared { 0 } sub GetFeigned { 0 }
    sub DivineAura { 0 } sub IsSilenced { 0 }
    sub GetID { $_[0]{id} }
    sub GetTarget { $_[0]{target} }
    sub GetItemIDAt { $_[1]==0 ? ($_[0]{item}//900501) : -1 }
    sub IsTaskCompleted { $_[0]{completed}{$_[1]}//0 }
    sub IsTaskActive { $_[0]{active}{$_[1]}//0 }
    sub TaskSelector { $_[0]{offered}=$_[1] }
    sub Message { push @{$_[0]{messages}},$_[2] }
    sub CountItem { $_[0]{owned}//0 }
    sub SummonItem { $_[0]{owned}=1; ++$_[0]{summons} }
    sub SetItemCooldown { $_[0]{ui_cooldown}=$_[2] }
    sub SpellFinished { push @{$_[0]{casts}}, [$_[1],$_[2]] }
    package EpicPet;
    sub GetOwnerID { $_[0]{owner} }
    sub IsNPC { 1 }
    sub GetHP { 100 }
    sub GetID { 900 }
}

my $npc=bless {},'EpicNPC';
sub client {
    return bless {id=>7, completed=>{map {$_=>1} 9500..9507},messages=>[],casts=>[],@_},'EpicClient';
}
sub reset_state { %plugin::states=(); $plugin::enabled=1; $plugin::write_failure=0; }

my $c=client(completed=>{});
plugin::epic05_dialogue($c,$npc,'journal');
is_deeply($c->{offered},[9500],'fresh character sees only first shared chapter');
$c->{completed}{9500}=1;
plugin::epic05_dialogue($c,$npc,'journal');
is_deeply($c->{offered},[9501],'next chapter follows earned completion');
$c->{completed}={map {$_=>1} 9500..9502};
plugin::epic05_dialogue($c,$npc,'journal');
is_deeply($c->{offered},[9503..9507],'all five archetype paths offered without class lookup');

reset_state(); $c=client();
plugin::epic05_dialogue($c,$npc,'journal attune guardian');
is($plugin::states{7}{active_path},'guardian','earned path attunes at hub');
plugin::epic05_dialogue($c,$npc,'journal forge');
is($c->{summons},1,'earned charm is recoverable');
plugin::epic05_dialogue($c,$npc,'journal forge');
is($c->{summons},1,'existing charm not duplicated');
is(plugin::epic05_click($c,0),1,'item click always blocks native dummy spell');
is(scalar @{$c->{casts}},1,'earned equipped charm invokes one effect');
is($c->{casts}[0][0],42801,'selected path supplies effect');
is($plugin::states{7}{remaining},600,'shared cooldown starts before effect');
plugin::epic05_click($c,0);
is(scalar @{$c->{casts}},1,'second click blocked');
plugin::epic05_dialogue($c,$npc,'journal attune warden');
is($plugin::states{7}{active_path},'guardian','cooldown blocks switching');
my $relog=client();
plugin::epic05_click($relog,0);
is(scalar @{$relog->{casts}},0,'fresh session retains cooldown');

for my $case (
    [level=>34], [zone=>202], [instance=>1], [aggro=>1], [casting=>1], [distance=>100],
    [stunned=>1], [contract=>0], [completed=>{}]
) {
    reset_state(); $c=client(@$case);
    plugin::epic05_dialogue($c,$npc,'journal attune guardian');
    ok(!$plugin::states{7},'invalid hub/eligibility state refuses attunement: '.$case->[0]);
}
for my $case ([item=>1],[stunned=>1],[casting=>1],[contract=>0],[level=>34],[hp=>0],[completed=>{}]) {
    reset_state(); $plugin::states{7}={active_path=>'guardian',remaining=>0};
    $c=client(@$case);
    is(plugin::epic05_click($c,0),1,'rejected click remains intercepted');
    is(scalar @{$c->{casts}},0,'invalid click state refuses ability: '.$case->[0]);
    is($plugin::states{7}{remaining},0,'rejected click consumes no cooldown');
}
reset_state(); $c=client(); $plugin::states{7}={active_path=>'guardian',remaining=>0};
plugin::epic05_click($c,22);
is(scalar @{$c->{casts}},0,'bag click cannot borrow equipped eligibility');
$plugin::write_failure=1;
plugin::epic05_click($c,0);
is(scalar @{$c->{casts}},0,'failed or uncertain DB reserve never applies power');
$plugin::write_failure=0; $plugin::enabled=0;
plugin::epic05_click($c,0);
is(scalar @{$c->{casts}},0,'disabled release refuses power');

reset_state(); $plugin::states{7}={active_path=>'binder',remaining=>0};
$c=client(target=>bless({owner=>8},'EpicPet'));
plugin::epic05_click($c,0);
is(scalar @{$c->{casts}},0,'foreign pet rejected');
is($plugin::states{7}{remaining},0,'invalid pet does not spend cooldown');
$c->{target}{owner}=7;
plugin::epic05_click($c,0);
is(scalar @{$c->{casts}},1,'one owned target receives binder ability');
is($c->{casts}[0][1],$c->{target},'binder does not multiply across pet roster');

{
    package EpicItemQuest;
    our($client,$slotid);
    do "$main::root/server-mods/quests/global/items/900501.pl" or die $@ || $!;
}
$EpicItemQuest::client=$c; $EpicItemQuest::slotid=0;
is(EpicItemQuest::EVENT_ITEM_CLICK_CAST(),1,'real item entry point intercepts activation');
done_testing();
