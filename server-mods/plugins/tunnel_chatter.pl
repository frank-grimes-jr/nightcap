use strict;
use warnings;

sub tunnel_market_ids { return (999500..999509, 999680..999685); }
sub tunnel_voice_ids { return (999520..999525, 999700..999707); }

sub tunnel_dialogue {
    my ($id)=@_;
    my %voices=(
        999520=>[
            'Crafted plate, two good blades, and enough room to swing. That is all I ask.',
            'A shield is sensible. So is killing it before it needs a second swing.',
            'If anyone asks, that dent in my breastplate was a dragon. A very small dragon.',
            'I sharpened both swords. Now I just need a plan worth sharpening them for.',
            'The smith says this armor has another expedition in it. He said that three expeditions ago.',
            'Buy your bandages before you need them. Learned that lesson the expensive way.'],
        999521=>[
            'Ghoulbane makes the road a little quieter. Usually after making it considerably louder.',
            'Anyone heading toward Unrest? Take a friend and leave room for a retreat.',
            'Good armor helps. Knowing when to pull back helps more.',
            'I offered the skeleton a chance to surrender. It was not much of a conversationalist.',
            'A blessing, fresh water, then we can talk about that dungeon.',
            'If you see someone making a corpse run, spare them a moment.'],
        999522=>[
            'I was standing right here the whole time. Ask anyone who did not see me.',
            'Lovely purse. Terrible knot. Just an observation.',
            'The secret passage was shorter. The corpse recovery was longer.',
            'Has anyone seen my spare dagger? Small, sharp, expensive sentimentally.',
            'A locked door is just a conversation that has not started yet.',
            'I always scout ahead. Sometimes I even tell the group what I found.'],
        999523=>[
            'Fear teaches patience. Bringing back the armor takes a little more than that.',
            'The tunnel lanterns make this armor look much less haunted.',
            'You can tell a good expedition by how quietly everyone eats afterward.',
            'That last pull needed one less monster and one more escape route.',
            'I came here for supplies. Somehow I am comparing boots again.',
            'A fine weapon is no substitute for keeping an eye on your healer.'],
        999524=>[
            'Level twelve, full bronze, and a goblin in Butcherblock still got me. Anyone seen my corpse?',
            'Every tree in Butcherblock looks like the tree beside the goblin that killed me. Still no corpse.',
            'I bought a map of Butcherblock. Unfortunately the goblin did not mark where it left my corpse.',
            'If you find a bronze-clad corpse in Butcherblock, that is mine. Tell the goblin I will be back.',
            'New plan: find the Butcherblock corpse, recover the bronze, avoid that particular goblin.',
            'Someone said follow the road in Butcherblock. My corpse and that goblin were definitely off it.'],
        999525=>[
            'The rings are open. Hail me if you need a road with fewer footsteps.',
            'I can take you to the stones. What you do after arriving is the adventurous part.',
            'Please count your companions before we leave. Pets, too.',
            'The forest smells like rain today. Much better than wet armor.',
            'A quiet moment at the rings is worth more than people think.',
            'Buy your food before asking for a port. The trees are not merchants.'],
    );
    return $voices{$id} if exists $voices{$id};
    return [
        'Anyone heading to the orc camps? I have supplies and a questionable sense of direction.',
        'Came in for water. Left with three bags of things I might need someday.',
        'There is room at the forge if you do not mind my first attempt at a helmet.',
        'That last group was good company. Even the corpse run.',
        'If I sell these boots I can afford the spell. Then I will need boots again.',
        'The tunnel is the only camp where my boots stay dry.',
        'Has anyone else carried a quest item so long they forgot whose quest it was?',
        'Someone remind me to buy food before I leave this time.',
        'I went into Guk for an hour. That was yesterday.',
        'Fresh arrows, full waterskin, empty bags. I give that last part ten minutes.',
        'Almost had that pull. Almost is doing a lot of work there.',
        'The kiln was hot. The pot was fragile. My confidence was misplaced.',
        'A proper conversation should last longer than the walk to the bank.',
        'Waiting on one more friend. They said they were nearly here a while ago.',
        'That smith makes it look easy. Mine came out shaped like a question.',
        'I am taking the long road home. Fewer things on it know my name.'
    ];
}

sub tunnel_choose {
    my ($coordinator,$key,@choices)=@_;
    my $last=$coordinator->GetEntityVariable($key);
    my @eligible=grep { !defined($last) || "$_" ne "$last" } @choices;
    @eligible=@choices unless @eligible;
    return unless @eligible;
    my $chosen=$eligible[int(rand(@eligible))];
    $coordinator->SetEntityVariable($key,$chosen);
    return $chosen;
}

sub tunnel_chatter_pulse {
    my ($entities,$coordinator)=@_;
    my @clients=$entities->GetClientList();
    return unless @clients && $coordinator;
    my @voices=grep { $entities->GetNPCByNPCTypeID($_) } tunnel_voice_ids();
    my $id=tunnel_choose($coordinator,'tunnel_last_voice',@voices);
    return unless defined $id;
    my $npc=$entities->GetNPCByNPCTypeID($id);
    my $lines=tunnel_dialogue($id);
    my $index=tunnel_choose($coordinator,'tunnel_line_'.$id,0..$#$lines);
    $_->TunnelChatter($npc->GetID(),$lines->[$index]) for @clients;
}

1;
