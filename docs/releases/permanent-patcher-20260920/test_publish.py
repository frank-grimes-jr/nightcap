import contextlib,hashlib,io,json,os,shutil,sys,tempfile
from pathlib import Path
base=Path(__file__).parent
source=(base/'publish.py').read_text()
report=[]
# Interruption during every backup/asset copy, or immediately after every rename.
for operation in ('copy','rename'):
 for fault in range(1,34 if operation=='rename' else 31):
  with tempfile.TemporaryDirectory(dir=base) as d:
   root=Path(d);stage=root/'releases/patcher-2026092006';public=root/'deploy/production/data/public';stage.mkdir(parents=True);public.mkdir(parents=True)
   checks=json.loads((base/'publication-files.json').read_text())
   for name in checks:
    p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);data=('new-'+name).encode();p.write_bytes(data);checks[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
   (stage/'publication-files.json').write_text(json.dumps(checks))
   for name in ('channel.json','guide.html','nightcap-friends.zip'):(public/name).write_bytes(b'old')
   old=hashlib.sha256(b'old').hexdigest()
   test=source.replace("base=Path('/opt/nightcap')",'base=Path('+repr(str(root))+')').replace("OLD_GAME='fdbf8486da06342593eca7efebb78916e50c0923a26a7993009d5a715e17f5cc'",'OLD_GAME='+repr(old))
   line=next(x for x in test.splitlines() if x.startswith('OLD_FILES='));test=test.replace(line,'OLD_FILES='+repr({n:old for n in ('channel.json','guide.html','nightcap-friends.zip')}))
   replace=os.replace;copy=shutil.copyfile;calls=[0];hit=[False]
   def interrupted_replace(a,b):
    replace(a,b)
    if operation=='rename':
     calls[0]+=1
     if calls[0]==fault:hit[0]=True;raise OSError('simulated loss after rename')
   def interrupted_copy(a,b,*args,**kwargs):
    if operation=='copy':
     calls[0]+=1
     if calls[0]==fault:Path(b).write_bytes(b'partial');hit[0]=True;raise OSError('simulated copy loss')
    return copy(a,b,*args,**kwargs)
   argv=sys.argv;sys.argv=['publish.py','publish'];os.replace=interrupted_replace;shutil.copyfile=interrupted_copy
   try:
    try:
     with contextlib.redirect_stdout(io.StringIO()):exec(compile(test,'publisher-test','exec'),{})
    except OSError:pass
   finally:os.replace=replace;shutil.copyfile=copy
   # If a new ZIP is visible, its launcher channel must already exist.
   if (public/'nightcap-friends.zip').read_bytes()!=b'old':assert (public/'launcher-channel.json').is_file()
   with contextlib.redirect_stdout(io.StringIO()):exec(compile(test,'publisher-resume','exec'),{})
   sys.argv=argv
   for name in ('channel.json','guide.html','nightcap-friends.zip'):assert (stage/'previous-public'/name).read_bytes()==b'old'
   report.append({'operation':operation,'boundary':fault,'fault_injected':hit[0],'resume':'pass','backup':'preserved'})
(base/'publication-recovery-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'cases':len(report),'faults_injected':sum(r['fault_injected'] for r in report),'result':'pass'}))
