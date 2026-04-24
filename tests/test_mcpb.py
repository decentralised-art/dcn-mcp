from __future__ import annotations

import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from dcn_mcp.mcpb import build_bundle, build_manifest


class McpbTests(TestCase):
    def test_manifest_uses_uv_runtime(self) -> None:
        manifest = build_manifest()
        self.assertEqual(manifest["manifest_version"], "0.4")
        self.assertEqual(manifest["server"]["type"], "uv")
        self.assertEqual(manifest["server"]["mcp_config"]["command"], "uv")
        self.assertIn("api_base", manifest["user_config"])
        self.assertIn("private_key", manifest["user_config"])
        self.assertIn("dcn_timeout", manifest["user_config"])
        self.assertIn("artifact_root", manifest["user_config"])
        self.assertTrue(any(tool["name"] == "core.build_parent_connector" for tool in manifest["tools"]))

    def test_build_bundle_writes_expected_files(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            bundle_path = build_bundle(Path(tmp_dir))
            self.assertTrue(bundle_path.exists())
            self.assertEqual(bundle_path.suffix, ".mcpb")
            with zipfile.ZipFile(bundle_path) as archive:
                names = set(archive.namelist())
                self.assertIn("manifest.json", names)
                self.assertIn("pyproject.toml", names)
                self.assertIn("README.md", names)
                self.assertIn("src/dcn_mcp/server.py", names)
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
                self.assertEqual(manifest["name"], "dcn-mcp")
