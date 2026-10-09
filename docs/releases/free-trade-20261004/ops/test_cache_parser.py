"""Exercise the deployed verifier against the earlier actual native cache."""
import ast,json,subprocess
from pathlib import Path
r=Path(__file__).parent
source=(r/'rollout.py').read_text();module=ast.parse(source)
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='verify_cache')
code=ast.get_source_segment(source,fn).replace("ROOT/'data/server/shared/items'","ROOT/'shared/items'")
setup='''import hashlib,json,mmap,os,struct,subprocess
from pathlib import Path
ROOT=Path('/tmp/nightcap_free_trade_774db57034e7')
cfg=json.loads(Path('/home/eqemu/server/eqemu_config.json').read_text())['server']['database']
def policy_rows():return ['1\\ttrue']
def sql(q):
    env=dict(os.environ,MYSQL_PWD=cfg['password'])
    return subprocess.check_output(['mariadb','-h',cfg['host'],'-P',str(cfg.get('port',3306)),'-u',cfg['username'],'--batch','--raw','--skip-column-names',cfg['db'],'-e',q],env=env,text=True)
'''
p=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=setup+code+'\nprint(json.dumps(verify_cache()))',text=True,capture_output=True,check=True,timeout=90)
result=json.loads(p.stdout);assert result['items_checked']==308928 and result['fixed_payout_items']==171528
(r/'cache-parser-test.json').write_text(json.dumps(result,indent=2)+'\n');print(p.stdout)
