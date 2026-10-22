"""Read-only production quest-hand-in inventory; retains no player data or secrets."""
import argparse
import json
import subprocess
from pathlib import Path

REMOTE = r'''
import datetime, hashlib, json, pathlib, re, subprocess
root = pathlib.Path('/opt/nightcap/deploy/production/data/server')
out = {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'files': {}, 'direct_checks': []}
direct_ids = set()
for relative in ('quests/lua_modules/items.lua', 'quests/southkarana/Shakrn_Meadowgreen.lua', 'plugins/check_handin.pl', 'plugins/globals.pl'):
    data = (root / relative).read_bytes()
    out['files'][relative] = {'sha256': hashlib.sha256(data).hexdigest(), 'text': data.decode()}
counts = {'lua_trade': 0, 'perl_trade': 0, 'lua_helper': 0, 'perl_helper': 0}
for p in sorted((root / 'quests').rglob('*')):
    if p.suffix not in ('.lua', '.pl') or 'plugins' in p.parts or 'lua_modules' in p.parts: continue
    s = p.read_text(errors='replace')
    trade = 'function event_trade' if p.suffix == '.lua' else 'sub EVENT_ITEM'
    if trade not in s: continue
    language = 'lua' if p.suffix == '.lua' else 'perl'
    counts[language + '_trade'] += 1
    helper = r'check_turn_in|CheckHandin' if language == 'lua' else r'check_handin|takeItems|givenItems|CheckHandin'
    if re.search(helper, s): counts[language + '_helper'] += 1
    # Retain possible bypasses for review, including checks alongside a helper.
    pattern = r'(?:trade.*GetID|\$item[1-4]\s*(?:==|eq)|\$itemcount\{)'
    hits = [{'line': n, 'text': line.strip()} for n, line in enumerate(s.splitlines(), 1) if re.search(pattern, line)]
    if hits:
        out['direct_checks'].append({'path': str(p.relative_to(root)), 'hits': hits,
                                    'lua_sibling': p.with_suffix('.lua').is_file() if p.suffix == '.pl' else False})
        data = p.read_bytes()
        try:
            text, encoding = data.decode('utf-8'), 'utf-8'
        except UnicodeDecodeError:
            text, encoding = data.decode('latin-1'), 'latin-1'
        out['files'][str(p.relative_to(root))] = {'sha256': hashlib.sha256(data).hexdigest(), 'text': text, 'encoding': encoding}
        for h in hits:
            direct_ids.update(int(x) for x in re.findall(r'\$itemcount\{(\d+)\}|\$item[1-4]\s*(?:==|eq)\s*["\']?(\d+)',h['text']) for x in x if x)
out['counts'] = counts
sql = 'SELECT id,Name FROM items WHERE id IN (13737,213737,413737,613737,10032,210032,410032,610032,4178); SELECT id,name FROM npc_types WHERE name LIKE "Shakrn%";'
p = subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','peq'], cwd='/opt/nightcap/deploy/production', input='START TRANSACTION READ ONLY; '+sql+' COMMIT;', text=True, capture_output=True, check=True)
out['content'] = p.stdout
sql = 'SELECT b.id,b.Name,v.id AS variant_id,v.Name AS variant_name FROM items b JOIN items v ON v.id IN (b.id+200000,b.id+400000,b.id+600000) WHERE b.id IN ('+','.join(map(str,sorted(direct_ids)))+') ORDER BY b.id,v.id;'
p = subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','peq'], cwd='/opt/nightcap/deploy/production', input='START TRANSACTION READ ONLY; '+sql+' COMMIT;', text=True, capture_output=True, check=True)
out['direct_variants'] = p.stdout
sql = 'SELECT b.id,b.Name,v.id AS variant_id,v.Name AS variant_name FROM items b JOIN items v ON v.id=b.id+200000 WHERE b.id>0 AND b.id<200000 AND LENGTH(b.Name)>52 ORDER BY b.id LIMIT 12;'
p = subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','peq'], cwd='/opt/nightcap/deploy/production', input='START TRANSACTION READ ONLY; '+sql+' COMMIT;', text=True, capture_output=True, check=True)
out['long_name_examples'] = p.stdout
print(json.dumps(out))
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    command = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes', 'ubuntu@135.148.47.202', 'sudo -n python3 -']
    result = subprocess.run(command, input=REMOTE, text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    data = json.loads(result.stdout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'counts': data['counts'], 'direct_check_files': len(data['direct_checks']), 'content': data['content']}))

if __name__ == '__main__':
    main()
