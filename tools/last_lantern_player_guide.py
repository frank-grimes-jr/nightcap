"""Replace only the published journal section; preserve private access and assets."""
import argparse,base64,hashlib,html,json,re,subprocess
from pathlib import Path
from ship_last_lantern import ROOT,HERE,ART,SSH,STAGE,remote
from last_lantern_content import compile_tasks

RELEASE='20261107-last-lantern-guide-v1'
FILES=('index.html','site-assets/site.css','site-assets/moon.svg','site-assets/traders-at-dusk.png','site-assets/master-of-three.png')
PATTERN=re.compile(rb'<section\b[^>]*\bid="journal-candidate"[^>]*>.*?</section>',re.S)

def block():
    tasks={t['id']:t for t in compile_tasks()[0]};e=html.escape
    stories=[(9500,'Read the Upper Guk, Unrest and Runnyeye entrance reports. Earn your boots.'),
      (9501,'Win the field trials, then bring Tovin through an Unrest rescue memory. Earn gloves.'),
      (9502,'Recover the named accounts and let Mera compare the records. Earn your first bracer.'),
      (None,'Earn Guardian, Striker, Arcanist, Warden or Binder. One path opens the continuation and the oath charm; further paths are optional.'),
      (9508,'Recover Mera’s satchel in Lower Guk and escort her through the retreat. Earn the second bracer.'),
      (9509,'Defeat the Solusek B lieutenants and defend Oren’s furnace. Earn arms and Oathbound refits.'),
      (9510,'Hear Captain Selene’s last orders in Cazic-Thule and hold the retreat. Earn leggings.'),
      (9511,'Recover the stolen roster in The Hole and bring Mera home.'),
      (9512,'Release the bound names in Fear and defeat their pursuer. Earn head armor and Restored refits.'),
      (9513,'Break the chosen guard in Hate and save the recorded names.'),
      (9514,'Gather the survivors in Commonlands and choose a memorial inscription.'),
      (9515,'Break the bindings, defend the standard and face the Hollow Witness. Return to the campfire for the chest or robe, Complete refits and Lanternbearer title.')]
    s='<section class="candidate-quests" id="journal-candidate" aria-labelledby="journal-title">\n<div class="candidate-heading"><span class="badge">Live testing</span><h3 id="journal-title">Wayfarer’s Oath: The Last Lantern</h3><p>Mera Vell has three reports and the same name scratched out of every one. Follow the lost company through twelve chapters, from level20 to the current level50 endgame. Begin with the Ancient Chronicler’s <strong>journal</strong> dialogue in East Commonlands; your Tasks window tracks the journey.</p></div>\n<ol class="candidate-list" aria-label="Adventure Journal campaign chapters">\n'
    for identity,text in stories:
        title=tasks[identity]['title'] if identity else 'Choose your oath';level=tasks[identity]['min_level'] if identity else 35
        s+=f'<li><div class="quest-heading"><h4>{e(title)}</h4><span class="level">Level {level}</span></div><p>{e(text)}</p></li>\n'
    s+='</ol><p class="quest-reward"><strong>Your journey outfit:</strong> Earn eight useful armor pieces in legal woven, leather, chain or plate fits. Oren Lanternwright handles the earned40/46/50 refits, preserving augments and custom dye. These personal pieces cannot be traded or sold; missing receipted gear is not replaced for free. The Wayfarer’s Oath charm has five earned attunements sharing a ten-minute recovery.</p><p>The private memories preserve public zones and Keeper runs. Stay with companions, survive ordered defense waves and move from the Witness’s marked ground or stun him. Full player pathing, appearance and encounter acceptance remain open. Exit the game and choose launcher Play for signed update2026110701 and its client notes.</p><p><a href="https://wiki.nightcapgame.org/adventure-journal.html">Full chapter route, oath trials, exact armor stats and testing guidance →</a></p>\n</section>'
    return s.encode('utf-8')

def prepare():
    result=remote('from pathlib import Path\nimport base64,hashlib,json,os\np=Path("/opt/nightcap/deploy/production/data/public/player-site/current");names='+repr(FILES)+'\nprint(json.dumps({"release":os.readlink(p),"files":{n:base64.b64encode((p/n).read_bytes()).decode() for n in names},"config_sha256":hashlib.sha256(Path("/opt/nightcap/deploy/production/nginx.conf").read_bytes()).hexdigest()}))')
    assert result['release']=='20261023-aa-level-guide-v1'
    target=ART/'player-guide';target.mkdir(exist_ok=False);old={n:base64.b64decode(v) for n,v in result['files'].items()}
    text=old['index.html'];matches=list(PATTERN.finditer(text));assert len(matches)==1,'Review the published guide structure'
    match=matches[0];new=text[:match.start()]+block()+text[match.end():]
    for n,data in old.items():
        p=target/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(new if n=='index.html' else data)
    # Maintain source, while publication retains every unrelated live byte.
    source=ROOT/'index.html';raw=source.read_bytes();assert len(PATTERN.findall(raw))==1
    source.write_bytes(PATTERN.sub(lambda m:block(),raw))
    (HERE/'player-guide-section.html').write_bytes(block())
    import player_site_package as package
    package.ROOT=target;archive=ART/(RELEASE+'.tar.gz');after=package.package(archive)
    before={n:hashlib.sha256(v).hexdigest() for n,v in old.items()}
    assert {n for n in after if after[n]!=before[n]}=={'index.html'}
    proof={'status':'candidate_not_published','previous':result['release'],'release':RELEASE,'manifest':after,'before':before,'config_sha256':result['config_sha256'],'unchanged_outside_journal_sha256':hashlib.sha256(text[:match.start()]+text[match.end():]).hexdigest(),'assets_preserved':4,'source':'Exact published private-guide bytes with only its journal section replaced; unrelated main changes excluded'}
    (HERE/'player-guide-candidate.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k not in ('manifest','before')}))

def publish():
    proof=json.loads((HERE/'player-guide-candidate.json').read_text());assert json.loads((HERE/'production-verification.json').read_text())['gateway_open']
    archive=ART/(RELEASE+'.tar.gz');files=[archive,archive.with_suffix('.json'),ROOT/'deploy/production/player-site-deploy.py']
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files};ssh=SSH[:-1];upload='/home/ubuntu/last-lantern-player-guide-20261107';stage='/opt/nightcap/releases/last-lantern-player-guide-20261107'
    subprocess.run(ssh+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],*map(str,files),ssh[-1]+':'+upload+'/'],check=True,timeout=120)
    result=remote(f'''from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
base=Path('/opt/nightcap/deploy/production');upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
os.umask(0o077);stage.mkdir(mode=0o700,exist_ok=False);assert {{p.name for p in upload.iterdir()}}==set(pins)
for n,pin in pins.items():
 p=upload/n;assert not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin;shutil.copyfile(p,stage/n)
spec=importlib.util.spec_from_file_location('campaign',Path({STAGE!r})/'rollout.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.initialize()
before={{s:m.r.compact(s) for s in ('game','gateway','db','web','tunnel')}}
def guard():
 assert all(m.r.compact(s)==v for s,v in before.items()),'Service drift'
 m.r.running(m.read(Path({STAGE!r})/'evidence/activation/deployed.json')['runtime']['image_id'],m.binaries())
with (base/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 pointer=base/'data/public/player-site/current';assert pointer.is_symlink() and str(pointer.readlink())=={proof['previous']!r}
 assert {{n:hashlib.sha256((pointer/n).read_bytes()).hexdigest() for n in {FILES!r}}}=={proof['before']!r}
 config=(base/'nginx.conf').read_bytes();assert hashlib.sha256(config).hexdigest()=={proof['config_sha256']!r};(stage/'current-nginx.conf').write_bytes(config)
 staged=json.loads(subprocess.check_output(['python3',str(stage/'player-site-deploy.py'),'stage',str(stage/{archive.name!r}),str(stage/{archive.with_suffix('.json').name!r}),{RELEASE!r},{proof['config_sha256']!r},str(stage/'current-nginx.conf')],text=True,timeout=180))
 activated=json.loads(subprocess.check_output(['python3',str(stage/'player-site-deploy.py'),'activate',{RELEASE!r}],text=True,timeout=180))
 guard();assert (base/'nginx.conf').read_bytes()==config
print(json.dumps({{'result':'PASS','release':{RELEASE!r},'stage':staged,'activation':activated,'assets_preserved':4,'only_journal_section_changed':True,'services_preserved':True,'private_access_preserved':True}}))
''')
    (HERE/'player-guide-publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','publish'));globals()[p.parse_args().action]()
