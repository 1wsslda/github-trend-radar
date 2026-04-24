from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseManifestScriptTests(unittest.TestCase):
    def test_script_writes_manifest_and_sha256sums_for_release_artifacts(self):
        shell = shutil.which("powershell") or shutil.which("pwsh")
        if not shell:
            self.skipTest("PowerShell is not available")

        with tempfile.TemporaryDirectory() as tempdir:
            dist_root = Path(tempdir)
            exe_path = dist_root / "GitSonar.exe"
            installer_dir = dist_root / "installer"
            installer_dir.mkdir()
            installer_path = installer_dir / "GitSonarSetup.exe"
            exe_path.write_bytes(b"portable exe")
            installer_path.write_bytes(b"installer exe")

            result = subprocess.run(
                [
                    shell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROOT / "scripts" / "write_release_manifest.ps1"),
                    "-DistRoot",
                    str(dist_root),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            manifest = json.loads((dist_root / "release-manifest.json").read_text(encoding="utf-8-sig"))
            sums = (dist_root / "SHA256SUMS.txt").read_text(encoding="ascii")

        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        self.assertEqual(set(artifacts), {"GitSonar.exe", "installer/GitSonarSetup.exe"})
        self.assertEqual(artifacts["GitSonar.exe"]["size"], len(b"portable exe"))
        self.assertEqual(artifacts["GitSonar.exe"]["sha256"], hashlib.sha256(b"portable exe").hexdigest())
        self.assertIn("GitSonar.exe", sums)
        self.assertIn("installer/GitSonarSetup.exe", sums)


if __name__ == "__main__":
    unittest.main()
