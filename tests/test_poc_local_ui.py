"""Issue #210: real synthetic CSV -> local HTTP -> verified report/manifest/triage."""
import http.client
import json
import re
import socket
import time
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

from agent_lab.poc_local_ui import LocalPocServer, MAX_CSV_BYTES, UPLOAD_DEADLINE_SECONDS, run_diagnostic

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "poc_204_catalog_synthetic_v1.csv"


def raw_http_request(request_line: str, headers: list[str], body: bytes = b"") -> bytes:
    """Create a CRLF-correct HTTP request for real socket security regressions.

    Allows duplicate names deliberately; rejects injected lines and literal
    backslash escapes (a former source of CI timeouts).
    """
    if (not request_line.endswith(" HTTP/1.1") or "\r" in request_line or "\n" in request_line
            or r"\r" in request_line or r"\n" in request_line):
        raise ValueError("invalid HTTP request line")
    if any(not h or ":" not in h or "\r" in h or "\n" in h
           or r"\r" in h or r"\n" in h for h in headers):
        raise ValueError("one header per list item is required")
    return ("\r\n".join([request_line, *headers, "", ""])).encode("ascii") + body


class RawHttpWireBuilderTests(unittest.TestCase):
    def test_raw_wire_uses_real_crlf_and_one_header_terminator(self):
        wire = raw_http_request(
            "POST /analyze HTTP/1.1", ["Host: 127.0.0.1:1234", "Content-Length: 3"], b"abc")
        self.assertIn(b"\r\nContent-Length: 3\r\n\r\nabc", wire)
        self.assertEqual(wire.count(b"\r\n\r\n"), 1)
        self.assertNotIn(b"\\r\\n", wire)
        self.assertEqual(wire.split(b"\r\n\r\n", 1)[1], b"abc")

    def test_wire_builder_rejects_embedded_or_literal_delimiters(self):
        for malformed in ("Host: good\r\nHost: injected", r"Host: bad\r\n", "Host"):
            with self.subTest(malformed=repr(malformed)):
                with self.assertRaises(ValueError):
                    raw_http_request("GET / HTTP/1.1", [malformed])


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

    def test_script_csp_uses_fresh_matching_nonce_and_blocks_other_inline_scripts(self):
        """Real HTTP response: only the intended page script has execution permission."""
        nonce_values = []
        for _ in range(2):
            status, headers, html = self.request("GET", "/")
            self.assertEqual(status, 200)
            csp = headers["Content-Security-Policy"]
            self.assertNotIn("script-src 'unsafe-inline'", csp)
            match = re.search(rb'<script nonce="([A-Za-z0-9_-]+)">', html)
            self.assertIsNotNone(match)
            nonce = match.group(1).decode("ascii")
            nonce_values.append(nonce)
            self.assertIn("script-src 'nonce-" + nonce + "'", csp)
            self.assertEqual(html.count(b"<script"), 1)
            self.assertNotIn(b"<script>", html)
        self.assertNotEqual(nonce_values[0], nonce_values[1])

        # Data and error routes do not authorize any JavaScript.
        for route in ("/sample.csv", "/does-not-exist"):
            with self.subTest(route=route):
                _, headers, _ = self.request("GET", route)
                self.assertIn("script-src 'none'", headers["Content-Security-Policy"])
                self.assertNotIn("script-src 'unsafe-inline'", headers["Content-Security-Policy"])

    def test_one_click_demo_uses_same_real_verified_pipeline(self):
        # HTTP integration plus explicit browser wiring; not a manual browser review.
        status, _, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b'id="example"', html)
        self.assertIn(b"await fetch('/sample.csv',{cache:'no-store'})", html)
        self.assertIn(b"await analyze(await sample.arrayBuffer())", html)
        self.assertIn(b"body:csvBytes", html)
        # Browser preflight rejects a large file before arrayBuffer allocates memory.
        self.assertIn(b"if(uploaded.size===0||uploaded.size>262144)", html)
        self.assertIn(b"await analyze(await uploaded.arrayBuffer())", html)
        status, _, sample = self.request("GET", "/sample.csv")
        self.assertEqual(status, 200)
        status, _, payload = self.upload(sample)
        self.assertEqual(status, 200, payload)
        result = json.loads(payload)
        self.assertEqual(result["summary"]["total_records"], 2)
        self.assertEqual(result["human_review"], "NOT_RECORDED")
        self.assertEqual(result["source_custody"], "UNAVAILABLE")
        for route in result["downloads"].values():
            download_status, _, data = self.request("GET", route)
            self.assertEqual(download_status, 200, data)

    def test_downloadable_sample_is_real_csv_and_completes_user_journey(self):
        code, headers, sample = self.request("GET", "/sample.csv")
        self.assertEqual(code, 200)
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertEqual(len(sample.decode("utf-8").splitlines()), 3)
        self.assertIn(b"M-DEMO-001", sample)
        status, _, body = self.upload(sample)
        self.assertEqual(status, 200, body)
        result = json.loads(body)
        self.assertEqual(result["summary"]["total_records"], 2)
        self.assertEqual(len(result["records"]), 2)
        self.assertTrue(all(r["human_review"]["status"] == "NOT_RECORDED"
                            for r in result["records"]))
        for route in result["downloads"].values():
            artifact_status, _, artifact = self.request("GET", route)
            self.assertEqual(artifact_status, 200, artifact)

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

    def test_search_interface_exposes_material_and_evidence_filter(self):
        status, _, page = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b'id="search"', page)
        self.assertIn(b"search.addEventListener('input',redraw)", page)
        self.assertIn(b"r.material_id,r.issues,r.evidence,r.duplicate_candidates", page)
        self.assertIn(b"search.value='';redraw()", page)

    def test_tampered_manifest_refuses_every_download(self):
        status, _, body = self.upload(self.csv_bytes)
        self.assertEqual(status, 200, body)
        routes = json.loads(body)["downloads"]
        run_id = routes["report"].split("/")[2]
        manifest = self.server.runs[run_id].with_name("report.json.manifest.json")
        original = manifest.read_bytes()
        # Keep the JSON parseable while corrupting the physical digest.
        payload = json.loads(original)
        digest_fields = [key for key, value in payload.items()
                         if isinstance(value, str) and len(value) == 64
                         and all(char in "0123456789abcdef" for char in value)]
        self.assertTrue(digest_fields, payload)
        payload[digest_fields[0]] = "0" * 64 if payload[digest_fields[0]] != "0" * 64 else "1" * 64
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        for route in routes.values():
            status, _, result = self.request("GET", route)
            self.assertEqual(status, 409, (route, result))
            self.assertNotIn(b"material_id", result)

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

    def test_duplicate_authority_and_security_headers_are_rejected(self):
        """Raw HTTP regression: duplicate security headers never select an arbitrary value."""
        baseline = set(self.server.runs)
        for extra_header, expected_status in (
            ("Host: localhost:{port}", b" 403 "),
            ("X-Poc-Token: invalid", b" 403 "),
            ("Origin: http://127.0.0.1:{port}", b" 403 "),
            ("Content-Type: text/csv", b" 403 "),
        ):
            with self.subTest(extra_header=extra_header):
                port = self.server.server_port
                request = raw_http_request(
                    "POST /analyze?catalog_id=TEST-215 HTTP/1.1",
                    [
                        f"Host: 127.0.0.1:{port}",
                        "Content-Type: text/csv",
                        f"X-Poc-Token: {self.server.csrf_token}",
                        f"Origin: http://127.0.0.1:{port}",
                        extra_header.format(port=port),
                        "Content-Length: 3",
                        "Connection: close",
                    ],
                    b"abc",
                )
                with socket.create_connection(("127.0.0.1", port), timeout=5) as conn:
                    conn.settimeout(5)
                    conn.sendall(request)
                    status_line = conn.recv(4096).split(b"\r\n", 1)[0]
                self.assertIn(expected_status, status_line)
                self.assertEqual(set(self.server.runs), baseline)
                self.assertEqual(self.server.pending_runs, set())

    def test_incomplete_http_upload_deadline_is_bounded_and_fail_closed(self):
        """Real socket adversarial regression for #217 (no mocked reader)."""
        before_runs = set(self.server.runs)
        before_pending = set(self.server.pending_runs)
        before_dirs = set(Path(self.server.workspace.name).iterdir())
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=4) as conn:
            conn.settimeout(UPLOAD_DEADLINE_SECONDS + 4)
            headers = raw_http_request(
                "POST /analyze?catalog_id=TEST-217 HTTP/1.1",
                [
                    f"Host: 127.0.0.1:{self.server.server_port}",
                    "Content-Type: text/csv",
                    f"X-Poc-Token: {self.server.csrf_token}",
                    "Content-Length: 128",
                    "Connection: close",
                ],
            )
            started = time.monotonic()
            conn.sendall(headers + b"partial")
            status_line = conn.recv(4096).split(b"\r\n", 1)[0]
            elapsed = time.monotonic() - started
        self.assertIn(b" 408 ", status_line)
        self.assertLess(elapsed, UPLOAD_DEADLINE_SECONDS + 2.0)
        self.assertEqual(set(self.server.runs), before_runs)
        self.assertEqual(set(self.server.pending_runs), before_pending)
        self.assertEqual(set(Path(self.server.workspace.name).iterdir()), before_dirs)

        # A failed connection must not poison the next valid user journey.
        status, _, body = self.upload(self.csv_bytes)
        self.assertEqual(status, 200, body)
        self.assertIn("downloads", json.loads(body))

    def test_ambiguous_http_body_framing_is_rejected_before_csv_read(self):
        """Real TCP regressions: no chunked or duplicate Content-Length framing."""
        baseline_runs = set(self.server.runs)
        baseline_pending = set(self.server.pending_runs)
        baseline_dirs = set(Path(self.server.workspace.name).iterdir())
        for framing in (
            "Transfer-Encoding: chunked\r\nContent-Length: 8\r\n",
            "Transfer-Encoding: chunked\r\n",
            "Content-Length: 8\r\nContent-Length: 8\r\n",
        ):
            with self.subTest(framing=framing):
                with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=3) as conn:
                    conn.settimeout(3)
                    request = raw_http_request(
                        "POST /analyze?catalog_id=TEST-215 HTTP/1.1",
                        [
                            f"Host: 127.0.0.1:{self.server.server_port}",
                            "Content-Type: text/csv",
                            f"X-Poc-Token: {self.server.csrf_token}",
                            *framing.rstrip("\r\n").split("\r\n"),
                            "Connection: close",
                        ],
                    )
                    conn.sendall(request)
                    response = conn.recv(4096)
                self.assertIn(b" 400 ", response.split(b"\r\n", 1)[0])
                self.assertEqual(set(self.server.runs), baseline_runs)
                self.assertEqual(set(self.server.pending_runs), baseline_pending)
                self.assertEqual(set(Path(self.server.workspace.name).iterdir()), baseline_dirs)

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
