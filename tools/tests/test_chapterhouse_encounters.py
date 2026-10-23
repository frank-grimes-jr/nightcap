"""Execute authored Perl encounters with entity/timer doubles, without a server."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]

class Encounters(unittest.TestCase):
    def test_warning_interrupt_escape_and_owned_add_cleanup(self):
        perl=shutil.which('perl')
        self.assertIsNotNone(perl,'Perl is required for quest behavior tests')
        fixture=r'''
use strict;use warnings;use Test::More;
our (%timers,%entities,$next,$hp,$combat_state,$timer,$hpevent,$npc,$entity_list);
package Mob;
sub new {my($c,$id)=@_;my $m=bless {id=>$id,x=>0,y=>0,z=>0,vars=>{},engaged=>1},$c;$main::entities{$id}=$m;return $m;}
sub GetID {$_[0]{id}} sub GetX {$_[0]{x}} sub GetY {$_[0]{y}} sub GetZ {$_[0]{z}}
sub IsEngaged {$_[0]{engaged}} sub IsStunned {$_[0]{stunned}} sub IsMezzed {$_[0]{mezzed}}
sub GetTarget {$_[0]{target}} sub Emote {$_[0]{emotes}++}
sub CastSpell {my($s,@args)=@_;push @{$s->{casts}},\@args;}
sub SetEntityVariable {$_[0]{vars}{$_[1]}=$_[2]} sub GetEntityVariable {$_[0]{vars}{$_[1]}//''}
sub AddToHateList {$_[0]{hate}=$_[1]} sub Depop {$_[0]{depop}=1}
package Entities;sub GetNPCByID {$main::entities{$_[1]}}
package quest;
sub settimer {$main::timers{$_[0]}=$_[1]} sub stoptimer {delete $main::timers{$_[0]}}
sub setnexthpevent {$main::hp=$_[0]}
sub spawn2 {main::is($_[0],998836,'only the no-loot shade');my $m=Mob->new(++$main::next);$m->{x}=$_[3];return $m->GetID();}
package main;
$next=100;$entity_list=bless {},'Entities';$npc=Mob->new(1);$npc->{target}=Mob->new(2);
{package Bell;our($npc,$client,$combat_state,$timer);}
{package Watch;our($npc,$client,$entity_list,$combat_state,$hpevent);}
my $dir=shift;
{open my $f,'<',"$dir/998821.pl" or die $!;local $/;eval 'package Bell;our($npc,$client,$combat_state,$timer);'.<$f>;die $@ if $@;}
$Bell::npc=$npc;$Bell::combat_state=1;Bell::EVENT_COMBAT();is($timers{bell},15,'bell cadence');
$Bell::timer='bell';Bell::EVENT_TIMER();is($timers{resolve_bell},3,'three second warning');
$Bell::timer='resolve_bell';$npc->{stunned}=1;Bell::EVENT_TIMER();ok(!$npc->{casts},'stun interrupts bell');
$npc->{stunned}=0;$npc->{target}{x}=31;Bell::EVENT_TIMER();ok(!$npc->{casts},'escape warning radius');
$npc->{target}{x}=30;Bell::EVENT_TIMER();is_deeply($npc->{casts}[0],[216,2,1,0,0],'Classic Stun at boundary');
$Bell::combat_state=0;Bell::EVENT_COMBAT();is_deeply(\%timers,{},'wipe cancels both timers');
{open my $f,'<',"$dir/998822.pl" or die $!;local $/;eval 'package Watch;our($npc,$client,$entity_list,$combat_state,$hpevent);'.<$f>;die $@ if $@;}
$Watch::npc=$npc;$Watch::entity_list=$entity_list;Watch::EVENT_SPAWN();is($hp,50,'half health trigger');
$Watch::hpevent=50;Watch::EVENT_HP();my @ids=split /,/,$npc->GetEntityVariable('vigil-watch-adds');
is(scalar @ids,2,'two adds');is_deeply([map{$entities{$_}{x}}@ids],[-8,8],'bounded authored placement');
for(@ids){is($entities{$_}->GetEntityVariable('vigil-watch-owner'),1,'owned by warden');is($entities{$_}{hate},$npc->{target},'targets combat participant');}
$entities{$ids[1]}->SetEntityVariable('vigil-watch-owner','another-attempt');
$Watch::combat_state=0;Watch::EVENT_COMBAT();ok($entities{$ids[0]}{depop},'own add cleaned');ok(!$entities{$ids[1]}{depop},'reused entity/other encounter preserved');
is($npc->GetEntityVariable('vigil-watch-adds'),'','cleanup idempotent');Watch::EVENT_DEATH_COMPLETE();

for my $boss (998823,998824) {
    my $package='Brand'.$boss;
    open my $f,'<',"$dir/$boss.pl" or die $!;local $/;my $code=<$f>;
    eval 'package '.$package.';our($npc,$client,$combat_state,$timer);'.$code;die $@ if $@;
    no strict 'refs';
    ${$package.'::npc'}=$npc;${$package.'::combat_state'}=1;
    &{$package.'::EVENT_COMBAT'}();is($timers{brand},$boss==998823?18:12,'boss-specific cadence');
    $npc->{casts}=[];$npc->{target}{x}=0;
    ${$package.'::timer'}='brand';&{$package.'::EVENT_TIMER'}();is($timers{resolve_brand},3,'brand warning');
    ${$package.'::timer'}='resolve_brand';$npc->{target}{x}=11;&{$package.'::EVENT_TIMER'}();
    is(scalar @{$npc->{casts}},0,'moving outside marked position escapes even if boss chases');
    $npc->{target}{x}=10;$npc->{stunned}=1;&{$package.'::EVENT_TIMER'}();
    is(scalar @{$npc->{casts}},0,'stun interrupts brand');
    $npc->{stunned}=0;&{$package.'::EVENT_TIMER'}();is_deeply($npc->{casts}[0],[329,2,1,0,0],'stationary boundary receives native Wrath');
    $npc->{target}{id}=3;&{$package.'::EVENT_TIMER'}();is(scalar @{$npc->{casts}},1,'target change cannot transfer mark');$npc->{target}{id}=2;
    ${$package.'::combat_state'}=0;&{$package.'::EVENT_COMBAT'}();is_deeply(\%timers,{},'wipe removes brand timers');
    &{$package.'::EVENT_DEATH_COMPLETE'}();is_deeply(\%timers,{},'death cleanup idempotent');
}
done_testing();
'''
        result=subprocess.run([perl,'-',str(ROOT/'server-mods/quests/chapterhouse')],input=fixture,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertRegex(result.stdout,r'1\.\.\d+')

if __name__=='__main__':unittest.main()
