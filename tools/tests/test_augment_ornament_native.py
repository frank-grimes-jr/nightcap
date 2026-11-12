"""Run actual ornament classification/update methods against item boundary doubles."""
import re
import unittest

import test_free_trade as native


class AugmentOrnamentTests(unittest.TestCase):
    def test_actual_ornament_methods(self):
        source = (native.CODE / 'common/item_instance.cpp').read_text(encoding='utf-8')
        header = (native.CODE / 'common/item_instance.h').read_text(encoding='utf-8')
        enum_start = header.index('enum OrnamentationAugmentTypes {')
        enum_end = header.index('};', enum_start) + 2
        methods = '\n'.join(native.body(source, signature) for signature in (
            'bool EQ::ItemInstance::IsOrnamentationAugment(',
            'EQ::ItemInstance* EQ::ItemInstance::GetOrnamentationAugment(',
            'bool EQ::ItemInstance::UpdateOrnamentationInfo('))
        fixture = (native.ROOT / 'tools/tests/fixtures/augment_ornament.cpp').read_text(encoding='utf-8')
        packet = (native.CODE / 'zone/client_packet.cpp').read_text(encoding='utf-8')
        if 'const bool update_ornamentation =' in packet:
            start = packet.index('const bool update_ornamentation =')
            decision = packet[start:packet.index(';', start) + 1]
            refresh = native.body(packet, 'if (update_ornamentation)')
            self.assertEqual(len(re.findall(r'if \(update_ornamentation\)\s*\{\s*tobe_auged->UpdateOrnamentationInfo\(\);\s*\}', packet)),
                             3, 'all three augmentation paths must use the gate')
        else:
            decision = ''
            refresh = 'tobe_auged->UpdateOrnamentationInfo();'
        fixture = fixture.replace('// NATIVE_AUGMENT_DECISION', decision).replace('// NATIVE_AUGMENT_REFRESH', refresh)
        native.FreeTradeTests.compile_run(self, fixture.replace('// NATIVE_ENUM', header[enum_start:enum_end])
                                         .replace('// NATIVE_METHODS', methods))


if __name__ == '__main__':
    unittest.main()
