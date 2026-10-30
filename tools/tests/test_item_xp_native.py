"""Execute actual inventory award/publication with deterministic boundary faults."""
import unittest
import test_free_trade as native


class ItemXPNativeTests(unittest.TestCase):
    def test_actual_award_failure_paths(self):
        source=(native.CODE/'zone/advanced_loot_inventory.cpp').read_text(encoding='utf-8')
        instance=(native.CODE/'common/item_instance.cpp').read_text(encoding='utf-8')
        fixture=(native.ROOT/'tools/tests/fixtures/item_xp_award.cpp').read_text(encoding='utf-8')
        metadata='\n'.join(native.body(instance,s) for s in (
            'std::string EQ::ItemInstance::GetCustomDataString(',
            'void EQ::ItemInstance::SetCustomDataString(',
            'void EQ::ItemInstance::SetCustomData(const std::string& identifier, const std::string& value)',
            'void EQ::ItemInstance::DeleteCustomData('))
        award='\n'.join(native.body(source,s) for s in (
            'InventoryRow FromItem(', 'std::vector<std::string> Values(',
            'bool CanTrainItem(', 'static bool TrainingLoreConflict(',
            'TransferResult AwardItemExperience('))
        native.FreeTradeTests.compile_run(self,fixture.replace('// NATIVE_METADATA',metadata).replace('// NATIVE_AWARD',award))


if __name__ == '__main__':
    unittest.main()
