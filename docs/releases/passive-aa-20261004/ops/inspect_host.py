"""Read-only OVH release baseline; never shadow Python's inspect module."""
import base64,hashlib,json,shutil,subprocess
from pathlib import Path
r=Path('/opt/nightcap/deploy/production')
def out(*args):return subprocess.check_output(args,cwd=r,text=True)
result={'services':{},'public':{}}
for service in ('db','game','gateway','web','tunnel'):
    cid=out('docker','compose','ps','-q',service).strip()
    d=json.loads(out('docker','inspect',cid))[0];state=d['State']
    result['services'][service]={'id':cid,'image_id':d['Image'],'started_at':state['StartedAt'],'restarts':d['RestartCount'],'running':state['Running'],'health':state.get('Health',{}).get('Status'),'oom_killed':state.get('OOMKilled',False)}
    if service=='game':
        result['image']=d['Config']['Image'];result['direct_ports']=d['HostConfig'].get('PortBindings')
        code="from pathlib import Path;import hashlib,json;r=Path('/opt/nightcap');print(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ['bin/world','bin/zone','bin/loginserver','bin/ucs','bin/shared_memory','start.py','configure.py','accounts.py']}))"
        result['hashes']=json.loads(out('docker','exec',cid,'python3','-c',code))
        start=out('docker','exec',cid,'cat','/opt/nightcap/start.py')
        assert "subprocess.run([str(BIN/'shared_memory')], check=True)" in start
        assert 'restarting the complete runtime' in start
for name in ('channel.json','launcher-channel.json','nightcap-friends.zip','guide.html'):
    raw=(r/'data/public'/name).read_bytes();result['public'][name]={'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}
    if name=='channel.json':result['public'][name]['signed']=json.loads(base64.b64decode(json.loads(raw)['manifest']))
q="SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ('AA:PassiveExpPercent','Character:AAExpMinLevel','AA:ExpPerPoint','Character:AAExpMultiplier','Character:ExpMultiplier','Items:FreeTrade','AA:NormalizedAAEnabled','AA:ModernAAScalingEnabled','AA:UnusedAAPointCap','AA:MaxAAEXPPerKill') ORDER BY ruleset_id,rule_name; SELECT varname,value FROM variables WHERE varname='RuleSet';"
result['rules']=out('docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq','-e',q).splitlines()
result['disk_free_bytes']=shutil.disk_usage(r).free
print(json.dumps(result,indent=2))
