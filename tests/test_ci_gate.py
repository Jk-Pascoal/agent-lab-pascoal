import unittest


class CIGateProtectionTest(unittest.TestCase):
    def test_ci_gate_blocks_merge_when_tests_fail(self):
        self.fail(
            "Falha controlada da Issue #12 para validar "
            "o bloqueio de merge pelo GitHub Ruleset."
        )


if __name__ == "__main__":
    unittest.main()