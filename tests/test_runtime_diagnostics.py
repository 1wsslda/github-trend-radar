from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.diagnostics import make_diagnostics_runtime


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"rate": {"remaining": 42, "reset": 123}}


class _Session:
    def get(self, *_args, **_kwargs):
        return _Response()


class RuntimeDiagnosticsTests(unittest.TestCase):
    def test_diagnostics_redacts_proxy_credentials_and_runtime_root(self):
        with tempfile.TemporaryDirectory() as tempdir:
            runtime = make_diagnostics_runtime(
                app_name="GitSonar",
                runtime_root=tempdir,
                status_path=str(Path(tempdir) / "status.json"),
                sanitize_settings=lambda _include_sensitive=False: {
                    "effective_proxy": "http://user:pass@127.0.0.1:7890",
                    "proxy_source": "configured",
                },
                current_port=lambda: 8080,
                validate_github_token=lambda: {"state": "success", "message": "ok", "login": "octo"},
                load_json_file=lambda _path, default: default,
                session=_Session(),
                api_timeout=(1, 1),
                trending_timeout=(1, 1),
                tcp_port_open=lambda _host, _port: True,
                iso_now=lambda: "now",
            )

            report = runtime.run_diagnostics()
            report_text = json.dumps(report, ensure_ascii=False)

            self.assertIn("http://***:***@127.0.0.1:7890", report_text)
            self.assertNotIn("user:pass", report_text)
            self.assertNotIn(tempdir, report_text)


if __name__ == "__main__":
    unittest.main()
