from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.discovery_clusters import cluster_discovery_results
from gitsonar.runtime.utils import normalize


class DiscoveryClusterTests(unittest.TestCase):
    def test_clusters_are_stable_and_assign_labels_to_repos(self):
        repos = [
            {
                "full_name": "octo/win-rpa",
                "url": "https://github.com/octo/win-rpa",
                "description": "Desktop automation toolkit for Windows workflows",
                "language": "Python",
                "topics": ["desktop-automation", "windows"],
                "composite_score": 92,
            },
            {
                "full_name": "octo/rpa-runner",
                "url": "https://github.com/octo/rpa-runner",
                "description": "RPA runner for desktop automation",
                "language": "Python",
                "topics": ["desktop-automation", "rpa"],
                "composite_score": 88,
            },
            {
                "full_name": "octo/browser-bot",
                "url": "https://github.com/octo/browser-bot",
                "description": "Browser automation with Playwright",
                "language": "TypeScript",
                "topics": ["browser-automation", "playwright"],
                "composite_score": 75,
            },
            {
                "full_name": "octo/web-rpa",
                "url": "https://github.com/octo/web-rpa",
                "description": "Web RPA helpers for browser automation",
                "language": "TypeScript",
                "topics": ["browser-automation", "web"],
                "composite_score": 70,
            },
        ]

        annotated, clusters = cluster_discovery_results(repos, normalize=normalize)

        self.assertEqual([cluster["label"] for cluster in clusters], ["Desktop Automation", "Browser Automation"])
        self.assertEqual(clusters[0]["count"], 2)
        self.assertEqual(
            clusters[0]["repo_urls"],
            ["https://github.com/octo/win-rpa", "https://github.com/octo/rpa-runner"],
        )
        self.assertEqual(annotated[0]["cluster_label"], "Desktop Automation")
        self.assertEqual(annotated[2]["cluster_label"], "Browser Automation")
        self.assertNotEqual(annotated[0]["cluster_id"], annotated[2]["cluster_id"])


if __name__ == "__main__":
    unittest.main()
