"""Optional real-browser smoke for synthetic local CSV journey (#223).

Install dev-only browser tooling:
    python -m pip install playwright
    python -m playwright install chromium
Run from repository root:
    python scripts/poc_210_browser_smoke.py --evidence-dir browser-evidence

No external URLs, real ERP data, runtime dependency or human approval implied.
The canonical unittest suite remains unchanged. This is automated browser
evidence, NOT the independent/manual review required by Issue #215.
"""
import argparse
import json
import threading
from pathlib import Path

from agent_lab.poc_audit_verify import verify_poc_audit_report_pair
from agent_lab.poc_local_ui import LocalPocServer


def run(evidence_dir: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Install optional tooling: pip install playwright; playwright install chromium") from exc

    evidence_dir.mkdir(parents=True, exist_ok=True)
    server = LocalPocServer(0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    errors = []
    worker.start()
    try:
        origin = f"http://127.0.0.1:{server.server_port}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(accept_downloads=False)
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(origin + "/", wait_until="domcontentloaded")
                page.locator("#example").click()
                page.locator("#result").wait_for(state="visible", timeout=15000)
                assert page.locator("#records tr").count() == 2, "synthetic example did not show two materials"
                assert "2 de 2" in page.locator("#count").inner_text()
                assert page.locator("#metrics").get_by_text("Registros").count() == 1

                links = page.locator("#downloads a")
                assert links.count() == 3, "expected report, manifest and triage downloads"
                urls = {}
                for index in range(links.count()):
                    item = links.nth(index)
                    name = item.inner_text().strip()
                    href = item.get_attribute("href")
                    assert href and href.startswith("/artifact/"), "unexpected download URL"
                    urls[name] = href
                assert set(urls) == {"Relatório JSON", "Manifesto SHA-256", "Triagem CSV"}
                for name, filename in (("Relatório JSON", "report.json"),
                                       ("Manifesto SHA-256", "report.json.manifest.json"),
                                       ("Triagem CSV", "triage.csv")):
                    response = page.request.get(origin + urls[name])
                    assert response.status == 200, f"download failed: {name} ({response.status})"
                    (evidence_dir / filename).write_bytes(response.body())

                verified = verify_poc_audit_report_pair(evidence_dir / "report.json")
                assert len(verified["records"]) == 2
                assert (evidence_dir / "triage.csv").stat().st_size > 0

                page.locator("#search").fill("M-DEMO-001")
                assert page.locator("#records tr").count() == 1, "search did not narrow result"
                page.locator("#search").fill("")
                page.locator("#filter").select_option("ACTIONABLE")
                assert page.locator("#records tr").count() <= 2
                page.locator("#filter").select_option("ALL")
                page.screenshot(path=str(evidence_dir / "verified-journey.png"), full_page=True)

                # A subsequent invalid CSV must not leave previously verified data visible.
                page.locator("#csv").set_input_files({
                    "name": "invalid.csv", "mimeType": "text/csv",
                    "buffer": b"not_a_catalog\ninvalid\n",
                })
                page.locator("#analyze").click()
                page.locator("#error").get_by_text("Recusado:", exact=False).wait_for(timeout=15000)
                assert page.locator("#result").is_hidden()
                assert page.locator("#downloads a").count() == 0
                page.screenshot(path=str(evidence_dir / "invalid-csv-rejected.png"), full_page=True)
                # Recover the interface and discard verified local sessions.
                page.locator("#example").click()
                page.locator("#result").wait_for(state="visible", timeout=15000)
                previous_link = page.locator("#downloads a").first.get_attribute("href")
                assert previous_link and previous_link.startswith("/artifact/")
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("#clear").click()
                page.get_by_text("Sessões locais descartadas.", exact=False).wait_for(timeout=15000)
                assert page.locator("#result").is_hidden()
                assert page.locator("#downloads a").count() == 0
                assert page.request.get(origin + previous_link).status == 404
                page.screenshot(path=str(evidence_dir / "sessions-discarded.png"), full_page=True)
                assert not errors, f"unexpected browser JavaScript errors: {errors}"
                (evidence_dir / "smoke-result.json").write_text(
                    json.dumps({"result": "PASS", "scope": "automated-headless-only",
                                "records": 2, "artifacts_verified": True,
                                "invalid_csv_hidden": True, "javascript_errors": 0}, indent=2) + "\n",
                    encoding="utf-8",
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        worker.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.evidence_dir)
    print(f"Automated browser smoke PASS; evidence: {args.evidence_dir}")
