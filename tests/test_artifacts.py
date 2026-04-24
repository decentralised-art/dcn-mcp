import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dcn_mcp.artifacts import resolve_artifact_path, write_json
from dcn_mcp.errors import ValidationError


class ArtifactTests(unittest.TestCase):
    def test_artifact_paths_are_confined_to_root(self):
        with TemporaryDirectory() as tmp_dir:
            with patch("dcn_mcp.artifacts.DEFAULT_ARTIFACT_ROOT", tmp_dir):
                resolved = resolve_artifact_path("nested/payload.json")
                self.assertEqual(resolved, Path(tmp_dir).resolve() / "nested" / "payload.json")

                with self.assertRaises(ValidationError):
                    resolve_artifact_path("../outside.json")

                with self.assertRaises(ValidationError):
                    resolve_artifact_path(str(Path(tmp_dir).resolve().parent / "outside.json"))

    def test_write_json_creates_artifact_under_root(self):
        with TemporaryDirectory() as tmp_dir:
            with patch("dcn_mcp.artifacts.DEFAULT_ARTIFACT_ROOT", tmp_dir):
                path = resolve_artifact_path("payload.json")
                written = write_json(path, {"ok": True})
                self.assertEqual(Path(written), path)
                self.assertIn('"ok": true', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
