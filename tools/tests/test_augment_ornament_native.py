"""Run actual ornament classification/update methods against item boundary doubles."""
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
        native.FreeTradeTests.compile_run(self, fixture.replace('// NATIVE_ENUM', header[enum_start:enum_end])
                                         .replace('// NATIVE_METHODS', methods))


if __name__ == '__main__':
    unittest.main()
