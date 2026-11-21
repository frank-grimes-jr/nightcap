use strict;
use warnings;
use FindBin;
use Test::More;

{ package plugin; require "$FindBin::Bin/../../server-mods/plugins/cairnwright.pl"; }
{ package Strike; our ($client, $caster_id, $spell_id, $entity_list); require "$FindBin::Bin/../../server-mods/quests/global/spells/44381.pl"; }
{ package Sound; our ($client, $caster_id, $spell_id, $entity_list); require "$FindBin::Bin/../../server-mods/quests/global/spells/44382.pl"; }
{
    package Actor;
    sub new { my ($class, %args) = @_; bless { x=>0, y=>0, z=>0, %args }, $class }
    sub GetID { $_[0]->{id} }
    sub GetX { $_[0]->{x} }
    sub GetY { $_[0]->{y} }
    sub GetZ { $_[0]->{z} }
    sub IsMulticlassMember { $_[1] == 17 && $_[0]->{held} }
    sub GetEntityVariable { $_[0]->{vars}{$_[1]} // '' }
    sub SetEntityVariable { $_[0]->{vars}{$_[1]} = $_[2] }
    sub DeleteEntityVariable { delete $_[0]->{vars}{$_[1]} }
    sub GetGroup { undef }
    sub GetCloseMobList { @{$_[0]->{mobs}} }
    sub IsNPC { 1 }
    sub GetOwnerID { $_[0]->{owner} // 0 }
    sub IsAttackAllowed { !$_[1]->{protected} }
    sub CheckAggro { $_[0]->{engaged} }
    sub CheckLoS { !$_[1]->{hidden} }
    sub CheckLoSToLoc { !$_[0]->{blocked} }
    sub GetMobByID {
        my ($self, $id) = @_;
        return (grep { $_->GetID == $id } @{$self->{mobs}})[0];
    }
    sub SpellFinished {
        my ($self, $spell, $mob, $mana) = @_;
        push @{$self->{hits}}, [$spell, $mob->GetID, $mana];
    }
    sub Message { }
}
my $actor = Actor->new(id=>70, held=>1);
sub cast_spell {
    my ($id) = @_;
    if ($id == 44381) {
        local ($Strike::client, $Strike::caster_id, $Strike::spell_id, $Strike::entity_list)
            = ($actor, $actor->GetID, $id, $actor);
        return Strike::EVENT_SPELL_EFFECT_CLIENT();
    }
    local ($Sound::client, $Sound::caster_id, $Sound::spell_id, $Sound::entity_list)
        = ($actor, $actor->GetID, $id, $actor);
    return Sound::EVENT_SPELL_EFFECT_CLIENT();
}
sub pulse {
    $actor->{hits} = [];
    cast_spell(44382);
    return $actor->{hits};
}

is_deeply(pulse(), [], 'no strike before placement');
plugin::cairnwright_spell($actor, 71, 44381, $actor);
ok(!$actor->GetEntityVariable('cairnwright.stone'), 'another caster cannot place the stone');
cast_spell(44381);
ok($actor->GetEntityVariable('cairnwright.stone'), 'placed at origin');
$actor->{mobs} = [map { Actor->new(%$_) } (
    {id=>1,x=>8,engaged=>1}, {id=>2,x=>18,engaged=>1}, {id=>3,x=>15,engaged=>1},
    {id=>4,x=>19,y=>5,engaged=>1}, {id=>5,x=>19,z=>7,engaged=>1},
    {id=>6,x=>19,engaged=>0}, {id=>7,x=>19,engaged=>1,owner=>111},
    {id=>8,x=>21,engaged=>1}, {id=>9,x=>19,engaged=>1,blocked=>1},
    {id=>10,x=>19,engaged=>1,hidden=>1}, {id=>11,x=>19,engaged=>1,protected=>1},
)];
is_deeply(pulse(), [], 'standing on the stone cannot pulse');
$actor->{x} = 20;
is_deeply(pulse(), [[44383,2,0],[44383,3,0]], 'two nearest valid opponents from hammer, one child hit each');
$actor->{x} = 61;
is_deeply(pulse(), [], 'out of reach');
$actor->{x} = 20;
$actor->{blocked} = 1;
is_deeply(pulse(), [], 'blocked seam');
$actor->{blocked} = 0;
$actor->{held} = 0;
is_deeply(pulse(), [], 'ownership lost');
$actor->{held} = 1;
$actor->SetEntityVariable('cairnwright.stone', '0,0,0,0');
is_deeply(pulse(), [], 'expired stone');
ok(!$actor->GetEntityVariable('cairnwright.stone'), 'expired state removed');
cast_spell(44381);
like($actor->GetEntityVariable('cairnwright.stone'), qr/,20,0,0$/, 'recast replaces the one owned stone');
done_testing;
