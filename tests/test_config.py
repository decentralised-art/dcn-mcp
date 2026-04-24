import importlib
import os
import unittest
from unittest.mock import patch

import dcn_mcp.config as config


class ConfigTests(unittest.TestCase):
    def tearDown(self):
        importlib.reload(config)

    def test_invalid_timeout_env_falls_back_without_import_failure(self):
        with patch.dict(os.environ, {"DCN_TIMEOUT": "not-a-number"}):
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.DEFAULT_TIMEOUT, reloaded.DEFAULT_TIMEOUT_SECONDS)

    def test_out_of_range_timeout_env_falls_back(self):
        with patch.dict(os.environ, {"DCN_TIMEOUT": "0"}):
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.DEFAULT_TIMEOUT, reloaded.DEFAULT_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
