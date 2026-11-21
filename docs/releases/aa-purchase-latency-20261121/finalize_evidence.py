"""Compact complete check output and retain the exact compressed originals."""
from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


def main():
    for name in ('skill-check', 'wiki-refresh'):
        path = HERE / (name + '.json')
        raw = path.read_bytes()
        value = json.loads(raw)
        packed = path.with_suffix('.json.gz')
        assert not packed.exists()
        packed.write_bytes(gzip.compress(raw, mtime=0))
        result = {'full_output': packed.name, 'full_output_sha256': hashlib.sha256(raw).hexdigest()}
        if name == 'skill-check':
            rows = value['topics']['multiclass']
            result.update(entries=len(rows),
                          candidate=[r for r in rows if 'aa-purchase-latency' in r['path']],
                          unrelated_drift=[r for r in rows if r['state'] != 'unchanged'])
        else:
            result.update(result=value['result'], source_ref=value['source_ref'],
                          changed_source_count=len(value['changed_sources']),
                          note='Full historical drift retained, unrelated review ledger not advanced.')
        save(path, result)


if __name__ == '__main__':
    main()
