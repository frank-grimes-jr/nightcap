"""Run the native RoF2 distiller gate and Remove case with an in-memory inventory."""
import unittest

import test_free_trade as native


class TunnelDistillerTests(unittest.TestCase):
    def test_native_removal(self):
        source = (native.CODE / "zone/client_packet.cpp").read_text(encoding="utf-8")
        handler = native.body(source, "void Client::Handle_OP_AugmentItem(")
        gate = native.body(handler, "if (in_augment->augment_action == AugmentActions::Remove")
        start = handler.index("case AugmentActions::Remove:")
        end = handler.index("case AugmentActions::Destroy:", start)
        fixture = (native.ROOT / "tools/tests/fixtures/tunnel_distiller.cpp").read_text()
        native.FreeTradeTests.compile_run(self, fixture.replace("// DISTILLER_GATE", gate)
                                          .replace("// REMOVE_CASE", handler[start:end]))


if __name__ == "__main__":
    unittest.main()
