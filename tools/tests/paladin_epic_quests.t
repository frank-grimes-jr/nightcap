use strict;
use warnings;
use Test::More;
our ($client,$npc,$text,$item1,$item2,$item3,$item4,$item1_charges,$item2_charges,$item3_charges,$item4_charges,$platinum);
our (@speech,@rewards,@removed,$exchanges,$returns);
sub quest::say {push @speech,$_[0]}
sub quest::summonitem {push @rewards,[@_]}
sub quest::givecash {die 'Unexpected manual cash return'}
{
 package MockClient;
 sub GetClass {$_[0]->{class}}
 sub AscendPaladinEpic {$main::exchanges++;1}
 sub CountItem {$_[1]==10908?1:0}
 sub RemoveItem {push @main::removed,[@_[1,2]]}
 sub GetName {'Tester'}
 package MockNPC;
 sub ReturnHandinItems {$main::returns++}
}
for my $path (@ARGV) {
 no warnings 'redefine';
 do $path or die "$path: $@ $!";
 $client=bless {class=>3},'MockClient';$npc=bless {},'MockNPC';
 @speech=();$text='hail';EVENT_SAY();
 like(join(' ',@speech),qr/awards Ascended Fiery Defender directly/,'Paladin direct reward explained');
 unlike(join(' ',@speech),qr/100,000/,'Paladin not asked for payment');
 $exchanges=0;$text='ascend fiery defender';EVENT_SAY();is($exchanges,1,'free exchange dispatched once');
 $returns=0;@rewards=();@removed=();EVENT_ITEM();
 is($returns,1,'native original-instance and all-currency return dispatched once');
 is(scalar @rewards,0,'no duplicate summons');is(scalar @removed,0,'no handin inventory removal');
 $client->{class}=1;($item1,$item2,$item3,$item4)=(900000,0,0,0);
 ($item1_charges,$item2_charges,$item3_charges,$item4_charges)=(8,0,0,0);$platinum=100000;
 EVENT_ITEM();is_deeply(\@removed,[[10908,1]],'Warrior original recipe consumes epic');
 is_deeply(\@rewards,[[810908]],'Warrior original recipe grants reward');
}
done_testing();
