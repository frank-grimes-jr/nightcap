import unittest
from client_hub_models import add_models


class HubModels(unittest.TestCase):
    def test_preserves_existing_imports_and_is_idempotent(self):
        result = add_models(b'2\r\ncst,cst\r\nfrt,innothule_chr\r\n')
        self.assertTrue(result.startswith(b'7\r\ncst,cst\r\nfrt,innothule_chr\r\n'))
        for code in ('mur','scu','frd','ddv','srn'):
            self.assertIn((code+','+code+'\r\n').encode(), result)
        self.assertEqual(add_models(result), result)

    def test_rejects_malformed_or_conflicting_imports(self):
        for raw in (b'2\nx,x\n', b'1\nmur,other\n', b'2\nx,x\nx,x\n', b'1\nx,../x\n'):
            with self.assertRaises(ValueError): add_models(raw)


if __name__ == '__main__': unittest.main()
