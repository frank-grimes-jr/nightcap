"""Read all three rule preimages, including alternate rulesets, on either active server."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from run import HERE, PRIVATE, remote

QUERY = """SELECT ruleset_id,rule_name,rule_value FROM rule_values
WHERE rule_name IN ('Zone:LootTierEpicChance','Zone:LootTierLegendaryChance','Zone:LootTierRareChance')
ORDER BY rule_name,ruleset_id;
SELECT ruleset_id FROM rule_sets WHERE name='default';
SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='rule_values';"""
p = argparse.ArgumentParser()
p.add_argument('target', choices=('local','production'))
p.add_argument('value', type=int, choices=(100,700))
args = p.parse_args()
local = args.target == 'local'
cmd = ['docker','exec','-i','akk-stack-mariadb-1' if local else 'nightcap-production-db-1','mariadb',
       '--defaults-extra-file='+('/run/local-secrets/client.cnf' if local else '/run/secrets/db_backup_config'),'-NB','peq']
out = subprocess.check_output(cmd,input=QUERY.encode()) if local else remote(*cmd,data=QUERY.encode())
rows = out.decode().splitlines()
assert rows == ['1\tZone:LootTierEpicChance\t500',f'1\tZone:LootTierLegendaryChance\t{args.value}',
                '1\tZone:LootTierRareChance\t2000','1','InnoDB'], rows
print(json.dumps(rows))
(PRIVATE/args.target/f'rules-{args.value}.json').write_text(json.dumps(rows,indent=2)+'\n')
