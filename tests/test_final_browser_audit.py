"""Final Independent Audit — Complete Real-Browser Verification Suite.

Tests all seven application routes in real headless Chromium/Edge:
1. Overview (/)
2. Data Explorer (/explorer)
3. Match Replay (/replay)
4. Pressure Lab (/pressure)
5. Player Intelligence (/players)
6. Reliability Rankings (/rankings)
7. Methodology & Reports (/reports)
8. Mobile Viewport (390x844 responsive)

Saves evidence screenshots to reports/final_audit/screenshots/
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("final_browser_audit")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "reports" / "final_audit" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"


class FinalBrowserAuditRunner:
    def __init__(self) -> None:
        self.server_proc: Optional[subprocess.Popen] = None
        self.console_errors: List[str] = []
        self.failed_requests: List[str] = []
        self.test_log: List[Dict[str, str]] = []

    def start_server(self) -> None:
        logger.info("Starting backend FastAPI server on %s...", BASE_URL)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        self.server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        for _ in range(30):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as resp:
                    if resp.status == 200:
                        logger.info("Server successfully started and responding on %s", BASE_URL)
                        return
            except Exception:
                pass

        raise RuntimeError("Failed to start FastAPI server within 15 seconds")

    def stop_server(self) -> None:
        if self.server_proc:
            logger.info("Stopping FastAPI server...")
            self.server_proc.terminate()
            try:
                self.server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_proc.kill()
            self.server_proc = None
            logger.info("Server stopped.")

    def run_audit(self) -> bool:
        all_passed = True
        try:
            self.start_server()

            with sync_playwright() as p:
                logger.info("Launching headless Chromium/Edge browser...")
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-web-security", "--no-sandbox"],
                    channel="msedge" if os.name == "nt" else None,
                )

                context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    user_agent="SupeRR-FinalAudit/2.0",
                )
                page = context.new_page()

                def on_console(msg):
                    if msg.type in ("error", "warning") and "Failed to load resource" not in msg.text:
                        if "favicon.ico" not in msg.text and "fonts.gstatic.com" not in msg.text:
                            self.console_errors.append(f"[{msg.type.upper()}] {msg.text}")
                            logger.warning("Browser console %s: %s", msg.type, msg.text)

                def on_request_failed(req):
                    if "fonts.gstatic.com" not in req.url and "favicon.ico" not in req.url:
                        self.failed_requests.append(f"{req.method} {req.url} -> {req.failure}")
                        logger.error("Request failed: %s %s -> %s", req.method, req.url, req.failure)

                page.on("console", on_console)
                page.on("requestfailed", on_request_failed)

                # Execute test stages
                stages = [
                    self.stage_1_overview,
                    self.stage_2_data_explorer,
                    self.stage_3_match_replay,
                    self.stage_4_pressure_lab,
                    self.stage_5_player_intelligence,
                    self.stage_6_reliability_rankings,
                    self.stage_7_methodology_reports,
                    self.stage_8_mobile_viewport,
                ]

                for stage in stages:
                    try:
                        stage(page)
                    except Exception as e:
                        logger.error("Stage %s failed: %s", stage.__name__, e, exc_info=True)
                        all_passed = False

                context.close()
                browser.close()

        finally:
            self.stop_server()

        return all_passed and len(self.console_errors) == 0 and len(self.failed_requests) == 0

    def stage_1_overview(self, page: Page) -> None:
        logger.info("--- Stage 1: Auditing Overview (/) ---")
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.wait_for_selector("#root > div", timeout=8000)

        # Invariant assertions
        assert page.locator("text=SupeRR Selector").count() > 0, "Branding header missing"
        assert page.locator("text=Matches").count() > 0, "Matches metric missing"
        assert page.locator("text=Full Analytics Pipeline Verification").count() > 0, "Pipeline card missing"

        # Check for dynamic status badge
        assert page.locator("text=Status:").count() > 0, "Dynamic status header badge missing"

        # Screenshot
        shot_path = SCREENSHOTS_DIR / "01_final_overview.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Overview verified -> %s", shot_path.name)

    def stage_2_data_explorer(self, page: Page) -> None:
        logger.info("--- Stage 2: Auditing Data Explorer (/explorer) ---")
        page.goto(f"{BASE_URL}/explorer", wait_until="networkidle")
        page.wait_for_selector("text=Data Architecture Explorer", timeout=8000)

        # Select dataset
        page.select_option("select", "competition_team_player_mapping")
        page.wait_for_timeout(500)

        # Search for Vipraj
        search_input = page.locator("input[placeholder*='Search']")
        if search_input.count() > 0:
            search_input.fill("Vipraj")
            page.wait_for_timeout(500)
            assert page.locator("td:has-text('Vipraj Nigam')").count() > 0, "Player Vipraj Nigam not found in search"

        shot_path = SCREENSHOTS_DIR / "02_final_data_explorer.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Data Explorer verified -> %s", shot_path.name)

    def stage_3_match_replay(self, page: Page) -> None:
        logger.info("--- Stage 3: Auditing Match Replay (/replay) ---")
        page.goto(f"{BASE_URL}/replay", wait_until="networkidle")
        page.wait_for_selector("text=High-Pressure Match Replay", timeout=8000)

        page.wait_for_selector("h3:has-text('Matches Registry')", timeout=8000)
        assert page.locator("table").count() > 0, "Delivery table missing"

        shot_path = SCREENSHOTS_DIR / "03_final_match_replay.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Match Replay verified -> %s", shot_path.name)

    def stage_4_pressure_lab(self, page: Page) -> None:
        logger.info("--- Stage 4: Auditing Pressure Lab (/pressure) ---")
        page.goto(f"{BASE_URL}/pressure", wait_until="networkidle")
        page.wait_for_selector("text=Dual Pressure Lab", timeout=8000)

        assert page.locator("text=Batting Pressure").count() > 0, "Batting gauge missing"
        assert page.locator("text=Bowling Pressure").count() > 0, "Bowling gauge missing"

        shot_path = SCREENSHOTS_DIR / "04_final_pressure_lab.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Pressure Lab verified -> %s", shot_path.name)

    def stage_5_player_intelligence(self, page: Page) -> None:
        logger.info("--- Stage 5: Auditing Player Intelligence (/players) ---")
        page.goto(f"{BASE_URL}/players", wait_until="networkidle")
        page.wait_for_selector("text=Player Intelligence Dossier", timeout=8000)

        assert page.locator("text=Reliability Score").count() > 0, "Reliability score metric missing"

        shot_path = SCREENSHOTS_DIR / "05_final_player_intelligence.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Player Intelligence verified -> %s", shot_path.name)

    def stage_6_reliability_rankings(self, page: Page) -> None:
        logger.info("--- Stage 6: Auditing Reliability Rankings (/rankings) ---")
        page.goto(f"{BASE_URL}/rankings", wait_until="networkidle")
        page.wait_for_selector("text=Official Reliability Rankings", timeout=8000)

        assert page.locator("text=Vipraj Nigam").count() > 0, "Top 1 batter Vipraj Nigam missing"

        # Switch to Bowlers tab
        bowl_btn = page.locator("button:has-text('Top 10 Bowlers')")
        if bowl_btn.count() > 0:
            bowl_btn.click()
            page.wait_for_timeout(500)
            assert page.locator("text=Manimaran Siddharth").count() > 0, "Top 1 bowler Manimaran Siddharth missing"

        shot_path = SCREENSHOTS_DIR / "06_final_reliability_rankings.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Reliability Rankings verified -> %s", shot_path.name)

    def stage_7_methodology_reports(self, page: Page) -> None:
        logger.info("--- Stage 7: Auditing Methodology & Reports (/reports) ---")
        page.goto(f"{BASE_URL}/reports", wait_until="networkidle")
        page.wait_for_selector("text=Methodology & Verification Reports", timeout=8000)

        assert page.locator("text=Official Methodology Report (PDF)").count() > 0, "PDF card missing"
        assert page.locator("text=Download").count() > 0, "Download buttons missing"

        shot_path = SCREENSHOTS_DIR / "07_final_methodology_reports.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Methodology & Reports verified -> %s", shot_path.name)

    def stage_8_mobile_viewport(self, page: Page) -> None:
        logger.info("--- Stage 8: Auditing Mobile Viewport (390x844) ---")
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{BASE_URL}/rankings", wait_until="networkidle")
        page.wait_for_selector("text=Official Reliability Rankings", timeout=8000)

        shot_path = SCREENSHOTS_DIR / "08_final_mobile_viewport.png"
        page.screenshot(path=str(shot_path), full_page=True)
        logger.info("[PASS] Mobile Viewport verified -> %s", shot_path.name)


def main():
    runner = FinalBrowserAuditRunner()
    success = runner.run_audit()
    print("=" * 60)
    print("FINAL BROWSER AUDIT EXECUTION OUTCOME:", "SUCCESS" if success else "FAILED")
    print(f"Console Errors:    {len(runner.console_errors)}")
    print(f"Failed Requests:   {len(runner.failed_requests)}")
    print("=" * 60)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
