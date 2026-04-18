from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gitsonar.runtime_github import make_github_runtime
from gitsonar.runtime_github.shared import GitHubRuntimeDeps


class RuntimeGitHubExportTests(unittest.TestCase):
    def test_public_exports_are_available(self):
        self.assertTrue(callable(make_github_runtime))
        self.assertEqual(GitHubRuntimeDeps.__name__, "GitHubRuntimeDeps")


if __name__ == "__main__":
    unittest.main()
