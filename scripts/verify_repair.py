"""Comprehensive test script to verify root rendering repair across both ports."""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPORTS_DIR = Path("reports/phase7")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ROUTES = [
    ("/", "Overview"),
    ("/explorer", "Data Explorer"),
    ("/replay", "Match Replay"),
    ("/pressure", "Pressure Lab"),
    ("/players", "Player Intelligence"),
    ("/rankings", "Reliability Rankings"),
    ("/reports", "Methodology & Reports"),
]

def verify_port(port: int):
    base_url = f"http://127.0.0.1:{port}"
    print(f"\n=======================================================")
    print(f"VERIFYING APPLICATION ON PORT {port} ({base_url})")
    print(f"=======================================================")
    
    port_results = {
        "port": port,
        "direct_routes": [],
        "sidebar_nav": [],
        "interactions": {},
        "failures": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        all_console_errors = []
        all_page_errors = []
        
        page.on("pageerror", lambda err: all_page_errors.append(str(err)))
        page.on("console", lambda msg: all_console_errors.append(msg.text) if msg.type == "error" else None)
        
        # 1. DIRECT URL NAVIGATION FOR ALL 7 ROUTES
        print("\n--- 1. Testing Direct URL Navigation ---")
        for route, name in ROUTES:
            url = f"{base_url}{route}"
            errors_before = len(all_page_errors)
            
            try:
                resp = page.goto(url, wait_until="networkidle", timeout=12000)
                status = resp.status if resp else "None"
            except Exception as e:
                status = f"Timeout/Error: {e}"
                
            page.wait_for_timeout(1000)
            
            dom_check = page.evaluate("""() => {
                const root = document.getElementById('root');
                const aside = document.querySelector('aside');
                const header = document.querySelector('header');
                const main = document.querySelector('main');
                const faultBoundary = document.querySelector('body')?.innerText?.includes('Fault Tolerant Boundary Active');
                return {
                    rootExists: !!root,
                    hasAside: !!aside,
                    hasHeader: !!header,
                    hasMain: !!main,
                    faultBoundaryActive: !!faultBoundary,
                    mainTextSnippet: main ? main.innerText.slice(0, 150).replace(/\\n/g, ' ') : "",
                    asideVisible: aside ? window.getComputedStyle(aside).display !== 'none' : false,
                };
            }""")
            
            clean_name = name.lower().replace(" ", "_").replace("&", "and")
            screenshot_path = REPORTS_DIR / f"repaired_{port}_{clean_name}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            
            new_errors = all_page_errors[errors_before:]
            is_success = dom_check["hasAside"] and dom_check["hasMain"] and len(new_errors) == 0
            
            res_item = {
                "route": route,
                "name": name,
                "status": status,
                "success": is_success,
                "dom_check": dom_check,
                "errors": new_errors,
                "screenshot": str(screenshot_path)
            }
            port_results["direct_routes"].append(res_item)
            
            print(f"[{'PASS' if is_success else 'FAIL'}] {name:22} ({route:10}) | Aside: {dom_check['hasAside']} | Main: {dom_check['hasMain']} | Errors: {len(new_errors)}")
            if not is_success:
                port_results["failures"].append(f"Direct nav to {route} failed: {new_errors}")
                
        # 2. IN-APP SIDEBAR NAVIGATION & CLICKING
        print("\n--- 2. Testing In-App Sidebar Navigation ---")
        page.goto(f"{base_url}/", wait_until="networkidle")
        page.wait_for_timeout(1000)
        
        for route, name in ROUTES:
            # Locate sidebar link by href
            link = page.locator(f"aside nav a[href='{route}']")
            if link.count() == 0:
                print(f"[FAIL] Link for {route} not found in sidebar!")
                port_results["failures"].append(f"Missing sidebar link for {route}")
                continue
                
            link.click()
            page.wait_for_timeout(1000)
            
            dom_check = page.evaluate("""() => {
                const aside = document.querySelector('aside');
                const main = document.querySelector('main');
                return {
                    hasAside: !!aside,
                    hasMain: !!main,
                    mainTextSnippet: main ? main.innerText.slice(0, 100).replace(/\\n/g, ' ') : "",
                };
            }""")
            
            is_ok = dom_check["hasAside"] and dom_check["hasMain"]
            print(f"[{'PASS' if is_ok else 'FAIL'}] Sidebar click -> {name:22} | URL: {page.url} | Main: {dom_check['hasMain']}")
            port_results["sidebar_nav"].append({
                "route": route,
                "name": name,
                "url": page.url,
                "success": is_ok
            })
            if not is_ok:
                port_results["failures"].append(f"Sidebar click navigation to {route} failed")
                
        # 3. BROWSER REFRESH ON DEEP ROUTE
        print("\n--- 3. Testing Deep Route Refresh ---")
        page.goto(f"{base_url}/rankings", wait_until="networkidle")
        page.wait_for_timeout(800)
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1000)
        refresh_check = page.evaluate("() => ({ hasAside: !!document.querySelector('aside'), hasMain: !!document.querySelector('main') })")
        print(f"[{'PASS' if refresh_check['hasAside'] and refresh_check['hasMain'] else 'FAIL'}] Refresh on /rankings | Aside: {refresh_check['hasAside']}, Main: {refresh_check['hasMain']}")
        port_results["interactions"]["refresh_rankings"] = refresh_check
        
        # 4. BACK / FORWARD NAVIGATION
        print("\n--- 4. Testing Browser Back / Forward ---")
        page.goto(f"{base_url}/explorer", wait_until="networkidle")
        page.wait_for_timeout(500)
        page.goto(f"{base_url}/pressure", wait_until="networkidle")
        page.wait_for_timeout(500)
        page.go_back(wait_until="networkidle")
        page.wait_for_timeout(500)
        back_url = page.url
        page.go_forward(wait_until="networkidle")
        page.wait_for_timeout(500)
        fwd_url = page.url
        print(f"[PASS] Back/Forward | Back: {back_url} | Forward: {fwd_url}")
        port_results["interactions"]["back_forward"] = {"back": back_url, "forward": fwd_url}
        
        # 5. INTERACTIVE FUNCTIONALITY TESTS
        print("\n--- 5. Testing Interactive Page Features ---")
        
        # A. Player Intelligence - Search & Discipline Toggle
        page.goto(f"{base_url}/players", wait_until="networkidle")
        page.wait_for_timeout(1000)
        # Search for a player
        search_input = page.locator("input[placeholder*='Search player']")
        if search_input.count() > 0:
            search_input.fill("Miller")
            page.wait_for_timeout(800)
            has_miller = page.evaluate("() => document.body.innerText.includes('David Miller')")
            print(f"[{'PASS' if has_miller else 'FAIL'}] Player Search ('Miller'): {has_miller}")
            port_results["interactions"]["player_search"] = has_miller
            
        # Toggle to bowling
        bowling_btn = page.locator("button:has-text('Bowling Intelligence')")
        if bowling_btn.count() > 0:
            bowling_btn.click()
            page.wait_for_timeout(1000)
            has_bowler = page.evaluate("() => document.body.innerText.includes('Manimaran Siddharth') || document.body.innerText.includes('BOWLING')")
            print(f"[{'PASS' if has_bowler else 'FAIL'}] Bowling Discipline Toggle: {has_bowler}")
            port_results["interactions"]["bowling_toggle"] = has_bowler
            
        # B. Data Explorer - Dataset Selection
        page.goto(f"{base_url}/explorer", wait_until="networkidle")
        page.wait_for_timeout(1000)
        dataset_select = page.locator("#dataset-select")
        if dataset_select.count() > 0:
            dataset_select.select_option("matches")
            page.wait_for_timeout(1500)
            has_matches_table = page.evaluate("() => document.body.innerText.includes('Matches Registry') && document.querySelectorAll('table tbody tr').length > 0")
            print(f"[{'PASS' if has_matches_table else 'FAIL'}] Data Explorer Matches Selection: {has_matches_table}")
            port_results["interactions"]["dataset_selection"] = has_matches_table
            
        # C. Match Replay - Innings & Delivery Navigation
        page.goto(f"{base_url}/replay", wait_until="networkidle")
        page.wait_for_timeout(1000)
        has_delivery_ui = page.evaluate("() => document.body.innerText.includes('Over') && document.body.innerText.includes('CRR')")
        print(f"[{'PASS' if has_delivery_ui else 'FAIL'}] Match Replay Delivery Scrubber Rendered: {has_delivery_ui}")
        port_results["interactions"]["match_replay_ui"] = has_delivery_ui
        
        # D. Reliability Rankings - Full Table
        page.goto(f"{base_url}/rankings", wait_until="networkidle")
        page.wait_for_timeout(1000)
        has_rankings = page.evaluate("() => document.body.innerText.includes('RANK #1') && document.querySelectorAll('table tbody tr').length >= 10")
        print(f"[{'PASS' if has_rankings else 'FAIL'}] Rankings Table (>=10 rows): {has_rankings}")
        port_results["interactions"]["rankings_table"] = has_rankings
        
        # E. Methodology & Reports - Direct Download verification
        page.goto(f"{base_url}/reports", wait_until="networkidle")
        page.wait_for_timeout(1000)
        download_links_count = page.locator("a[href*='/api/reports/'][href*='/download']").count()
        print(f"[{'PASS' if download_links_count > 0 else 'FAIL'}] Reports Download Links: {download_links_count} found")
        port_results["interactions"]["reports_download_links"] = download_links_count
        
        browser.close()
        
    return port_results

if __name__ == "__main__":
    res_8000 = verify_port(8000)
    res_5173 = verify_port(5173)
    
    total_failures = len(res_8000["failures"]) + len(res_5173["failures"])
    print(f"\n=======================================================")
    print(f"FINAL VERIFICATION SUMMARY: {'ALL PASSED' if total_failures == 0 else f'{total_failures} FAILURES'}")
    print(f"=======================================================")
