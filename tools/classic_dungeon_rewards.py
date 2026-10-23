"""Authored Classic raid relics. Templates cap power; identity is never inferred."""
from copy import deepcopy

# zone: (title, shared design, role, resistance, inspect lore). Lore is authored
# Nightcap fiction inspired by the zone, not a claim these were original EQ loot.
DESIGNS = {
    'chapterhouse': (
        ('Blade of the Released Dawn',11,'melee','mr','An oath released from the knight who would not yield.'),
        ('Mantle of the First Dawn',20,'guardian','dr','The fallen order remembers those who kept the vigil.'),
        ('Seal of the Rekindled Chapel',17,'healer','mr','The chapel is quiet; its light has returned.')),
    'blackburrow': (
        ("Elgnub's Burrowfang",10,'melee','pr','A fang claimed from the lord beneath the hills.'),
        ('Blackburrow Packwarden Mantle',20,'guardian','cr','Gnoll-hide stitched for the long watch over the burrow.'),
        ("Brewer's Amber Seal",17,'balanced','pr','An amber seal carrying the scent of a stolen cask.')),
    'crushbone': (
        ("Crush's Broken Scepter",9,'melee','mr','An emperor commands nothing when his scepter is broken.'),
        ("Ambassador's Ashen Veil",19,'caster','fr','The last disguise of an envoy whose bargain failed.'),
        ('Liberator of the Pens',21,'guardian','pr','Broken slave-chain links reforged into a belt of freedom.')),
    'runnyeye': (
        ('Pickclaw Tunnelbreaker',11,'melee','mr','A broad blade beaten thin against the stone of Runnyeye.'),
        ('Evil Eye Witness',18,'caster','mr','The watching eye is closed; the witness remembers.'),
        ('Crown of the Pickclaw Court',0,'guardian','dr','A court of tunnels needs no sunlight for its crown.')),
    'soldunga': (
        ("Goblin King's Cinderstaff",12,'caster','fr','The king of the furnace has surrendered his fire.'),
        ('Firebloom Forgegrips',4,'melee','fr','Soot darkens the runes; the forge still remembers.')) + (
        ('Embervault Reliquary',23,'balanced','fr','A cooled cinder seals the treasures of the goblin king.'),),
    'guktop': (
        ("Shinlord's Oathblade",8,'melee','mr','An oath sworn beneath the swamp outlasts its keeper.'),
        ('Heart of the Living Guk',18,'healer','pr','A living pulse answers the darkness below.'),
        ('Reedwoven Watcher Boots',6,'guardian','pr','Soft steps keep watch over the living halls.')),
    'gukbottom': (
        ("Ghoul Lord's Last Decree",11,'melee','dr','The dead court receives its final decree.'),
        ('Pall of the Silent Court',20,'caster','dr','A burial pall woven for a court that would not rest.'),
        ('Seal of Released Souls',17,'healer','mr','The seal is broken; the voices beneath Guk fall silent.')),
    'mistmoore': (
        ("Xicotl's Midnight Talon",10,'melee','dr','A talon lifted from the midnight watch.'),
        ('Mistmoore Bloodless Gorget',18,'guardian','dr','A cold collar worn by one who refused the feast.'),
        ('Echo of the Unfinished Waltz',16,'caster','mr','One note remains after the castle falls silent.')),
    'kedge': (
        ("Phinigel's Tidebound Trident",13,'melee','cr','A final tide curls around the last master of Kedge.'),
        ('Pearl of the Drowned Chorus',16,'healer','cr','A pearl holds songs no surface voice can sing.'),
        ('Kedge Deepcurrent Robe',1,'caster','mr','The current remembers where the old halls once stood.')),
    'paw': (
        ("Ishva's Splitpaw Knuckles",15,'melee','pr','The pack yields when its strongest fist is broken.'),
        ('Splitpaw Spiritcord',21,'healer','mr','A shaman binds a memory where a claw once hung.'),
        ('Denfather Stoneguard',7,'guardian','pr','A shoulder guard weathered by the deepest den.')),
    'hole': (
        ('Wretched Stonecleaver',9,'melee','mr','Irslak leaves a fracture in every stone he strikes.'),
        ('Pael Sealed Memory',19,'caster','dr','A sealed memory survives beneath the fallen city.'),
        ('Earthbound Oathplate',1,'guardian','mr','Stone remembers an oath long after its speaker is dust.')),
    'qcat': (
        ("Omorb's Sluicefang",10,'melee','pr','A narrow fang pulled from beneath the city streets.'),
        ('Catacomb Vigil Lantern',18,'healer','dr','A small light kept burning for the forgotten dead.'),
        ('Qeynos Underway Satchel',22,'balanced','pr',"Dry seams guard a courier through the city's hidden ways.")),
    'fearplane': (
        ('Spine of the Faceless',13,'melee','dr','Even the Faceless casts a shadow upon the fearless.'),
        ('Visage of Unbroken Will',19,'guardian','mr','Look into fear until its unseen shape is revealed.'),
        ('Dreadhusk of the Last Stand',1,'guardian','dr','The last stand belongs to the one who refuses to flee.')),
    'hateplane': (
        ("Innoruuk's Severed Covenant",10,'melee','mr','A royal covenant severed in the halls of the Prince of Hate.'),
        ("Maestro's Unfinished Requiem",18,'caster','mr','The final note goes unheard; its bearer passes unseen.'),
        ('Seal of the First Betrayal',17,'healer','dr','Two broken crowns remember the hatred that remade them.')),
    'airplane': (
        ("Veeshan's Unwritten Horizon",14,'melee','cr','No mortal arrow can mark the edge of the Crystalline sky.'),
        ('Mantle of the First Brood',20,'guardian','mr',"A mortal tribute to the brood beneath Veeshan's wings."),
        ('Astrolabe of the Eighth Island',18,'healer','mr','Eight islands charted; the horizon remains beyond reach.')),
}

# Existing Classic utilities only. Shared across qualities and duplicate copies.
# Reserved groups 91..93 map to native persistent timers 191..193, inside the
# item namespace. Migration and runtime guards exclude unrelated item use.
CLICKS = {
    ('fearplane',1): (80,'See Invisible',300,91),
    ('hateplane',1): (42,'Invisibility',600,92),
    ('airplane',2): (261,'Levitate',900,93),
}
CLICK_DEFAULTS=dict(clicktype=0,clicklevel=0,clicklevel2=0,casttime=0,
                    casttime_=0,maxcharges=0,recastdelay=0,recasttype=0,clickname='')

def added_rewards(existing,dungeons):
    result=[]
    templates={(r['band'],r['design'],r['quality']):r['values']
               for r in existing if r['source']=='completion'}
    for index,(zone,_,_,band,_) in enumerate(dungeons[7:],7):
        for design,(title,template,role,resist,lore) in enumerate(DESIGNS[zone]):
            for quality in ('Polished','Ascended'):
                q=1 if quality=='Polished' else 2
                item=deepcopy(templates[band,template,quality])
                item.update(CLICK_DEFAULTS)
                ident=960288+index*6+design*2+q-1
                item.update(id=ident,Name=quality+' '+title,lore=lore,magic=1,reclevel=band)
                if zone in ('fearplane','hateplane','airplane'):
                    item['reqlevel']=46
                if item['itemclass']!=1:
                    # Move the existing resist budget, never add to it.
                    budget=sum(item[k] for k in ('mr','fr','cr','pr','dr'))
                    for k in ('mr','fr','cr','pr','dr'):item[k]=0
                    item[resist]=budget
                    # All roles retain existing HP/mana/endurance and spell
                    # power ceilings. Identity comes from relevant stat pairs,
                    # resist choice, slots, lore and the planar utility clicks.
                    stat=max(item[k] for k in ('astr','asta','aagi','adex','aint','awis','acha'))
                    for k in ('astr','asta','aagi','adex','aint','awis','acha'):item[k]=0
                    pair={'melee':('astr','adex'),'guardian':('asta','aagi'),
                          'caster':('aint','asta'),'healer':('awis','asta'),
                          'balanced':('adex','awis')}[role]
                    for k in pair:item[k]=stat
                if (zone,design) in CLICKS:
                    spell,name,reuse,group=CLICKS[zone,design]
                    item.update(clickeffect=spell,clicktype=4,clicklevel=46,clicklevel2=46,
                                casttime=10000,casttime_=10000,maxcharges=-1,
                                recastdelay=reuse,recasttype=group,clickname=name)
                assert len(item['Name'].encode())<64 and len(lore.encode())<80
                result.append(dict(id=ident,band=band,quality=quality,design=design,
                                   source=zone,template=template,role=role,values=item))
    return result
