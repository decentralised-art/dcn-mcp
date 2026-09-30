import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dcn_mcp.artifacts import resolve_artifact_path
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

if __name__ == "__main__":
    unittest.main()
