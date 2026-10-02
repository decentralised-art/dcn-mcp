import importlib
import os
import tempfile
import unittest
from unittest.mock import patch

import decentralised_art_mcp.config as config


class ConfigTests(unittest.TestCase):
    def tearDown(self):
        importlib.reload(config)

    def test_invalid_timeout_env_falls_back_without_import_failure(self):
        with patch.dict(os.environ, {"DECENTRALISED_ART_TIMEOUT": "not-a-number"}):
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.DEFAULT_TIMEOUT, reloaded.DEFAULT_TIMEOUT_SECONDS)

    def test_out_of_range_timeout_env_falls_back(self):
        with patch.dict(os.environ, {"DECENTRALISED_ART_TIMEOUT": "0"}):
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.DEFAULT_TIMEOUT, reloaded.DEFAULT_TIMEOUT_SECONDS)


    def test_legacy_settings_are_read_when_new_ones_are_unset(self):
        env = {"DCN_TIMEOUT": "42", "DCN_ARTIFACT_ROOT": "/tmp/legacy-records"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("DECENTRALISED_ART_TIMEOUT", None)
            os.environ.pop("DECENTRALISED_ART_ARTIFACT_ROOT", None)
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.DEFAULT_TIMEOUT, 42.0)
            self.assertEqual(reloaded.DEFAULT_ARTIFACT_ROOT, "/tmp/legacy-records")

    def test_new_settings_take_precedence_over_legacy_ones(self):
        env = {
            "DCN_TIMEOUT": "42",
            "DECENTRALISED_ART_TIMEOUT": "7",
            "DCN_ARTIFACT_ROOT": "/tmp/legacy-records",
            "DECENTRALISED_ART_ARTIFACT_ROOT": "/tmp/records",
        }
        with patch.dict(os.environ, env):
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.DEFAULT_TIMEOUT, 7.0)
            self.assertEqual(reloaded.DEFAULT_ARTIFACT_ROOT, "/tmp/records")

    def test_existing_legacy_records_folder_is_kept_by_default(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=False):
            for name in ("DECENTRALISED_ART_ARTIFACT_ROOT", "DCN_ARTIFACT_ROOT"):
                os.environ.pop(name, None)
            previous = os.getcwd()
            os.chdir(folder)
            try:
                self.assertEqual(config.default_artifact_root(), "decentralised-art-mcp-artifacts")
                os.mkdir("dcn-mcp-artifacts")
                self.assertEqual(config.default_artifact_root(), "dcn-mcp-artifacts")
                os.mkdir("decentralised-art-mcp-artifacts")
                self.assertEqual(config.default_artifact_root(), "decentralised-art-mcp-artifacts")
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
