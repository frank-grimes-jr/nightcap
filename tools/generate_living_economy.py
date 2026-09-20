"""Generate guarded market content and NPC quests from read-only PEQ captures."""
import argparse
import copy
import json
from pathlib import Path
from living_economy import ROOT, prices
from pok_hub_migration import read_sql, sql_value

TRADERS = [
    ('Rellan_Ridgewalker',22033,-300,-1660), ('Mirielle_Dusksong',22087,-240,-1660),
    ('Caelith_Emberweave',22092,-80,-1650), ('Bromli_Copperkeg',22083,-35,-1705),
    ('Tamsin_Quickstep',22082,-90,-1735), ('Varkyn_Ashblade',22116,-155,-1750),
    ('Harlon_Frostbeard',22088,-230,-1735), ('Nimri_Mossfoot',22086,-300,-1720),
    ('Grukk_Bargainhand',22118,-390,-1710), ('Selindra_Starsong',22073,-385,-1585),
]
CITIES = ['qeynos','qeynos2','freportw','freporte','gfaydark','rivervale','halas','neriakb','grobb','oggok','erudnext','akanon']


def rows(sql):
    return [json.loads(s) for s in read_sql(sql).splitlines()]


def insert(table, row):
    return f'INSERT INTO `{table}` ('+','.join('`'+c+'`' for c in row)+') VALUES ('+','.join(sql_value(v) for v in row.values())+');'


def guard(query, expected, label):
    return query.replace('SELECT COUNT(*)','SELECT COUNT(*) INTO n',1)+f";\nIF n<>{expected} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='{label}'; END IF;"


def generate(output, refresh=False):
    if refresh and output.resolve() != (ROOT/'docs/economy/generated').resolve():
        raise ValueError('Refresh is limited to the checked-in generated market package')
    if output.exists() and not refresh:
        raise ValueError('Refusing to overwrite generated evidence')
    policy = json.loads((ROOT/'docs/economy/policy.json').read_text())
    catalog = json.loads((ROOT/'docs/economy/catalog-20260920.json').read_text())
    rules = rows("SELECT JSON_OBJECT('name',rule_name,'value',rule_value) FROM rule_values WHERE ruleset_id=1 AND rule_name IN "
                 "('Expansion:CurrentExpansion','Merchant:BuyCostMod','Zone:GlobalLootMultiplier','Merchant:SellCostMod',"
                 "'Merchant:PriceBonusPct','Merchant:PricePenaltyPct','Merchant:UsePriceMod','Merchant:UseClassicPriceMod');")
    expected = {'Expansion:CurrentExpansion':str(policy['expansion']), 'Merchant:BuyCostMod':policy['buy_cost_mod'],
                'Zone:GlobalLootMultiplier':str(policy['global_loot_multiplier']), 'Merchant:SellCostMod':policy['sell_cost_mod'],
                'Merchant:PriceBonusPct':str(policy['price_bonus_pct']), 'Merchant:PricePenaltyPct':str(policy['price_penalty_pct']),
                'Merchant:UsePriceMod':'true','Merchant:UseClassicPriceMod':'false'}
    if {r['name']:r['value'] for r in rules} != expected:
        raise ValueError('Live era/economy rules differ from reviewed pricing policy')
    columns = read_sql('SHOW COLUMNS FROM npc_types;').splitlines()
    cols = [line.split('\t')[0] for line in columns]
    template_ids = ','.join(str(t[1]) for t in TRADERS)
    templates = rows('SELECT JSON_OBJECT('+','.join(sql_value(c)+',`'+c+'`' for c in cols)+
                     ') FROM npc_types WHERE id IN ('+template_ids+');')
    template_map = {r['id']:r for r in templates}
    merchants = []
    for city in CITIES:
        candidates = rows("SELECT JSON_OBJECT('npc_id',n.id,'name',n.name,'zone',s.zone,'zone_id',z.zoneidnumber,"
            "'merchant_id',n.merchant_id,'x',s.x,'y',s.y,'z',s.z) FROM npc_types n "
            "JOIN spawnentry e ON e.npcID=n.id JOIN spawn2 s ON s.spawngroupID=e.spawngroupID "
            "JOIN zone z ON z.short_name=s.zone AND z.version=0 WHERE s.zone="+sql_value(city)+
            " AND s.version=0 AND s.min_expansion<=0 AND n.class=41 AND n.alt_currency_id=0 "
            "AND (SELECT COUNT(*) FROM merchantlist m WHERE m.merchantid=n.merchant_id) BETWEEN 1 AND 40 "
            "AND (SELECT MAX(slot) FROM merchantlist m WHERE m.merchantid=n.merchant_id)<60 "
            "AND (SELECT COUNT(*) FROM spawnentry se JOIN spawn2 ss ON ss.spawngroupID=se.spawngroupID WHERE se.npcID=n.id)=1 "
            "AND (SELECT COUNT(*) FROM spawnentry se WHERE se.spawngroupID=s.spawngroupID)=1 "
            "ORDER BY n.id LIMIT 1;")
        if len(candidates) != 1:
            raise ValueError('No unambiguous city merchant: '+city)
        merchants += candidates
    reserved = 'BETWEEN 999500 AND 999509'
    collisions = {'npc_types':f'id {reserved}', 'spawngroup':f'id {reserved}',
                  'spawnentry':f'spawngroupID {reserved} OR npcID {reserved}',
                  'spawn2':f'id {reserved} OR spawngroupID {reserved}',
                  'zone_state_spawns':f'npc_id {reserved} OR spawngroup_id {reserved} OR spawn2_id {reserved}'}
    for table, where in collisions.items():
        if read_sql(f'SELECT COUNT(*) FROM {table} WHERE {where};').strip() != '0':
            raise ValueError('Reserved identity collision: '+table)
    guards = [guard(f'SELECT COUNT(*) FROM {table} WHERE {where} FOR UPDATE',0,'Market identity collision '+table)
              for table,where in collisions.items()]
    tables = ['npc_types','spawngroup','spawnentry','spawn2','zone_state_spawns','inventory','character_currency',
              'nightcap_market_state','nightcap_market_catalog','nightcap_market_actors','nightcap_market_offers','nightcap_market_trades']
    table_list = ','.join(sql_value(t) for t in tables)
    guards.insert(0,guard('SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() '
                         f"AND TABLE_NAME IN({table_list}) AND ENGINE='InnoDB'",len(tables),'Market requires transactional tables'))
    guards.insert(1,guard('SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() '
                         f'AND EVENT_OBJECT_TABLE IN({table_list})',0,'Unexpected market trigger'))
    guards.append(guard('SELECT COUNT(*) FROM nightcap_market_state WHERE id=1 AND enabled=0',1,'Market must be disabled'))
    for name,value in expected.items():
        guards.append(guard('SELECT COUNT(*) FROM rule_values WHERE ruleset_id=1 AND rule_name='+sql_value(name)+
                            ' AND rule_value='+sql_value(value),1,'Market rules changed'))
    inserts = [f"UPDATE nightcap_market_state SET loot_multiplier={int(policy['global_loot_multiplier'])},"
               f"buy_cost_mod={sql_value(policy['buy_cost_mod'])} WHERE id=1 AND enabled=0;"]
    for item in catalog['items']:
        item.update(prices(item['reference_pp'],item['price'],policy,item['sellrate']))
        guards.append(guard(f"SELECT COUNT(*) FROM items WHERE id={item['id']} AND nodrop<>0 AND norent<>0 "
            f"AND stackable=0 AND maxcharges=0 AND itemclass=0 AND questitemflag=0 AND attuneable=0 "
            f"AND price={item['price']} AND sellrate={item['sellrate']}",1,'Market item drift'))
        # Infinite merchant stock would turn finite WTB into a repeatable shop route.
        if item['pool'] == 'tunnel':
            if read_sql(f"SELECT COUNT(*) FROM merchantlist WHERE item={item['id']} AND min_expansion<=0;").strip() != '0':
                raise ValueError('Tunnel item already in permanent merchant stock: '+item['Name'])
            guards.append(guard(f"SELECT COUNT(*) FROM merchantlist WHERE item={item['id']} AND min_expansion<=0",0,'Tunnel stock changed'))
        inserts.append(insert('nightcap_market_catalog',{
            'item_id':item['id'],'pool':item['pool'],'min_expansion':0,'max_expansion':-1,
            **{k:item[k] for k in ('find_cp','sell_cp','buy_cp')},'source_url':item['source_url'],
            'captured_at':catalog['captured_at'][:10]}))
    for merchant in merchants:
        guards.append(guard(f"SELECT COUNT(*) FROM npc_types WHERE id={merchant['npc_id']} AND class=41 "
                            f"AND merchant_id={merchant['merchant_id']} AND alt_currency_id=0",1,'Market merchant changed'))
        inserts.append(insert('nightcap_market_actors',{'npc_id':merchant['npc_id'],'zone_id':merchant['zone_id'],'kind':'find'}))
    traders = []
    for index,(name,template,x,y) in enumerate(TRADERS):
        identity = 999500+index
        row = copy.deepcopy(template_map[template])
        row.update(id=identity,name=name,lastname='Tunnel Trader',level=50,**{'class':1},
                   hp=100000,mana=0,loottable_id=0,merchant_id=0,alt_currency_id=0,npc_spells_id=0,
                   npc_spells_effects_id=0,npc_faction_id=0,adventure_template_id=0,trap_template=0,
                   special_abilities='19,1^20,1^24,1^35,1',npcspecialattks='',aggroradius=0,assistradius=0,
                   npc_aggro=0,always_aggro=0,raid_target=0,spawn_limit=1,findable=1,emoteid=0,
                   private_corpse=0,isquest=1,skip_global_loot=1,keeps_sold_items=0,is_parcel_merchant=0,
                   multiquest_enabled=0,qglobal=0,unique_spawn_by_name=1)
        if row['race'] not in range(1,13):
            raise ValueError('Non-Classic playable appearance')
        inserts.extend([insert('npc_types',row), insert('spawngroup',{'id':identity,'name':'NightcapMarket'+str(identity)}),
            insert('spawnentry',{'spawngroupID':identity,'npcID':identity,'chance':100}),
            insert('spawn2',{'id':identity,'spawngroupID':identity,'zone':'ecommons','version':0,
                            'x':x,'y':y,'z':3.75,'heading':128 if index%2 else 384,'respawntime':60,
                            'variance':0,'pathgrid':0,'min_expansion':0,'max_expansion':-1}),
            insert('nightcap_market_actors',{'npc_id':identity,'zone_id':22,'kind':'sell' if index<6 else 'buy'})])
        traders.append({'npc_id':identity,'name':name,'template':template,'race':row['race'],'gender':row['gender'],
                        'x':x,'y':y,'z':3.75,'kind':'sell' if index<6 else 'buy'})
    guards.append(guard('SELECT COUNT(*) FROM nightcap_market_actors',0,'Market already seeded'))
    guards.append(guard('SELECT COUNT(*) FROM nightcap_market_catalog',0,'Market catalog already seeded'))
    output.mkdir(parents=True,exist_ok=refresh)
    (output/'content.sql').write_text("DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE n BIGINT;\n"
        "DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\nSTART TRANSACTION;\n"+
        '\n'.join(guards+inserts)+"\nCOMMIT;\nEND //\nDELIMITER ;\n")
    (output/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (output/'placement.json').write_text(json.dumps({'merchants':merchants,'traders':traders,'policy':policy},indent=2)+'\n')
    (output/'probe-input.json').write_text(json.dumps({'map':'/home/eqemu/server/maps/base/ecommons.map',
        'points':[{'label':t['name'],**{k:t[k] for k in ('x','y','z')}} for t in traders]},indent=2)+'\n')
    rollback = [guards[0], guards[1], guard('SELECT COUNT(*) FROM nightcap_market_actors',22,'Actor set changed')]
    for trader in traders:
        identity=trader['npc_id']
        rollback.extend([
            guard(f"SELECT COUNT(*) FROM npc_types WHERE id={identity} AND name={sql_value(trader['name'])}",1,'Trader identity changed'),
            guard(f"SELECT COUNT(*) FROM spawngroup WHERE id={identity} AND name='NightcapMarket{identity}'",1,'Trader group changed'),
            guard(f"SELECT COUNT(*) FROM spawn2 WHERE id={identity} AND spawngroupID={identity} AND zone='ecommons' AND version=0",1,'Trader spawn changed')])
    rollback.extend([
        guard('SELECT COUNT(*) FROM spawnentry WHERE spawngroupID BETWEEN 999500 AND 999509 OR npcID BETWEEN 999500 AND 999509',10,'Unexpected spawn reference'),
        guard('SELECT COUNT(*) FROM spawn2 WHERE spawngroupID BETWEEN 999500 AND 999509',10,'Unexpected spawn placement'),
        'UPDATE nightcap_market_state SET enabled=0 WHERE id=1;',
        'DELETE FROM nightcap_market_offers;',
        'DELETE FROM nightcap_market_actors;',
        'DELETE FROM zone_state_spawns WHERE zone_id=22 AND instance_id=0 AND is_corpse=0 AND is_zone=0 '
        'AND (npc_id BETWEEN 999500 AND 999509 OR spawngroup_id BETWEEN 999500 AND 999509 OR spawn2_id BETWEEN 999500 AND 999509);',
        'DELETE FROM spawn2 WHERE id BETWEEN 999500 AND 999509;',
        'DELETE FROM spawnentry WHERE spawngroupID BETWEEN 999500 AND 999509;',
        'DELETE FROM spawngroup WHERE id BETWEEN 999500 AND 999509;',
        'DELETE FROM npc_types WHERE id BETWEEN 999500 AND 999509;'])
    (output/'rollback.sql').write_text('-- Stop world/zones first. Retains purchased items, wallets, catalog and trade audit.\n'
        'DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE n BIGINT;\n'
        'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\nSTART TRANSACTION;\n'+
        '\n'.join(rollback)+'\nCOMMIT;\nEND //\nDELIMITER ;\n')
    # Generated identical adapters keep all behavior in the single plugin.
    quests = ROOT/'server-mods/quests/ecommons'
    quests.mkdir(parents=True,exist_ok=True)
    for trader in traders:
        path = quests/(str(trader['npc_id'])+'.pl')
        adapter = ('sub EVENT_SAY { plugin::market_hail($client, $npc, $text); }\n'+
            ('sub EVENT_SPAWN { quest::settimer("market", 75 + int(rand(46))); }\n'
             'sub EVENT_TIMER { if ($timer eq "market") { plugin::market_pulse($entity_list); '
             'quest::settimer("market", 75 + int(rand(46))); } }\n' if trader['npc_id']==999500 else '')+
            'sub EVENT_ITEM { $npc->ReturnHandinItems($client); }\n')
        if path.exists() and (not refresh or path.read_text() != adapter):
            raise ValueError('Quest file collision: '+str(path))
        if not path.exists(): path.write_text(adapter)
    print(json.dumps({'items':len(catalog['items']),'merchants':len(merchants),'traders':len(traders),'status':'generated_not_applied'}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--refresh',action='store_true')
    args=p.parse_args()
    generate(args.output,args.refresh)
