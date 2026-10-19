"""Retain the companion's mechanics assertions for the expanded combined matrix."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
text=(ROOT/'docs/releases/wpm-melee-20261018/analyze_native.py').read_text()
text=text.replace("len(execution['cases'])==26","len(execution['cases'])==47")
text=text.replace('26 input/output hashes','47 input/output hashes').replace("'execution_cases':26","'execution_cases':47")
text=text.replace("'stat_cases':6","'stat_cases':6,'spell_probe_cases':18")
text=text.replace('# Native WPM and pet comparison','# Combined native item/spell and WPM/pet comparison')
text=text.replace('All26 scenarios','All47 scenarios')
text=text.replace("'Bare/equipped pet comparisons retain fixed Classic support gems, with separate PoP summon cases',", "'Bare/equipped pet comparisons retain fixed Classic support gems, with separate PoP summon cases',\n            'Eighteen caster probes sample direct values/resists and landed initial-duration DoT ticks; no full casting/buff lifecycle',")
(REL/'analyze_native.py').write_text(text)
collect=(ROOT/'docs/releases/wpm-melee-20261018/collect_native.py').read_text().replace('/tmp/nightcap-balance-wpm-20261018','/tmp/nightcap-balance-thj-parity-20261018').replace('/tmp/wpm-native-results.tar.gz','/tmp/thj-parity-native-results.tar.gz')
(ROOT.parent/'thj-parity-native-input/collect_native.py').write_text(collect)
verify=(ROOT/'docs/releases/wpm-melee-20261018/verify_native_pairing.py').read_text().replace('/tmp/nightcap-wpm-pet-v1','/tmp/nightcap-thj-parity-v1').replace('/tmp/nightcap-balance-wpm-20261018','/tmp/nightcap-balance-thj-parity-20261018')
(ROOT.parent/'thj-parity-native-input/verify_native_pairing.py').write_text(verify)
