"""Stage collection/pairing helpers; the maintained analyzer is never overwritten."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
collect=(ROOT/'docs/releases/wpm-melee-20261018/collect_native.py').read_text().replace('/tmp/nightcap-balance-wpm-20261018','/tmp/nightcap-balance-thj-parity-20261018').replace('/tmp/wpm-native-results.tar.gz','/tmp/thj-parity-native-results.tar.gz')
(ROOT.parent/'thj-parity-native-input/collect_native.py').write_text(collect)
verify=(ROOT/'docs/releases/wpm-melee-20261018/verify_native_pairing.py').read_text().replace('/tmp/nightcap-wpm-pet-v1','/tmp/nightcap-thj-parity-v1').replace('/tmp/nightcap-balance-wpm-20261018','/tmp/nightcap-balance-thj-parity-20261018')
(ROOT.parent/'thj-parity-native-input/verify_native_pairing.py').write_text(verify)
