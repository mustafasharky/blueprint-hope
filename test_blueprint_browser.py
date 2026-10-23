import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import blueprint_browser as b


class ExportTests(unittest.TestCase):
    def test_only_exact_blueprint_hosts_or_explicit_hosts(self):
        self.assertEqual(b.report_url("https://my.blueprintprep.com/analytics", ["blueprintprep.com"]),
                         "https://my.blueprintprep.com/analytics")
        for url in ("https://blueprintprep.com.evil.test/analytics", "https://notblueprintprep.com/analytics",
                    "http://blueprintprep.com/analytics", "https://u:p@blueprintprep.com/analytics"):
            with self.assertRaises(ValueError):
                b.report_url(url, ["blueprintprep.com"])

    def test_auth_urls_rejected_but_report_filters_preserved(self):
        for url in ("https://blueprintprep.com/login", "https://blueprintprep.com/analytics?access_token=secret",
                    "https://blueprintprep.com/#access_token=secret", "https://blueprintprep.com/#/auth/callback",
                    "https://blueprintprep.com/analytics?code=secret"):
            with self.assertRaises(ValueError):
                b.report_url(url, ["blueprintprep.com"])
        url = "https://blueprintprep.com/analytics?start=2026-10-01&page=2"
        self.assertEqual(b.report_url(url, ["blueprintprep.com"]), url)

    def test_discovery_contains_types_not_response_values(self):
        value = {"attempts": [{"score": 504, "correct": True, "name": "LearnerName"}],
                 "access_token": "my-secret", "nested": {"refreshToken": "refresh-secret"}}
        result = json.dumps(b.shape(value))
        for content in ("504", "LearnerName", "my-secret", "refresh-secret", "access_token", "refreshToken"):
            self.assertNotIn(content, result)
        self.assertIn("boolean", result)

    def test_endpoint_labels_omit_query_and_fragment(self):
        self.assertEqual(b.endpoint_label("https://blueprintprep.com/api/report?session=secret#secret"),
                         "https://blueprintprep.com/api/report")

    def test_failed_run_preserves_latest_context(self):
        inspector = b.Inspector(["blueprintprep.com"])
        row = {"url": "https://blueprintprep.com/analytics", "title": "Analytics", "captured_at": b.now(),
               "text": "Sample report text"}
        with tempfile.TemporaryDirectory() as tmp, patch.object(b, "PRIVATE", Path(tmp)):
            b.write_exports([row], inspector, "capture")
            before = (Path(tmp) / "blueprint_context.md").read_bytes()
            b.write_exports([], inspector, "sync", [{"error": "reauthenticate"}])
            self.assertEqual((Path(tmp) / "blueprint_context.md").read_bytes(), before)
            self.assertEqual(len(list((Path(tmp) / "browser_exports").iterdir())), 2)

    def test_known_bearer_and_jwt_strings_redacted(self):
        text = "Bearer secret-value and eyJabc.def.signature"
        self.assertNotIn("secret-value", b.clean_text(text))
        self.assertNotIn("eyJabc", b.clean_text(text))


class PageTests(unittest.IsolatedAsyncioTestCase):
    async def test_password_form_is_not_exported(self):
        page = MagicMock()
        page.url = "https://blueprintprep.com/analytics"
        password = MagicMock()
        password.count = AsyncMock(return_value=1)
        password.nth.return_value.is_visible = AsyncMock(return_value=True)
        page.locator.return_value = password
        with self.assertRaises(ValueError):
            await b.capture_page(page, ["blueprintprep.com"])

    async def test_json_observer_stores_only_shape(self):
        inspector = b.Inspector(["blueprintprep.com"])
        response = MagicMock()
        response.url = "https://blueprintprep.com/api/results?email=private@example.com"
        response.status = 200
        response.request.resource_type = "fetch"
        response.request.method = "GET"
        response.headers = {"content-type": "application/json"}
        response.body = AsyncMock(return_value=b'{"score":504,"token":"secret"}')
        await inspector.inspect(response)
        serialized = json.dumps(list(inspector.items.values()))
        self.assertIn("number", serialized)
        for forbidden in ("504", "secret", "private@example.com"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
