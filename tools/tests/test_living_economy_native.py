import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_gameplay_policies import ROOT, ZONE, function


class NativeMarket(unittest.TestCase):
    def test_transaction_failures_and_sql(self):
        body = function((ZONE/'living_economy.cpp').read_text(), 'Result Trade(')
        fixture = (Path(__file__).parent/'living_economy_fixture.cpp').read_text()
        with tempfile.TemporaryDirectory(prefix='nightcap-market-native-') as tmp:
            out = Path(tmp)
            (out/'test.cpp').write_text(fixture.replace('// ACTUAL_TRADE', body))
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
            self.assertEqual(build.returncode,0,(out/'build.log').read_text())
            run = subprocess.run([str(out/'test.exe')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            traces = {side.lower():[line[len(side)+1:] for line in run.stdout.splitlines() if line.startswith(side+':')]
                      for side in ('BUY','SELL')}
            if os.environ.get('NIGHTCAP_TEST_EVIDENCE'):
                target=Path(os.environ['NIGHTCAP_TEST_EVIDENCE']);target.mkdir(parents=True,exist_ok=True)
                (target/'market-sql.json').write_text(json.dumps(traces,indent=2)+'\n')
            self.assertEqual(len(traces['buy']),12)

    def test_native_integration_contract(self):
        handler=function((ZONE/'client_packet.cpp').read_text(),'void Client::Handle_OP_ShopPlayerBuy(')
        self.assertLess(handler.index('BuyMarketFind('),handler.index('TakeMoneyFromPP('))
        self.assertLess(handler.index('GetMerchantSessionEntityID() != mp->npcid'),handler.index('BuyMarketFind('))
        source=(ZONE/'client_living_economy.cpp').read_text()
        allocate=function(source,'void Client::SendMarketFind(')
        self.assertIn('entry.slot + 1',allocate)
        self.assertIn('slot > limit',allocate)
        buy=function(source,'bool Client::BuyMarketFind(')
        self.assertIn('GetMerchantSessionEntityID() != npc_entity_id',buy)
        self.assertLess(buy.index('entry.slot == slot'),buy.index('CompleteMarketTrade('))
        close=function((ZONE/'client.cpp').read_text(),'void Client::SendMerchantEnd(')
        self.assertIn('m_market_slot = 0;',close)
        self.assertIn('m_market_quote = {};',close)
        complete=function(source,'bool Client::CompleteMarketTrade(')
        self.assertIn('RecalcWeight();',complete)
        self.assertLess(complete.index('NightcapMarket::Trade('),complete.index('m_pp.platinum = after'))
        self.assertIn('m_pet_armor_transfer_valid = false;',complete)
        self.assertIn('client_data_loaded = false;',complete)
        self.assertIn('CheckLoreConflict(',complete)
        self.assertLess(complete.index('NightcapMarket::ReadOffer('),complete.index('NightcapMarket::Trade('))


if __name__ == '__main__': unittest.main()
