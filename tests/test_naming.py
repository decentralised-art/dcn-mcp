import unittest

from dcn_mcp.naming import ensure_unique_name, sanitize_name


class FakeDCN:
    def __init__(self, existing):
        self.existing = set(existing)

    def connector_exists(self, name):
        return name in self.existing


class NamingTests(unittest.TestCase):
    def test_sanitize_name_normalizes(self):
        self.assertEqual(sanitize_name(" 12 bad name ", prefix="x"), "x_12_bad_name")

    def test_ensure_unique_name_skips_reserved_and_existing(self):
        dcn = FakeDCN({"abc_2"})
        self.assertEqual(ensure_unique_name(dcn, "abc", ["abc"]), "abc_3")


if __name__ == "__main__":
    unittest.main()
