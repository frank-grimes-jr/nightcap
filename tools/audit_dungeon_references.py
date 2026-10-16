"""Read-only reserved item-reference counts; never read/copy player records."""
import json
from pathlib import Path
from dungeon_migration import ITEM_REFERENCES
from package_dungeons import sql
ROOT=Path(__file__).resolve().parents[1]
columns={tuple(line.split('\t')) for line in sql("SELECT table_name,LOWER(column_name) FROM information_schema.columns WHERE table_schema='peq';").splitlines()}
present=[(table,column) for table,names in sorted(ITEM_REFERENCES.items()) for column in names if (table,column) in columns]
statements=[f'SELECT COUNT(*) FROM peq.`{table}` WHERE `{column}` BETWEEN 960000 AND 960329;' for table,column in present]
counts=list(map(int,sql('\n'.join(statements)).splitlines()))
assert len(counts)==len(present)
report=dict(scope='Read-only local aggregate counts; no player records or production capture',
            reserved_range=[960000,960329],counts={table+'.'+column:count for (table,column),count in zip(present,counts)},
            optional_columns_absent=[table+'.'+column for table,names in sorted(ITEM_REFERENCES.items()) for column in names if (table,column) not in columns])
assert not any(counts),'Reserved reference occupied; do not install this catalog'
(ROOT/'docs/dungeons/reference-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'All {len(counts)} present item-reference columns are clear in local data.')
