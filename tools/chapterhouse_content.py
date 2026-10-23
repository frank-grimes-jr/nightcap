"""Authored level-50 Chapterhouse population; pure compiler, no live writes."""
from copy import deepcopy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/quests/camil-chapterhouse'
ZONE=760
KEEPER=998820
AUGMENT=961000
COMBAT=set(range(998821,998827))|{998836}
SERVICES={KEEPER,999240,*range(998827,998835)}
ARRIVAL=(-119,-197,2,0)
# Explicit Classic West Commonlands host. Native map probe is required before activation.
ENTRANCE=(576, -1150, -40.28, 0)
BOSSES=[(998821,'Vicar_Sered_the_Bellkeeper',50,250000,450,1100,152467),
        (998822,'Warden_Halvyr',51,325000,500,1250,152497),
        (998823,'Sir_Vaelen_Ashen_Dawn',52,400000,575,1400,152571),
        (998824,'The_Unbroken_Shadow',53,480000,650,1550,152904)]
TRASH=[152453,152454,152455,152456,152461,152466,152476,152478,
       152480,152484,152495,152525,152528,152543,152551,152559,
       152564,152574,152592,152607,152654]
PROTECTED='14,1^15,1^16,1^17,1^19,1^20,1^24,1^25,1^35,1'

def access_policy():
    era=json.loads((ROOT/'era.json').read_text())
    assert era['zone_exception_policy']=='config/chapterhouse-access.json'
    p=json.loads((ROOT/era['zone_exception_policy']).read_text())
    assert (p['zone_id'],p['short_name'],p['version'],p['source_expansion'])==(760,'chapterhouse',0,19)
    assert era['expansion']==0 and era['max_level']==50
    assert p['min_level']==50 and p['bypass_expansion_check']==1 and p['public_exit_zone']==21
    assert not p['stock_spawn_flag_enabled'] and not p['campaign_enabled_on_install']
    assert p['stock_spawn_flag']=='nightcap_chapterhouse_stock_disabled'
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
        n=dict(template['npc_types'],id=id,name=name,lastname='',race=60,gender=2,size=6,
               level=50,hp=12000,mana=0,bodytype=3,AC=180,ATK=150,
               mindmg=35,maxdmg=95,attack_count=1,attack_delay=30,
               hp_regen_rate=0,hp_regen_per_second=0,npc_spells_id=0,npc_spells_effects_id=0,
               merchant_id=0,loottable_id=0,npc_faction_id=0,skip_global_loot=1,
               special_abilities='',aggroradius=35,assistradius=25,always_aggro=1,
               MR=60,FR=50,CR=50,PR=50,DR=70,Corrup=0,PhR=0,slow_mitigation=0,
               spellscale=100,healscale=100,exp_mod=100,version=0,exclude=1)
        n.update(values);rows['npc_types'].append(n)
        rows['spawngroup'].append(dict(template['spawngroup'],id=id,name='nightcap_vigil_'+str(id)))
        rows['spawnentry'].append(dict(template['spawnentry'],spawngroupID=id,npcID=id,chance=100,
            min_expansion=0,max_expansion=-1,content_flags=None,content_flags_disabled=None))
    def spawn(id,anchor=None,pose=None,public=False,zone='chapterhouse'):
        if pose is None:
            p=source[anchor];pose=(p['x'],p['y'],-.55,p['heading'])
            if anchor==152476:pose=(109.875,-225.125,-.55,p['heading'])
            if anchor==152528:pose=(64,94,-.55,p['heading'])
        sid=9220000+len(rows['nightcap_dungeon_spawns'])
        x,y,z,h=pose
        rows['nightcap_dungeon_spawns'].append(dict(zone_id=760,spawn_id=sid,group_id=id,npc_id=id,
                                                  x=x,y=y,z=z,heading=h,respawn=900,grid_id=0))
        if public:
            rows['spawn2'].append(dict(template['spawn2'],id=sid,zone=zone,version=0,spawngroupID=id,
                x=x,y=y,z=z,heading=h,pathgrid=0,respawntime=300,variance=0,_condition=0,cond_value=0,
                min_expansion=0,max_expansion=-1,content_flags=None,content_flags_disabled=None))
        return sid
    for id,name,level,hp,low,high,anchor in BOSSES:
        npc(id,name,level=level,hp=hp,mindmg=low,maxdmg=high,AC=200+(level-50)*10,
            ATK=300+(level-50)*25,attack_count=2,attack_delay=20,
            spellscale=1500 if id==998824 else 1200 if id==998823 else 100,
            special_abilities='5,1,5' if id==998824 else '')
        spawn(id,anchor)
    npc(998825,'a_bound_watchman',level=48,hp=28000,mindmg=125,maxdmg=320)
    npc(998826,'a_restless_acolyte',level=46,hp=22000,mindmg=100,maxdmg=270,race=85)
    for i,anchor in enumerate(TRASH):spawn(998825 if i%3 else 998826,anchor)
    npc(KEEPER,'Instance_Keeper',lastname='chapterhouse',race=108,bodytype=1,size=3,
        hp=50000,always_aggro=0,aggroradius=0,assistradius=0,special_abilities=PROTECTED)
    spawn(KEEPER,pose=(-86,-155,-.5,128),public=True)
    # Public host shares the exact Keeper identity; no random or unbound legacy destination.
    rows['spawn2'].append(dict(rows['spawn2'][-1],id=9220099,zone='commons',
                             x=ENTRANCE[0],y=ENTRANCE[1],z=ENTRANCE[2],heading=ENTRANCE[3]))
    # Waypoint recall lands in the empty public foyer; entering a run still uses the Keeper.
    spawn(999240,pose=(-119,-197,2,0),public=True)
    rows['nightcap_waypoints'].append(dict(zone='chapterhouse',zone_id=760,x=-119,y=-197,z=2,heading=0,is_dungeon=1))
    service_poses=[(998827,'Sister_Elowen',(-52.5,-79.25,-.5,0)),
        (998828,'First_Memorial',(-51,-248,-.5,0)),(998829,'Second_Memorial',(20.25,-245,-.5,0)),
        (998830,'Third_Memorial',(27.625,-22.875,-.5,0)),
        (998831,'Knight_of_Mercy',(-57,181.875,-.5,0)),(998832,'Knight_of_Courage',(91.875,136.875,-.5,0)),
        (998833,'Knight_of_Resolve',(36.625,219.75,-.5,0)),(998834,'Altar_of_the_First_Dawn',(-122,275,2,0))]
    for id,name,pose in service_poses:
        npc(id,name,race=1 if id==998827 else 108,bodytype=1,size=6 if id==998827 else 3,
            gender=1 if id==998827 else 2,hp=10000,always_aggro=0,aggroradius=0,assistradius=0,
            special_abilities=PROTECTED)
        spawn(id,pose=pose)
    npc(998835,'Elowens_Prayer',level=50,race=1,gender=1,bodytype=1,hp=10000,
        mindmg=0,maxdmg=0,attack_count=0,always_aggro=0,aggroradius=0,assistradius=0,
        special_abilities='',exp_mod=0)
    npc(998836,'a_vigil_shade',level=46,hp=30000,mindmg=175,maxdmg=400,exp_mod=0)
    # Match the existing level-50 hunt family budget, changing its identity/stat pair only.
    for tier,(hp,heroic,ac) in enumerate(((60,5,2),(87,6,3),(114,8,5),(144,10,6))):
        name='Ember of the First Dawn'+('', ' (Polished)',' (Exalted)',' (Ascension)')[tier]
        item=base_item(AUGMENT+tier,name)
        item.update(itemtype=54,slots=921732,augtype=2097152,reqlevel=50,reclevel=50,
                    weight=0,nopet=1,nodrop=0,magic=1,hp=hp,mana=hp,heroic_sta=heroic,heroic_wis=heroic,ac=ac)
        rows['items'].append(item)
    templates={(r['design'],r['quality']):r['values'] for r in existing_items() if r['source']=='completion' and r['band']==50}
    for i,(design,name) in enumerate(((18,'Sered\'s Memorial Chain'),(7,'Halvyr\'s Unbroken Mantle'),(8,'Vaelen\'s Last Oath'))):
        item=deepcopy(templates[design,'Polished'])
        item.update(id=961010+i,Name=name,lore=name,reqlevel=50,reclevel=50,magic=1)
        rows['items'].append(item)
    rows['tasks'].append(dict(id=9800,type=2,duration=0,title='The Vigil of the Dawn',
        description='Camil asks a level-50 Paladin to release the fallen order. Enter a Chapterhouse run through its Keeper near Befallen in West Commonlands. Earn personal credit nearby; completed duties survive resets. Recover this journal through Camil or a sanctuary service.',
        reward_text='Winged Helm of the Dawn - claim once from Camil.',repeatable=0,enabled=1))
    objectives=[(0,5,'Enter your Chapterhouse expedition'),(1,2,'Defeat Vicar Sered the Bellkeeper'),
        (2,4,'Read the First Memorial'),(2,4,'Read the Second Memorial'),(2,4,'Read the Third Memorial'),
        (3,2,'Protect Elowens prayer through three waves'),(4,2,'Defeat Warden Halvyr'),
        (5,4,'Release the Knight of Mercy'),(5,4,'Release the Knight of Courage'),(5,4,'Release the Knight of Resolve'),
        (6,2,'Defeat Sir Vaelen Ashen Dawn'),(7,2,'Defeat the Unbroken Shadow'),
        (8,4,'Reconsecrate the Altar of the First Dawn'),(9,4,'Return to Camil and claim your helm')]
    for i,(step,kind,description) in enumerate(objectives):
        rows['task_activities'].append(dict(taskid=9800,activityid=i,step=step,activitytype=kind,
            target_name=description,description_override=description,goalcount=1,zones='22' if i==13 else '760',
            goalmethod=2,req_activity_id=-1))
    for mode in range(2):
        task=9742+mode
        rows['tasks'].append(dict(id=task,type=2,duration=43200,title='Chapterhouse - '+('Grind','Raid')[mode],
            description='Receive personal credit for all four named enemies.',reward_text='Claim your dungeon reward from the Instance Keeper.',repeatable=1,enabled=1))
        for i,b in enumerate(BOSSES):
            rows['task_activities'].append(dict(taskid=task,activityid=i,step=0,activitytype=2,target_name=b[1].replace('_',' '),
                description_override='Defeat '+b[1].replace('_',' '),goalcount=1,zones='760',goalmethod=2,req_activity_id=-1))
        rows['task_activities'].append(dict(taskid=task,activityid=4,step=1,activitytype=2,target_name='Dungeon Journal',
            description_override='Full dungeon clear: earn all four boss credits.',goalcount=1,zones='760',goalmethod=2,req_activity_id=-1))
    return rows

def dungeon():
    rows=compile_rows();points=rows['nightcap_dungeon_spawns']
    return dict(index=21,zone='chapterhouse',zone_id=760,keeper_id=KEEPER,band=50,band_index=3,
        task_grind=9742,task_raid=9743,bosses=[dict(boss_id=i+1,npc_id=n['id'],
        name=n['name'].replace('_',' '),spawn_id=points[i]['spawn_id'],
        spawn=dict(id=points[i]['spawn_id'],managed_private=True),is_final=i==3)
        for i,n in enumerate(rows['npc_types'][:4])])

if __name__=='__main__':
    rows=compile_rows()
    (OUT/'install-rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:len(v) for k,v in rows.items()}))
