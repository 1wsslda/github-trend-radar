from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gitsonar.runtime.paths as runtime_paths


class RuntimePathMergeTests(unittest.TestCase):
    def merge_dev_runtime_root(self) -> str:
        with (
            patch.object(runtime_paths.logger, "info"),
            patch.object(runtime_paths.logger, "warning"),
        ):
            return runtime_paths.merge_dev_runtime_root()

    def merge_legacy_runtime_root(self) -> str:
        with (
            patch.object(runtime_paths.logger, "info"),
            patch.object(runtime_paths.logger, "warning"),
        ):
            return runtime_paths.merge_legacy_runtime_root()

    def test_merge_dev_runtime_root_copies_missing_items(self):
        with tempfile.TemporaryDirectory() as tempdir:
            legacy = Path(tempdir) / "legacy-root"
            preferred = Path(tempdir) / "runtime-data"
            legacy.mkdir()
            (legacy / "settings.json").write_text('{"theme":"legacy"}', encoding="utf-8")
            (legacy / "data").mkdir()
            (legacy / "data" / "latest.json").write_text('{"ok":true}', encoding="utf-8")

            with patch.multiple(
                runtime_paths,
                PROJECT_ROOT=str(legacy),
                DEV_RUNTIME_ROOT=str(preferred),
                DEV_RUNTIME_ITEMS=("settings.json", "data"),
            ):
                merged_root = self.merge_dev_runtime_root()

            self.assertEqual(merged_root, str(preferred))
            self.assertEqual((preferred / "settings.json").read_text(encoding="utf-8"), '{"theme":"legacy"}')
            self.assertEqual((preferred / "data" / "latest.json").read_text(encoding="utf-8"), '{"ok":true}')

    def test_merge_dev_runtime_root_falls_back_when_runtime_dir_init_fails(self):
        with tempfile.TemporaryDirectory() as tempdir:
            legacy = Path(tempdir) / "legacy-root"
            preferred = Path(tempdir) / "runtime-data"
            legacy.mkdir()

            with (
                patch.multiple(
                    runtime_paths,
                    PROJECT_ROOT=str(legacy),
                    DEV_RUNTIME_ROOT=str(preferred),
                    DEV_RUNTIME_ITEMS=("settings.json",),
                ),
                patch.object(runtime_paths.os, "makedirs", side_effect=OSError("boom")),
            ):
                merged_root = self.merge_dev_runtime_root()

            self.assertEqual(merged_root, str(legacy))

    def test_merge_dev_runtime_root_keeps_existing_targets(self):
        with tempfile.TemporaryDirectory() as tempdir:
            legacy = Path(tempdir) / "legacy-root"
            preferred = Path(tempdir) / "runtime-data"
            legacy.mkdir()
            preferred.mkdir()
            (legacy / "settings.json").write_text('{"theme":"legacy"}', encoding="utf-8")
            (preferred / "settings.json").write_text('{"theme":"preferred"}', encoding="utf-8")

            with patch.multiple(
                runtime_paths,
                PROJECT_ROOT=str(legacy),
                DEV_RUNTIME_ROOT=str(preferred),
                DEV_RUNTIME_ITEMS=("settings.json",),
            ):
                merged_root = self.merge_dev_runtime_root()

            self.assertEqual(merged_root, str(preferred))
            self.assertEqual((preferred / "settings.json").read_text(encoding="utf-8"), '{"theme":"preferred"}')

    def test_merge_legacy_runtime_root_copies_missing_items(self):
        with tempfile.TemporaryDirectory() as tempdir:
            appdata = Path(tempdir)
            legacy = appdata / runtime_paths.LEGACY_APP_SLUG
            preferred = appdata / runtime_paths.APP_SLUG
            legacy.mkdir()
            (legacy / "settings.json").write_text('{"theme":"legacy"}', encoding="utf-8")
            (legacy / "data").mkdir()
            (legacy / "data" / "latest.json").write_text('{"ok":true}', encoding="utf-8")

            with patch.multiple(
                runtime_paths,
                IS_FROZEN=True,
                LOCAL_APPDATA_ROOT=str(appdata),
            ):
                merged_root = self.merge_legacy_runtime_root()

            self.assertEqual(merged_root, str(preferred))
            self.assertEqual((preferred / "settings.json").read_text(encoding="utf-8"), '{"theme":"legacy"}')
            self.assertEqual((preferred / "data" / "latest.json").read_text(encoding="utf-8"), '{"ok":true}')

    def test_merge_legacy_runtime_root_falls_back_to_legacy_when_init_fails(self):
        with tempfile.TemporaryDirectory() as tempdir:
            appdata = Path(tempdir)
            legacy = appdata / runtime_paths.LEGACY_APP_SLUG
            legacy.mkdir()

            with (
                patch.multiple(
                    runtime_paths,
                    IS_FROZEN=True,
                    LOCAL_APPDATA_ROOT=str(appdata),
                ),
                patch.object(runtime_paths.os, "makedirs", side_effect=OSError("boom")),
            ):
                merged_root = self.merge_legacy_runtime_root()

            self.assertEqual(merged_root, str(legacy))

    def test_merge_legacy_runtime_root_keeps_existing_targets(self):
        with tempfile.TemporaryDirectory() as tempdir:
            appdata = Path(tempdir)
            legacy = appdata / runtime_paths.LEGACY_APP_SLUG
            preferred = appdata / runtime_paths.APP_SLUG
            legacy.mkdir()
            preferred.mkdir()
            (legacy / "settings.json").write_text('{"theme":"legacy"}', encoding="utf-8")
            (preferred / "settings.json").write_text('{"theme":"preferred"}', encoding="utf-8")

            with patch.multiple(
                runtime_paths,
                IS_FROZEN=True,
                LOCAL_APPDATA_ROOT=str(appdata),
            ):
                merged_root = self.merge_legacy_runtime_root()

            self.assertEqual(merged_root, str(preferred))
            self.assertEqual((preferred / "settings.json").read_text(encoding="utf-8"), '{"theme":"preferred"}')


if __name__ == "__main__":
    unittest.main()
