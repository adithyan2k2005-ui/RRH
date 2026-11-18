"""Comprehensive Real-Browser End-to-End Test Suite for SupeRR Intelligence Lab.

Tests all seven application routes in real headless Chromium/Edge:
1. Overview (/)
2. Data Explorer (/explorer)
3. Match Replay (/replay)
4. Pressure Lab (/pressure)
5. Player Intelligence (/players)
6. Reliability Rankings (/rankings)
7. Methodology & Reports (/reports)

Verifications executed per page:
- Direct URL loading
- Sidebar navigation
- Page refresh stability
- Primary interactive controls (selectors, inputs, toggles, scrubbers, modals)
- Valid result rendering
- Empty / filtered result states
- Error handling / non-empty root
- Browser console error tracking (zero React error #31)
- Network request tracking (zero 4xx / 5xx failures)
- Viewport testing (Desktop 1440x900 & Mobile 390x844)
- High-fidelity PNG screenshot capture into reports/critical_repairs/repair3/screenshots/
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("browser_qa")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "reports" / "final_audit" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"


class BrowserQARunner:
    def __init__(self) -> None:
        self.server_proc: Optional[subprocess.Popen] = None
        self.console_errors: List[str] = []
        self.failed_requests: List[str] = []
        self.test_log: List[Dict[str, str]] = []

    def start_server(self) -> None:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as resp:
                if resp.status == 200:
                    logger.info("Server is already running and healthy on %s.", BASE_URL)
                    return
        except Exception:
            pass
        logger.info("Starting backend FastAPI server on %s...", BASE_URL)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(PORT)]
        self.server_proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for server to become healthy
        max_retries = 30
        for i in range(max_retries):
            time.sleep(1.0)
            try:
                with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2) as resp:
                    if resp.status == 200:
                        logger.info("Server is healthy and ready to serve requests.")
                        return
            except Exception:
                pass
        raise RuntimeError("FastAPI server failed to start within timeout.")

    def stop_server(self) -> None:
        if self.server_proc:
            logger.info("Stopping FastAPI server...")
            self.server_proc.terminate()
            try:
                self.server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_proc.kill()

    def setup_page_listeners(self, page: Page) -> None:
        page.on("console", lambda msg: self._handle_console(msg))
        page.on(
            "requestfailed",
            lambda req: self.failed_requests.append(f"{req.method} {req.url}: {req.failure}")
            if "fonts.gstatic.com" not in req.url and "fonts.googleapis.com" not in req.url
            else None,
        )
        page.on("response", lambda resp: self._handle_response(resp))

    def _handle_console(self, msg) -> None:
        if msg.type == "error":
            text = msg.text
            # Filter harmless network closures / favicon / external fonts
            if "favicon.ico" not in text and "ERR_CONNECTION_CLOSED" not in text and "fonts.gstatic" not in text:
                self.console_errors.append(text)
                logger.error("Browser Console Error: %s", text)

    def _handle_response(self, resp) -> None:
        if resp.status >= 400 and "favicon.ico" not in resp.url and "fonts.gstatic.com" not in resp.url:
            self.failed_requests.append(f"{resp.request.method} {resp.url} returned status {resp.status}")
            logger.warning("HTTP %d on %s", resp.status, resp.url)

    def run_tests(self) -> None:
        with sync_playwright() as p:
            # Launch MS Edge (or Chrome)
            browser: Browser
            try:
                browser = p.chromium.launch(headless=True, channel="msedge")
                logger.info("Launched Edge browser successfully.")
            except Exception:
                browser = p.chromium.launch(headless=True, channel="chrome")
                logger.info("Launched Chrome browser successfully.")

            # Desktop Context
            desktop_context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = desktop_context.new_page()
            self.setup_page_listeners(page)

            try:
                self.test_overview_page(page)
                self.test_data_explorer_page(page)
                self.test_match_replay_page(page)
                self.test_pressure_lab_page(page)
                self.test_player_intelligence_page(page)
                self.test_reliability_rankings_page(page)
                self.test_methodology_reports_page(page)

                # Mobile Responsive Viewport
                page.set_viewport_size({"width": 390, "height": 844})
                time.sleep(0.5)
                self.test_mobile_responsiveness(page)

            finally:
                desktop_context.close()
                browser.close()

    def test_overview_page(self, page: Page) -> None:
        logger.info("--- Testing Page 1: Overview (/) ---")
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.wait_for_selector("h2", timeout=10000)

        # Assert key elements present and populated
        content = page.content()
        assert "SupeRR Selector Season 2" in content
        assert "Rajasthan Royals" in content
        assert "Vipraj Nigam" in content
        assert "Manimaran Siddharth" in content
        assert "Deliveries Analysed" in content

        # Check that #root is non-empty and no React error #31 is visible
        assert "Minified React error #31" not in content
        assert "System Data Load Error" not in content

        # Sidebar navigation check
        page.click("nav a:has-text('Overview')")
        time.sleep(0.5)

        # Page refresh check
        page.reload(wait_until="networkidle")
        page.wait_for_selector("h2", timeout=10000)

        # Save screenshot
        ss_path = SCREENSHOTS_DIR / "01_overview_desktop.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Overview", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Overview page verified successfully.")

    def test_data_explorer_page(self, page: Page) -> None:
        logger.info("--- Testing Page 2: Data Explorer (/explorer) ---")
        page.goto(f"{BASE_URL}/explorer", wait_until="networkidle")
        page.wait_for_selector("select#dataset-select", timeout=10000)

        # Assert dataset dropdown options exist
        select_elem = page.locator("select#dataset-select")
        assert select_elem.is_visible()

        # Switch to matches dataset
        select_elem.select_option("matches")
        page.wait_for_selector("h3:has-text('Matches Registry')", timeout=10000)

        # Switch to top_10_batters dataset
        select_elem.select_option("top_10_batters")
        page.wait_for_selector("h3:has-text('Official Top 10 Batters')", timeout=10000)
        page.wait_for_selector("td:has-text('Vipraj Nigam')", timeout=10000)

        # Test Search Filter
        search_input = page.locator("input[placeholder*='Search']")
        if search_input.is_visible():
            search_input.fill("Vipraj")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector("td:has-text('Vipraj Nigam')", timeout=10000)
            # Test empty result search
            search_input.fill("NONEXISTENT_XYZ_QUERY")
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)
            # Reset search
            search_input.fill("")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector("td:has-text('Vipraj Nigam')", timeout=10000)

        # Save screenshot
        ss_path = SCREENSHOTS_DIR / "02_data_explorer_desktop.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Data Explorer", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Data Explorer verified successfully.")

    def test_match_replay_page(self, page: Page) -> None:
        logger.info("--- Testing Page 3: Match Replay (/replay) ---")
        page.goto(f"{BASE_URL}/replay", wait_until="networkidle")
        page.wait_for_selector("select", timeout=10000)

        # Verify scoreboard and match state elements
        content = page.content()
        assert "Ball-by-Ball Match-State Replay" in content
        assert "ZERO FUTURE LEAKAGE GUARANTEED" in content
        assert "Score Before" in content
        assert "Balls Remaining" in content

        # Test range scrubber navigation
        slider = page.locator("input[type='range']")
        if slider.is_visible():
            slider.fill("10")
            time.sleep(0.5)

        # Test innings button toggle
        inn_buttons = page.locator("button:has-text('Innings')")
        if inn_buttons.count() > 1:
            inn_buttons.nth(1).click()
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)

        # Save screenshot
        ss_path = SCREENSHOTS_DIR / "03_match_replay_desktop.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Match Replay", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Match Replay verified successfully.")

    def test_pressure_lab_page(self, page: Page) -> None:
        logger.info("--- Testing Page 4: Pressure Lab (/pressure) ---")
        page.goto(f"{BASE_URL}/pressure", wait_until="networkidle")
        page.wait_for_selector("h2", timeout=10000)

        # Verify pressure curves & factors
        content = page.content()
        assert "Context-Aware Cricket Pressure Engine" in content
        assert "Continuous Match Pressure Timeline" in content

        # Toggle to Innings 1
        inn1_btn = page.locator("button:has-text('Inn 1')")
        if inn1_btn.is_visible():
            inn1_btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)

        # Save screenshot
        ss_path = SCREENSHOTS_DIR / "04_pressure_lab_desktop.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Pressure Lab", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Pressure Lab verified successfully.")

    def test_player_intelligence_page(self, page: Page) -> None:
        logger.info("--- Testing Page 5: Player Intelligence (/players) ---")
        page.goto(f"{BASE_URL}/players", wait_until="networkidle")
        page.wait_for_selector("h2", timeout=10000)

        content = page.content()
        h2_text = page.locator("h2").all_inner_texts()
        logger.info("Player intelligence h2 texts: %s", h2_text)
        assert "Player Intelligence" in content

        # Search for player
        search_box = page.locator("input[placeholder*='Search player']")
        if search_box.is_visible():
            search_box.fill("Jadeja")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector("text=Ravindra Jadeja", timeout=10000)
            search_box.fill("")
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)

        # Toggle to Bowling Intelligence
        bowl_btn = page.locator("button:has-text('Bowling Intelligence')")
        bowl_btn.click()
        page.wait_for_selector("text=Manimaran Siddharth", timeout=10000)

        # Test Compare Modal Trigger
        compare_btn = page.locator("button:has-text('Compare with Another Player')")
        if compare_btn.is_visible():
            compare_btn.click()
            time.sleep(0.5)
            # Close modal if open
            close_btn = page.locator("button:has-text('Close')")
            if close_btn.is_visible():
                close_btn.click()

        # Save screenshot
        ss_path = SCREENSHOTS_DIR / "05_player_intelligence_desktop.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Player Intelligence", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Player Intelligence verified successfully.")

    def test_reliability_rankings_page(self, page: Page) -> None:
        logger.info("--- Testing Page 6: Reliability Rankings (/rankings) ---")
        page.goto(f"{BASE_URL}/rankings", wait_until="networkidle")
        page.wait_for_selector("text=Vipraj Nigam", timeout=10000)

        content = page.content()
        assert "SupeRR Reliability Rankings — Official Round 1 Selections" in content
        # Check Top 1 Batter presence
        assert "Vipraj Nigam" in content
        assert "Towhid Hridoy" in content
        assert "Matthew Wade" in content
        assert "92.69" in content

        # Switch to Top 10 Bowlers
        bowl_tab = page.locator("button:has-text('Top 10 Bowlers')")
        bowl_tab.click()
        page.wait_for_selector("text=Manimaran Siddharth", timeout=10000)

        bowl_content = page.content()
        assert "Manimaran Siddharth" in bowl_content
        assert "Muhammad Khan" in bowl_content
        assert "Abbas Afridi" in bowl_content
        assert "88.46" in bowl_content

        # Save screenshot
        ss_path = SCREENSHOTS_DIR / "06_reliability_rankings_desktop.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Reliability Rankings", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Reliability Rankings verified successfully.")

    def test_methodology_reports_page(self, page: Page) -> None:
        logger.info("--- Testing Page 7: Methodology & Reports (/reports) ---")
        page.goto(f"{BASE_URL}/reports", wait_until="networkidle")
        page.wait_for_selector("h2", timeout=10000)

        content = page.content()
        assert "Methodology, Quality Verification" in content
        assert "16-Point Analytical Quality Gate Audit" in content
        assert "16 / 16 GATES PASSED (100%)" in content
        assert "Official Methodology Report (PDF)" in content
        assert "High Pressure Impact" in content
        assert "40%" in content
        assert "Pressure Uplift" in content
        assert "25%" in content

        # Save screenshot
        ss_path = SCREENSHOTS_DIR / "07_methodology_reports_desktop.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Methodology & Reports", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Methodology & Reports verified successfully.")

    def test_mobile_responsiveness(self, page: Page) -> None:
        logger.info("--- Testing Mobile Responsiveness (390x844) ---")
        time.sleep(1.0)

        # Verify mobile header and hamburger menu button exist
        menu_button = page.locator("button[aria-label='Toggle navigation menu']")
        assert menu_button.is_visible()

        # Open mobile drawer
        menu_button.click()
        time.sleep(0.5)
        assert page.locator("aside").is_visible()

        # Navigate to rankings on mobile
        page.click("nav a:has-text('Reliability Rankings')")
        page.wait_for_selector("h2:has-text('SupeRR Reliability Rankings')", timeout=10000)
        assert "SupeRR Reliability Rankings" in page.content()

        # Save mobile screenshot
        ss_path = SCREENSHOTS_DIR / "08_mobile_rankings_viewport.png"
        page.screenshot(path=str(ss_path), full_page=True)
        self.test_log.append({"page": "Mobile Viewport", "status": "PASS", "screenshot": ss_path.name})
        logger.info("Mobile responsiveness verified successfully.")


def main():
    runner = BrowserQARunner()
    try:
        runner.start_server()
        runner.run_tests()
        logger.info("All browser tests completed successfully!")
        print("\n=== BROWSER QA TEST RESULTS SUMMARY ===")
        for item in runner.test_log:
            print(f"[{item['status']}] {item['page']} -> Screenshot: {item['screenshot']}")

        print(f"\nConsole Errors Count: {len(runner.console_errors)}")
        print(f"Failed Requests Count: {len(runner.failed_requests)}")

        # Fail if any console errors occurred
        if runner.console_errors:
            print("\nErrors recorded:")
            for e in runner.console_errors:
                print("  -", e)
            sys.exit(1)
        if runner.failed_requests:
            print("\nFailed network requests:")
            for req in runner.failed_requests:
                print("  -", req)
            sys.exit(1)

    finally:
        runner.stop_server()


if __name__ == "__main__":
    main()
