"""Prepare local publication helpers from the reviewed preceding publisher."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'docs/dungeons/hate-layout-20261029/release/wiki'

capture = (OLD/'capture_baseline.py').read_text().replace('20261028-bazaar-owner-qa-v1', '20261029-hate-layout-v1')
(HERE/'capture_baseline.py').write_text(capture)
(HERE/'verify_wiki_public.py').write_text((OLD/'verify_wiki_public.py').read_text())
publisher = (OLD/'publish_wiki.py').read_text()
publisher = publisher.replace('HERE.parents[4]', 'HERE.parents[2]').replace('work/hate-wiki', 'work/keyless-wiki')
publisher = publisher.replace('20261029-hate-layout-v1', '20261029-keyless-doors-v1').replace('wiki-hate-layout-20261029-v1', 'wiki-keyless-doors-20261029-v1')
publisher = publisher.replace("{'dungeon-modes.html', 'features.html', 'unreleased.html',\n           'recent-changes.html', 'travel.html', 'zone-hunt.html', 'search-index.json'}", "{'features.html', 'unreleased.html', 'recent-changes.html', 'travel.html',\n           'zone-hole.html', 'search-index.json'}")
publisher = publisher.replace("    assert activation['runtime_receipt'] and activation['client_receipt']", "    assert activation['runtime_receipt']")
publisher = '\n'.join(line for line in publisher.split('\n') if "activation['client_receipt" not in line)
publisher = publisher.replace("expected={activation['services_after']!r}[name]", "expected={activation['services']!r}['/nightcap-production-'+name+'-1']")
publisher = publisher.replace("assert all(row[k]==expected[k] for k in ['Id','Image','RestartCount']),'Service identity changed'", "assert row['Id']==expected['id'] and row['Image']==expected['image'] and row['RestartCount']==expected['restarts'],'Service identity changed'")
publisher = publisher.replace("assert all(row['State'][k]==expected['state'][k] for k in ['Running','StartedAt','OOMKilled']),'Service state changed'", "assert row['State']['StartedAt']==expected['start'],'Service lifetime changed'")
publisher = publisher.replace('Hate ground-level entry and retained Nightcap rewards; owner gameplay acceptance open', '194 keyless doors across 48 zones; owner gameplay acceptance open')
publisher = publisher.replace('Publish approved Hate guidance after verified server/client activation.', 'Publish approved keyless-door guidance after verified database/runtime activation.')
(HERE/'publish_wiki.py').write_text(publisher)
