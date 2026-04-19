from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def clear_gitsonar_modules() -> None:
    for name in list(sys.modules):
        if name == "gitsonar" or name.startswith("gitsonar."):
            sys.modules.pop(name, None)


class ImportSideEffectTests(unittest.TestCase):
    def test_importing_package_keeps_runtime_app_lazy(self):
        clear_gitsonar_modules()
        with (
            mock.patch("shutil.copy2") as copy2,
            mock.patch("shutil.copytree") as copytree,
            mock.patch("requests.Session", side_effect=AssertionError("runtime sessions should not be created")),
        ):
            package = importlib.import_module("gitsonar")

        self.assertIn("main", package.__all__)
        self.assertNotIn("gitsonar.runtime.app", sys.modules)
        copy2.assert_not_called()
        copytree.assert_not_called()

    def test_importing_runtime_app_does_not_build_handler_or_run_migration(self):
        clear_gitsonar_modules()
        with (
            mock.patch("shutil.copy2") as copy2,
            mock.patch("shutil.copytree") as copytree,
            mock.patch("requests.Session", side_effect=AssertionError("runtime sessions should not be created")),
        ):
            runtime_app = importlib.import_module("gitsonar.runtime.app")

        self.assertIsNone(runtime_app.ServerAppHandler)
        self.assertIsNone(runtime_app.github_runtime)
        self.assertIsNone(runtime_app.shell_runtime)
        copy2.assert_not_called()
        copytree.assert_not_called()


if __name__ == "__main__":
    unittest.main()
