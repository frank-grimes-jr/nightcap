"""Append-only Classic zone coverage; IDs are reviewed public content identities.

The first seven dungeon indices, objectives and exclusive rewards remain owned
by dungeon_catalog.py. Added finals draw existing shared-band reward designs.
"""

ADDED_DUNGEONS = [
    ('blackburrow',17,998800,20,[17021,17035,17042,17029]),
    ('crushbone',58,998801,20,[58040,58002,58028,58031,58059,58032]),
    ('runnyeye',11,998802,30,[11124,11067,11015,11086,11017]),
    ('soldunga',31,998803,40,[31124,31085,31127,31136,31134,31022,31126,31128]),
    ('guktop',65,998804,30,[65140,65146,65148,65105,65104,65125,65128]),
    ('gukbottom',66,998805,50,[66178,66173,66021,66092,66171,66165,66169,66146,66156,66159,66005]),
    ('mistmoore',59,998806,40,[59133,59020,59102,59116,59115,59150,59089,59151,59152]),
    ('kedge',64,998807,50,[64102,64103,64107,64093,64105,64106,64089,64087,64029,64001]),
    ('paw',18,998808,40,[18144,18116,18122,18138,18141,18142,18136]),
    ('hole',39,998809,50,[39132,39037,39006,39141,39162]),
    ('qcat',45,998810,20,[45007,45096,45101,45041,45117]),
    ('fearplane',72,998811,50,[72000,72002,72004,72090,72003]),
    ('hateplane',76,998812,50,[76019,76015,76011,76007]),
    ('airplane',71,998813,50,[71032,71059,71021,71075,71013,71012,71072,71076,71065]),
]

# Script-only key bosses need canonical spawn identities for durable Raid
# deaths/credit and restart-safe Grind timers. Public spawn definitions stay put.
# Locations retain the deployed scripts' islands. Script-only bosses use eight
# hours; the princess retains her native four-hour interval.
SKY_PRIVATE = [
    (9200000,986000,71059,-602.2,-254.4,-333.5,403),
    (9200001,986001,71075,-996.3,910.5,192.3,36),
    # Ground-probed island surface; the old delayed script's z=843 floats40u.
    (9200002,986002,71072,94,-890,806,0),
    (9200003,986003,71076,-929,-1035,1093,128),
    # The current native princess point is gated to expansion 1. Keep that
    # public row unchanged and restore the key encounter only in managed Sky.
    (9200004,986004,71032,609,1372,-658,385),
]

def sky_respawn(npc_id):
    return 14400 if npc_id == 71032 else 28800

# Canonical noncombat Sirran copies survive the managed native reload path,
# which intentionally does not replay dynamic living quest NPCs. Keep token
# requirements; each original key-exchange island has its own reachable service.
SKY_KEY_SERVICE = 998814
SKY_SERVICES = [
    (9200005,986005,SKY_KEY_SERVICE,688,1381,-645,384),
    (9200006,986006,SKY_KEY_SERVICE,-531,-214,-322,256),
    (9200007,986007,SKY_KEY_SERVICE,320,540,-54,256),
    (9200008,986008,SKY_KEY_SERVICE,-543,767,174,128),
    (9200009,986009,SKY_KEY_SERVICE,955,-570,466,390),
    (9200010,986010,SKY_KEY_SERVICE,234,-1078,812,384),
    (9200011,986011,SKY_KEY_SERVICE,-960,-1037,1093,128),
]

ALL_CLASSIC_ZONES = frozenset((
    'befallen','unrest','highkeep','najena','cazicthule','permafrost','soldungb',
    *(d[0] for d in ADDED_DUNGEONS)))
