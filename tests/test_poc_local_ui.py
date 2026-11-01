"""Issue #210: real synthetic CSV -> local HTTP -> verified report/manifest/triage."""
import http.client
import json
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

from agent_lab.poc_local_ui import LocalPocServer, MAX_CSV_BYTES, run_diagnostic

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "poc_204_catalog_synthetic_v1.csv"


class PocLocalJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalPocServer(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.csv_bytes = FIXTURE.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    def request(self, method, route, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        try:
            connection.request(method, route, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def upload(self, content, *, token=None):
        return self.request("POST", "/analyze?catalog_id=TEST-210", content, {
            "Content-Type": "text/csv",
            "X-Poc-Token": self.server.csrf_token if token is None else token,
        })

    def test_local_page_exposes_upload_and_no_remote_dependencies(self):
        code, headers, body = self.request("GET", "/")
        self.assertEqual(code, 200)
        self.assertIn(b"diagn\xc3\xb3stico", body.lower())
        self.assertIn(self.server.csrf_token.encode(), body)
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertNotIn(b"https://", body)

    def test_real_fixture_end_to_end_verified_report_manifest_and_triage(self):
        code, _, body = self.upload(self.csv_bytes)
        self.assertEqual(code, 200, body)
        result = json.loads(body)
        self.assertEqual(result["summary"]["total_records"], 3)
        self.assertEqual([x["material_id"] for x in result["records"]],
                         ["M-SYN-001", "M-SYN-002", "M-SYN-003"])
        self.assertEqual(result["source_custody"], "UNAVAILABLE")
        self.assertTrue(all(r["human_review"]["status"] == "NOT_RECORDED"
                            and r["source_row_status"] == "UNAVAILABLE" for r in result["records"]))
        artifacts = {}
        for name, route in result["downloads"].items():
            status, _, content = self.request("GET", route)
            self.assertEqual(status, 200, (name, content))
            artifacts[name] = content
        self.assertEqual(json.loads(artifacts["report"])["summary"], result["summary"])
        self.assertEqual(json.loads(artifacts["manifest"])["schema_version"], "poc_audit_manifest.v0")
        self.assertIn(b"human_review_status", artifacts["triage"])
        self.assertIn(b"NOT_RECORDED", artifacts["triage"])

    def test_missing_manifest_blocks_all_downloads(self):
        status, _, body = self.upload(self.csv_bytes)
        self.assertEqual(status, 200, body)
        routes = json.loads(body)["downloads"]
        run_id = routes["report"].split("/")[2]
        manifest = self.server.runs[run_id].with_name("report.json.manifest.json")
        manifest.unlink()
        for route in routes.values():
            status, _, payload = self.request("GET", route)
            self.assertEqual(status, 409)
            self.assertNotIn(b"material_id", payload)

    def test_invalid_csv_fails_without_download_links(self):
        status, _, response = self.upload(b"unknown_column\nSYN-001\n")
        self.assertEqual(status, 422, response)
        self.assertNotIn(b"downloads", response)

    def test_oversized_upload_rejected_before_parse(self):
        status, _, response = self.upload(b"a" * (MAX_CSV_BYTES + 1))
        self.assertEqual(status, 413, response)
        self.assertNotIn(b"downloads", response)

    def test_failed_upload_reclaims_disk_and_does_not_consume_a_session(self):
        previous_runs = set(self.server.runs)
        previous_dirs = set(Path(self.server.workspace.name).iterdir())
        status, _, body = self.upload(b"unknown_column\\nSYN-001\\n")
        self.assertEqual(status, 422, body)
        self.assertEqual(set(self.server.runs), previous_runs)
        self.assertEqual(self.server.pending_runs, set())
        self.assertEqual(set(Path(self.server.workspace.name).iterdir()), previous_dirs)

    def test_inflight_artifact_is_not_published_until_verification(self):
        reached = threading.Event()
        proceed = threading.Event()
        outcome = []
        before = set(self.server.runs)

        def slow_diagnostic(csv_bytes, catalog_id, directory):
            reached.set()
            if not proceed.wait(timeout=10):
                raise RuntimeError("test timed out waiting for release")
            return run_diagnostic(csv_bytes, catalog_id, directory)

        with patch("agent_lab.poc_local_ui.run_diagnostic", side_effect=slow_diagnostic):
            worker = threading.Thread(
                target=lambda: outcome.append(self.upload(self.csv_bytes)), daemon=True)
            worker.start()
            try:
                self.assertTrue(reached.wait(timeout=5))
                self.assertEqual(set(self.server.runs), before)
                self.assertEqual(len(self.server.pending_runs), 1)
            finally:
                proceed.set()
                worker.join(timeout=10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcome[0][0], 200, outcome[0][2])
        self.assertEqual(len(self.server.runs), len(before) + 1)
        self.assertEqual(self.server.pending_runs, set())

    def test_rejects_missing_token_and_untrusted_origin_and_host(self):
        status, _, _ = self.upload(self.csv_bytes, token="wrong")
        self.assertEqual(status, 403)
        status, _, _ = self.request("POST", "/analyze", self.csv_bytes, {
            "Content-Type": "text/csv", "X-Poc-Token": self.server.csrf_token,
            "Origin": "https://not-local.example",
        })
        self.assertEqual(status, 403)
        status, _, _ = self.request("GET", "/", headers={"Host": "other.example"})
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
