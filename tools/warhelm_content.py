"""Authored level-50 Ashen Compact population; pure compiler, no live writes."""
from copy import deepcopy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/quests/warhelm'
ZONE=113
KEEPER=998860
AUGMENT=961020
COMBAT=set(range(998861,998867))|{998876}
SERVICES={KEEPER,999240,*range(998867,998875)}
ARRIVAL=(1281,351,-126.125,0)
# Explicit Classic West Commonlands host. Native map probe is required before activation.
ENTRANCE=(556, -1140, -40.28125, 0)
BOSSES=[(998861,'Herald_of_the_Iron_Oath',50,200000,450,1100,23604),
        (998862,'Marshal_Kharzug',51,275000,500,1250,23678),
        (998863,'General_Vhalek',52,350000,575,1400,23641),
        (998864,'Echo_of_Endless_War',53,420000,650,1550,23590)]
TRASH=[23602,23603,23605,23610,23617,23625,23638,23611,23670,23680,
       23616,23620,23622,23629,23630,23615,23645,23643,23644,23658,23669]
PROTECTED='14,1^15,1^16,1^17,1^19,1^20,1^24,1^25,1^35,1'

def access_policy():
    era=json.loads((ROOT/'era.json').read_text())
    assert 'config/warhelm-access.json' in era['additional_zone_exception_policies']
    p=json.loads((ROOT/'config/warhelm-access.json').read_text())
    assert (p['zone_id'],p['short_name'],p['version'],p['source_expansion'])==(113,'kael',0,2)
    assert era['expansion']==0 and era['max_level']==50
    assert p['min_level']==50 and p['bypass_expansion_check']==1 and p['public_exit_zone']==21
    assert not p['stock_spawn_flag_enabled'] and not p['campaign_enabled_on_install']
    assert p['stock_spawn_flag']=='nightcap_kael_stock_disabled'
    return p

def compile_rows():
    access_policy()
    # Import late to allow dungeon_catalog to append this dungeon without cycles.
    from dungeon_catalog import base_item, existing_items
    s=json.loads((OUT/'local-content.json').read_text())
    source={p['id']:p for p in s['spawn2']}
    rows={t:[] for t in ('npc_types','spawngroup','spawnentry','spawn2',
                         'nightcap_dungeon_spawns','items','tasks','task_activities','nightcap_waypoints')}
    template=s['templates']
    def npc(id,name,**values):
        n=dict(template['npc_types'],id=id,name=name,lastname='',race=49,gender=2,size=10,
               level=50,hp=12000,mana=0,bodytype=4,AC=180,ATK=150,
               mindmg=35,maxdmg=95,attack_count=1,attack_delay=30,
               hp_regen_rate=0,hp_regen_per_second=0,npc_spells_id=0,npc_spells_effects_id=0,
               merchant_id=0,loottable_id=0,npc_faction_id=0,skip_global_loot=1,
               special_abilities='',aggroradius=35,assistradius=25,always_aggro=1,
               MR=45,FR=50,CR=50,PR=45,DR=45,Corrup=0,PhR=0,slow_mitigation=0,
               spellscale=100,healscale=100,exp_mod=100,version=0,exclude=1)
        n.update(values);rows['npc_types'].append(n)
        rows['spawngroup'].append(dict(template['spawngroup'],id=id,name='nightcap_ashen_'+str(id)))
        rows['spawnentry'].append(dict(template['spawnentry'],spawngroupID=id,npcID=id,chance=100,
            min_expansion=0,max_expansion=-1,content_flags=None,content_flags_disabled=None))
    def spawn(id,anchor=None,pose=None,public=False,zone='kael'):
        if pose is None:
            p=source[anchor];pose=(p['x'],p['y'],p['z'],p['heading'])
        sid=9230000+len(rows['nightcap_dungeon_spawns'])
        x,y,z,h=pose
        rows['nightcap_dungeon_spawns'].append(dict(zone_id=113,spawn_id=sid,group_id=id,npc_id=id,
                                                  x=x,y=y,z=z,heading=h,respawn=900,grid_id=0))
        if public:
            rows['spawn2'].append(dict(template['spawn2'],id=sid,zone=zone,version=0,spawngroupID=id,
                x=x,y=y,z=z,heading=h,pathgrid=0,respawntime=300,variance=0,_condition=0,cond_value=0,
                min_expansion=0,max_expansion=-1,content_flags=None,content_flags_disabled=None))
        return sid
    for id,name,level,hp,low,high,anchor in BOSSES:
        npc(id,name,level=level,hp=hp,mindmg=low,maxdmg=high,AC=200+(level-50)*10,
            ATK=300+(level-50)*25,attack_count=2,attack_delay=20,
            spellscale=1500 if id==998864 else 1200 if id==998863 else 100,
            special_abilities='5,1,5' if id==998864 else '')
        spawn(id,anchor)
    npc(998865,'an_iron_oath_warrior',level=48,hp=28000,mindmg=125,maxdmg=320)
    npc(998866,'an_ashen_soulbinder',level=46,hp=22000,mindmg=100,maxdmg=270,race=6,size=6,bodytype=1)
    for i,anchor in enumerate(TRASH):spawn(998865 if i%3 else 998866,anchor)
    npc(KEEPER,'Instance_Keeper',lastname='kael',race=108,bodytype=1,size=3,
        hp=50000,always_aggro=0,aggroradius=0,assistradius=0,special_abilities=PROTECTED)
    spawn(KEEPER,pose=(1281,331,-126.125,128),public=True)
    # Public host shares the exact Keeper identity; no random or unbound legacy destination.
    rows['spawn2'].append(dict(rows['spawn2'][-1],id=9230099,zone='commons',
                             x=ENTRANCE[0],y=ENTRANCE[1],z=ENTRANCE[2],heading=ENTRANCE[3]))
    # Waypoint recall lands in the empty public foyer; entering a run still uses the Keeper.
    spawn(999240,pose=ARRIVAL,public=True)
    rows['nightcap_waypoints'].append(dict(zone='kael',zone_id=113,x=ARRIVAL[0],y=ARRIVAL[1],z=ARRIVAL[2],heading=0,is_dungeon=1))
    def pose(anchor):
        p=source[anchor];return (p['x'],p['y'],p['z'],p['heading'])
    service_poses=[(998867,'Soulbinder_Veyra',pose(23606)),
        (998868,'Standard_of_Conquest',pose(23608)),(998869,'Standard_of_Dread',pose(23607)),
        (998870,'Standard_of_Dominion',pose(23614)),
        (998871,'Knight_of_Hunger',pose(23612)),(998872,'Knight_of_Ruin',pose(23619)),
        (998873,'Knight_of_Defiance',pose(23618)),(998874,'War_Altar_of_Rallos_Zek',pose(23663))]
    for id,name,pose in service_poses:
        npc(id,name,race=1 if id==998867 else 49 if 998871<=id<=998873 else 108,
            bodytype=1,size=6 if id==998867 else 8 if 998871<=id<=998873 else 3,
            gender=1 if id==998867 else 2,hp=10000,always_aggro=0,aggroradius=0,assistradius=0,
            special_abilities=PROTECTED)
        spawn(id,pose=pose)
    npc(998875,'Veyras_Soul_Binding',level=50,race=1,gender=1,bodytype=1,hp=10000,
        mindmg=0,maxdmg=0,attack_count=0,always_aggro=0,aggroradius=0,assistradius=0,
        special_abilities='',exp_mod=0)
    npc(998876,'an_unbound_war_soul',level=46,hp=30000,mindmg=175,maxdmg=400,exp_mod=0)
    # Match the existing level-50 hunt family budget, changing its identity/stat pair only.
    for tier,(hp,heroic,ac) in enumerate(((60,5,2),(87,6,3),(114,8,5),(144,10,6))):
        name='Cinder of the Ashen Compact'+('', ' (Polished)',' (Exalted)',' (Ascension)')[tier]
        item=base_item(AUGMENT+tier,name)
        item.update(itemtype=54,slots=921732,augtype=2097152,reqlevel=50,reclevel=50,
                    weight=0,nopet=1,nodrop=0,magic=1,hp=hp,mana=hp,heroic_sta=heroic,heroic_int=heroic,ac=ac)
        rows['items'].append(item)
    templates={(r['design'],r['quality']):r['values'] for r in existing_items() if r['source']=='completion' and r['band']==50}
    for i,(design,name) in enumerate(((18,'Iron Oath Gorget'),(7,'Kharzug\'s War Mantle'),(8,'Vhalek\'s Soulcleaver'))):
        item=deepcopy(templates[design,'Polished'])
        item.update(id=961030+i,Name=name,lore=name,reqlevel=50,reclevel=50,magic=1)
        rows['items'].append(item)
    rows['tasks'].append(dict(id=9801,type=2,duration=0,title='The Ashen Compact',
        description='Drazhul challenges a level-50 Shadow Knight to master the stolen war-fire of Kael. Accept before creating a run at the nearby Keeper in West Commonlands. Earn personal credit while alive and nearby. Completed duties survive resets; Drazhul or a war-rite service restores this journal.',
        reward_text='Warhelm of the Ashen Compact - claim once from Drazhul.',repeatable=0,enabled=1))
    objectives=[(0,5,'Enter your Ashen Compact expedition'),(1,2,'Defeat the Herald of the Iron Oath'),
        (2,4,'Claim the Standard of Conquest'),(2,4,'Claim the Standard of Dread'),(2,4,'Claim the Standard of Dominion'),
        (3,2,"Protect Veyra's binding through three waves"),(4,2,'Defeat Marshal Kharzug'),
        (5,4,'Claim the oath of the Knight of Hunger'),(5,4,'Claim the oath of the Knight of Ruin'),(5,4,'Claim the oath of the Knight of Defiance'),
        (6,2,'Defeat General Vhalek'),(7,2,'Defeat the Echo of Endless War'),
        (8,4,'Temper the Warhelm at the War Altar'),(9,4,'Return to Drazhul and claim your helm')]
    for i,(step,kind,description) in enumerate(objectives):
        rows['task_activities'].append(dict(taskid=9801,activityid=i,step=step,activitytype=kind,
            target_name=description,description_override=description,goalcount=1,zones='21' if i==13 else '113',
            goalmethod=2,req_activity_id=-1))
    for mode in range(2):
        task=9744+mode
        rows['tasks'].append(dict(id=task,type=2,duration=43200,title='Kael - '+('Grind','Raid')[mode],
            description='Receive personal credit for all four named enemies.',reward_text='Claim your dungeon reward from the Instance Keeper.',repeatable=1,enabled=1))
        for i,b in enumerate(BOSSES):
            rows['task_activities'].append(dict(taskid=task,activityid=i,step=0,activitytype=2,target_name=b[1].replace('_',' '),
                description_override='Defeat '+b[1].replace('_',' '),goalcount=1,zones='113',goalmethod=2,req_activity_id=-1))
        rows['task_activities'].append(dict(taskid=task,activityid=4,step=1,activitytype=2,target_name='Dungeon Journal',
            description_override='Full dungeon clear: earn all four boss credits.',goalcount=1,zones='113',goalmethod=2,req_activity_id=-1))
    npc(998877,'Drazhul_Blackmantle',race=6,gender=0,bodytype=1,size=6,
        hp=50000,always_aggro=0,aggroradius=0,assistradius=0,special_abilities=PROTECTED)
    rows['spawn2'].append(dict(rows['spawn2'][0],id=9230098,zone='commons',spawngroupID=998877,
        x=ENTRANCE[0],y=ENTRANCE[1]-10,z=ENTRANCE[2],heading=ENTRANCE[3]))
    helm=base_item(990510,'Warhelm of the Ashen Compact')
    helm.update(lore='War-fire yields to the knight who commands it.',classes=16,races=4095,slots=4,
        material=91,color=0,ac=18,hp=25,mana=25,asta=5,aint=7,mr=10,fr=5,cr=5,icon=746,
        itemtype=10,magic=1,reqlevel=0,reclevel=0)
    rows['items'].append(helm)
    # Pinned authored positions derived from native Kael collision-floor probes.
    poses=json.loads((OUT/'placements.json').read_text())['points']
    for row in rows['nightcap_dungeon_spawns']:
        row.update(poses[str(row['spawn_id'])])
    for row in rows['spawn2']:
        if row['zone']=='kael':row.update(poses[str(row['id'])])
    waypoint=next(r for r in rows['nightcap_dungeon_spawns'] if r['npc_id']==999240)
    rows['nightcap_waypoints'][0].update({k:waypoint[k] for k in ('x','y','z')})
    return rows

def dungeon():
    rows=compile_rows();points=rows['nightcap_dungeon_spawns']
    return dict(index=22,zone='kael',zone_id=113,keeper_id=KEEPER,band=50,band_index=3,
        task_grind=9744,task_raid=9745,bosses=[dict(boss_id=i+1,npc_id=n['id'],
        name=n['name'].replace('_',' '),spawn_id=points[i]['spawn_id'],
        spawn=dict(id=points[i]['spawn_id'],managed_private=True),is_final=i==3)
        for i,n in enumerate(rows['npc_types'][:4])])

if __name__=='__main__':
    rows=compile_rows()
    (OUT/'install-rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:len(v) for k,v in rows.items()}))
