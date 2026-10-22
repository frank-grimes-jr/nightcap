use strict;
use warnings;
our ($text,$name,$client);
$name='Tester';
$client=bless {}, 'RejectChanges';
package RejectChanges;
our $AUTOLOAD;
sub AUTOLOAD { die "Retired Goldwind called client mutation: $AUTOLOAD"; }
sub DESTROY {}
package quest;
our @messages;
sub say { push @messages, $_[0]; }
package main;
for my $path (@ARGV) {
 do $path; die "Cannot load $path: $@" if $@;
 for my $input ('hail','empower','EMPOWER') {
  @quest::messages=(); $text=$input; EVENT_SAY();
  die 'Missing Matron guidance' unless @quest::messages==1 && $quest::messages[0]=~/Matron Restora/ && $quest::messages[0]=~/free blessings/;
 }
}
print "PASS: retired hail/empower performs no client mutations in both scripts\n";
